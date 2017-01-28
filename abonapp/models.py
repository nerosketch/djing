# -*- coding: utf-8 -*-
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django.db import models
from django.core.validators import DecimalValidator

from agent import Transmitter, AbonStruct, TariffStruct, NasFailedResult
from ip_pool.models import IpPoolItem
from tariff_app.models import Tariff
from accounts_app.models import UserProfile


class LogicError(Exception):
    def __init__(self, value):
        self.message = value

    def __str__(self):
        return repr(self.message)

    def __str__(self):
        return repr(self.message)


class AbonGroup(models.Model):
    title = models.CharField(max_length=127, unique=True)
    profiles = models.ManyToManyField(UserProfile, blank=True, related_name='abon_groups')

    class Meta:
        db_table = 'abonent_groups'
        permissions = (
            ('can_add_ballance', 'Пополнение счёта'),
        )

    def __str__(self):
        return self.title


class AbonLog(models.Model):
    abon = models.ForeignKey('Abon')
    amount = models.FloatField(default=0.0)
    author = models.ForeignKey(UserProfile, related_name='+')
    comment = models.CharField(max_length=128)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'abonent_log'

    def __str__(self):
        return self.comment


class AbonTariff(models.Model):
    abon = models.ForeignKey('Abon')
    tariff = models.ForeignKey(Tariff, related_name='linkto_tariff')
    tariff_priority = models.PositiveSmallIntegerField(default=0)

    # время начала действия, остальные что не начали действие - NULL
    time_start = models.DateTimeField(null=True, blank=True, default=None)

    def priority_up(self):
        # ищем услугу с большим приоритетом(число приоритета меньше)
        target_abtar = AbonTariff.objects.filter(
            abon=self.abon,
            tariff_priority__lt=self.tariff_priority
        ).order_by('-tariff_priority')[:1]
        if target_abtar.count() > 0:
            target_abtar = target_abtar[0]
        else:
            return

        # Ищем текущий тариф абонента
        active_abtar = AbonTariff.objects.filter(
            abon=self.abon
        )[:1]
        if active_abtar.count() > 0:
            active_abtar = active_abtar[0]
        else:
            return

        # Если услуга с которой хотим поменяться приоритетом является текущей то нельзя меняться
        if active_abtar == target_abtar:
            return

        # Swap приоритетов у текущего и найденного с меньшим tariff_priority (большим приоритетом)
        tmp_prior = target_abtar.tariff_priority
        target_abtar.tariff_priority = self.tariff_priority
        target_abtar.save(update_fields=['tariff_priority'])
        self.tariff_priority = tmp_prior
        self.save(update_fields=['tariff_priority'])

    def priority_down(self):
        # ищем услугу с меньшим приоритетом
        target_abtar = AbonTariff.objects.filter(
            abon=self.abon,
            tariff_priority__gt=self.tariff_priority
        )[:1]
        if target_abtar.count() > 0:
            target_abtar = target_abtar[0]
        else:
            # меньше нет, это самая последняя услуга
            return

        # Swap приоритетов у текущего и найденного с большим tariff_priority (меньшим приоритетом)
        tmp_pr = self.tariff_priority
        self.tariff_priority = target_abtar.tariff_priority
        target_abtar.tariff_priority = tmp_pr
        target_abtar.save(update_fields=['tariff_priority'])
        self.save(update_fields=['tariff_priority'])

    # Считает текущую стоимость услуг согласно выбранной для тарифа логики оплаты (см. в документации)
    def calc_amount_service(self):
        calc_obj = self.tariff.get_calc_type()
        # calc_obj - instance of tariff_app.custom_tariffs.TariffBase
        amount = calc_obj.calc_amount(self)
        return round(amount, 2)

    # Активируем тариф
    def activate(self, current_user):
        amnt = self.calc_amount_service()
        # если не хватает денег
        if self.abon.ballance < amnt:
            raise LogicError('Не хватает денег на счету')
        # дата активации услуги
        self.time_start = timezone.now()
        # снимаем деньги за услугу
        self.abon.make_pay(current_user, amnt)
        self.save()

    # Используется-ли услуга сейчас, если время старта есть то он активирован
    def is_started(self):
        return True if self.time_start is not None else False

    def __str__(self):
        return "%d: '%s' - '%s'" % (
            self.tariff_priority,
            self.tariff.title,
            self.abon.get_short_name()
        )

    class Meta:
        ordering = ('tariff_priority',)
        db_table = 'abonent_tariff'
        unique_together = (('abon', 'tariff', 'tariff_priority'),)
        permissions = (
            ('can_complete_service', 'Досрочное завершение услуги абонента'),
            ('can_activate_service', 'Активация услуги абонента')
        )


class AbonStreets(models.Model):
    name = models.CharField(max_length=64)
    group = models.ForeignKey(AbonGroup)


class Abon(UserProfile):
    current_tariffs = models.ManyToManyField(Tariff, through=AbonTariff)
    group = models.ForeignKey(AbonGroup, models.SET_NULL, blank=True, null=True)
    ballance = models.FloatField(default=0.0, validators=[DecimalValidator])
    ip_address = models.OneToOneField(IpPoolItem, on_delete=models.SET_NULL, null=True, blank=True)
    #TODO: надо ж пароль для абонента создавать
    description = models.TextField(null=True, blank=True)
    street = models.ForeignKey(AbonStreets, on_delete=models.SET_NULL, null=True, blank=True)
    house = models.CharField(max_length=12, null=True, blank=True)

    _act_tar_cache = None

    # возвращает текущий тариф для абонента
    def active_tariff(self, use_cache=True):
        if self._act_tar_cache and use_cache:
            return self._act_tar_cache

        ats = AbonTariff.objects.filter(abon=self).exclude(time_start=None)

        if ats.count() > 0:
            self._act_tar_cache = ats[0].tariff
            return ats[0].tariff
        else:
            self._act_tar_cache = None
            return

    class Meta:
        db_table = 'abonent'
        permissions = (
            ('can_buy_tariff', 'Покупка тарифа абоненту'),
        )

    # Платим за что-то
    def make_pay(self, curuser, how_match_to_pay=0.0, u_comment='Снятие со счёта средств'):
        AbonLog.objects.create(
            abon=self,
            amount=-how_match_to_pay,
            author=curuser,
            comment=u_comment
        )
        self.ballance -= how_match_to_pay

    # Пополняем счёт
    def add_ballance(self, current_user, amount):
        AbonLog.objects.create(
            abon=self,
            amount=amount,
            author=current_user,
            comment='Пополнение счёта через админку'
        )
        self.ballance += amount

    # покупаем тариф
    def buy_tariff(self, tariff, author):
        assert isinstance(tariff, Tariff)

        # выбераем связь ТарифАбонент с самым низким приоритетом
        abtrf = AbonTariff.objects.filter(abon=self).order_by('-tariff_priority')[:1]
        abtrf = abtrf[0] if abtrf.count() > 0 else None

        # создаём новую связь с приоритетом ещё ниже
        new_abtar = AbonTariff(
            abon=self,
            tariff=tariff,
            tariff_priority=abtrf.tariff_priority + 1 if abtrf else -1
        )

        # Если это первая услуга в списке (фильтр по приоритету ничего не вернул)
        if not abtrf:
            # значит она сразу стаёт активной
            new_abtar.time_start = timezone.now()

        new_abtar.save()

        # Запись об этом в лог
        AbonLog.objects.create(
            abon=self, amount=-tariff.amount,
            author=author,
            comment='Покупка тарифного плана через админку, тариф "%s"' % tariff.title
        )

    # Пробует подключить новую услугу если пришло время
    def activate_next_tariff(self, author):
        ats = AbonTariff.objects.filter(abon=self).order_by('tariff_priority')

        nw = datetime.now(tz=timezone.get_current_timezone())

        for at in ats:
            # Если активированный тариф
            if not at.is_started():
                return

            # время к началу месяца
            to_start_month = datetime(nw.year, nw.month, 1, tzinfo=timezone.get_current_timezone())

            # проверяем расстояние от Сегодня до начала этого месяца.
            # И от заказа тарифа до начала этого месяца
            if (nw - at.time_start) > (nw - to_start_month):
                # Заказ из прошлого месяца, срок действия закончен
                print('Заказ из прошлого месяца, срок действия закончен')

                # выберем следующую по приоритету
                # next_tarifs = AbonTariff.objects.filter(tariff_priority__gt = self.tariff_priority, abon=self.abon)
                next_tarifs = filter(lambda tr: tr.tariff_priority > at.tariff_priority, ats)[:2]

                # и если что-нибудь вернулось то активируем, давая время начала действия
                if len(next_tarifs) > 0:
                    next_tarifs[0].time_start = nw
                    next_tarifs[0].save(update_fields=['time_start'])

                # завершаем текущую услугу.
                at.delete()

                # Создаём лог о завершении услуги
                AbonLog.objects.create(
                    abon=self,
                    amount=0,
                    author=author,
                    comment='Завершение услуги по истечению срока действия'
                )

    # есть-ли доступ у абонента к услуге, смотрим в tariff_app.custom_tariffs.<TariffBase>.manage_access()
    def is_access(self):
        trf = self.active_tariff()
        if not trf: return False
        ct = trf.get_calc_type()
        if ct.manage_access(self):
            return True
        else:
            return False


class InvoiceForPayment(models.Model):
    abon = models.ForeignKey(Abon)
    status = models.BooleanField(default=False)
    amount = models.FloatField(default=0.0)
    comment = models.CharField(max_length=128)
    date_create = models.DateTimeField(auto_now_add=True)
    date_pay = models.DateTimeField(blank=True, null=True)
    author = models.ForeignKey(UserProfile, related_name='+')

    def __str__(self):
        return "%s -> %d $" % (self.abon.username, self.amount)

    def set_ok(self):
        self.status = True
        self.date_pay = datetime.now()

    def get_prev_invoice(self):
        return self.objects.order

    class Meta:
        ordering = ('date_create',)
        db_table = 'abonent_inv_pay'


def abon_post_save(sender, instance, **kwargs):
    if instance.ip_address:
        user_ip = instance.ip_address.int_ip()
    else:
        return
    inst_tariff = instance.active_tariff()
    if inst_tariff:
        agent_trf = TariffStruct(inst_tariff.id, inst_tariff.speedIn, inst_tariff.speedOut)
    else:
        agent_trf = TariffStruct()
    agent_abon = AbonStruct(instance.id, user_ip, agent_trf)
    tm = Transmitter()
    if kwargs['created']:
        # создаём абонента
        tm.add_user(agent_abon)
    else:
        # обновляем абонента на NAS
        try:
            tm.update_user(agent_abon)
        except NasFailedResult:
            tm.add_user(agent_abon)
        # если не активен то приостановим услугу
        if instance.is_active:
            tm.start_user(agent_abon)
        else:
            tm.pause_user(agent_abon)


def abon_del_signal(sender, instance, **kwargs):
    # подключаемся к NAS'у
    tm = Transmitter()
    # удаляем абонента на NAS
    tm.remove_user(instance.id)


def abontariff_post_save(sender, instance, **kwargs):
    # Тут или подключение абону услуги, или изменение приоритета
    if not kwargs['created']:
        # если изменение приоритета то не говорим об этом NAS'у
        return
    if instance.abon.ip_address is None:
        return
    agent_trf = TariffStruct(instance.tariff.id, instance.tariff.speedIn, instance.tariff.speedOut)
    agent_abon = AbonStruct(instance.abon.id, instance.abon.ip_address.int_ip(), agent_trf)
    tm = Transmitter()
    tm.update_user(agent_abon)
    tm.start_user(agent_abon)


def abontariff_del_signal(sender, instance, **kwargs):
    if not instance.is_started():
        # если удаляем не активную услугу то говорить об этом NAS'у не обязательно
        return
    agent_trf = TariffStruct(instance.tariff.id, instance.tariff.speedIn, instance.tariff.speedOut)
    agent_abon = AbonStruct(instance.abon.id, instance.abon.ip_address.int_ip(), agent_trf)
    tm = Transmitter()
    tm.pause_user(agent_abon)


models.signals.post_save.connect(abon_post_save, sender=Abon)
models.signals.post_delete.connect(abon_del_signal, sender=Abon)

models.signals.post_save.connect(abontariff_post_save, sender=AbonTariff)
models.signals.post_delete.connect(abontariff_del_signal, sender=AbonTariff)
