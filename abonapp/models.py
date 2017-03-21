# -*- coding: utf-8 -*-
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
from django.core import validators
from django.utils.translation import ugettext as _
from agent import Transmitter, AbonStruct, TariffStruct, NasFailedResult
from ip_pool.models import IpPoolItem
from tariff_app.models import Tariff
from accounts_app.models import UserProfile


class LogicError(Exception):
    pass


class AbonGroup(models.Model):
    title = models.CharField(max_length=127, unique=True)
    profiles = models.ManyToManyField(UserProfile, blank=True, related_name='abon_groups')
    tariffs = models.ManyToManyField(Tariff, blank=True, related_name='tariff_groups')

    class Meta:
        db_table = 'abonent_groups'
        permissions = (
            ('can_add_ballance', _('fill account')),
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

    # время завершения услуги
    deadline = models.DateTimeField(null=True, blank=True, default=None)

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
        amount = self.tariff.amount
        return round(amount, 2)

    # Активируем тариф
    def activate(self, current_user):
        calc_obj = self.tariff.get_calc_type()(self)
        amnt = self.tariff.amount
        # если не хватает денег
        if self.abon.ballance < amnt:
            raise LogicError(_('not enough money'))
        # считаем дату активации услуги
        self.time_start = timezone.now()
        # считаем дату завершения услуги
        self.deadline = calc_obj.calc_deadline()
        # снимаем деньги за услугу
        self.abon.make_pay(current_user, amnt, u_comment=_('service finish log'))
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
            ('can_complete_service', _('finish service perm')),
            ('can_activate_service', _('activate service perm'))
        )


class AbonStreet(models.Model):
    name = models.CharField(max_length=64)
    group = models.ForeignKey(AbonGroup)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'abon_street'


class ExtraFieldsModel(models.Model):
    DYNAMIC_FIELD_TYPES = (
        ('int', _('Digital field')),
        ('str', _('Text field')),
        ('dbl', _('Floating field'))
    )

    field_type = models.CharField(max_length=3, choices=DYNAMIC_FIELD_TYPES)
    data = models.CharField(max_length=64, null=True, blank=True)

    def clean(self):
        d = self.data
        if self.field_type == 'int':
            validators.validate_integer(d)
        elif self.field_type == 'dbl':
            try:
                float(d)
            except ValueError:
                raise ValidationError(_('Double invalid value'), code='invalid')
        elif self.field_type == 'str':
            str_validator = validators.MaxLengthValidator(64)
            str_validator(d)

    def __str__(self):
        return "%s: %s" % (self.get_field_type_display(), self.data)

    class Meta:
        db_table = 'abon_extra_fields'


class Abon(UserProfile):
    current_tariffs = models.ManyToManyField(Tariff, through=AbonTariff)
    group = models.ForeignKey(AbonGroup, models.SET_NULL, blank=True, null=True)
    ballance = models.FloatField(default=0.0)
    ip_address = models.OneToOneField(IpPoolItem, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    street = models.ForeignKey(AbonStreet, on_delete=models.SET_NULL, null=True, blank=True)
    house = models.CharField(max_length=12, null=True, blank=True)
    extra_fields = models.ManyToManyField(ExtraFieldsModel)

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
            ('can_buy_tariff', _('Buy service perm')),
            ('can_view_passport', _('Can view passport'))
        )

    # Платим за что-то
    def make_pay(self, curuser, how_match_to_pay=0.0, u_comment=_('pay log')):
        AbonLog.objects.create(
            abon=self,
            amount=-how_match_to_pay,
            author=curuser,
            comment=u_comment
        )
        self.ballance -= how_match_to_pay
        self.save(update_fields=['ballance'])

    # Пополняем счёт
    def add_ballance(self, current_user, amount, comment):
        AbonLog.objects.create(
            abon=self,
            amount=amount,
            author=current_user,
            comment=comment
        )
        self.ballance += amount

    # покупаем тариф
    def pick_tariff(self, tariff, author, comment=None):
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
            # значит пробуем её активировать
            new_abtar.activate(author)
        else:
            new_abtar.save()

        # Запись об этом в лог
        AbonLog.objects.create(
            abon=self, amount=-tariff.amount,
            author=author,
            comment=comment or _('Buy service default log')
        )

    # Пробует подключить новую услугу если пришло время
    def activate_next_tariff(self, author):
        ats = AbonTariff.objects.filter(abon=self).order_by('tariff_priority')

        nw = timezone.make_aware(datetime.now())

        for at in ats:
            # услуга не активна, продолжаем
            if at.deadline is None:
                continue
            # если услуга просрочена
            if nw > at.deadline:
                print(_('service overdue log'))
                # выберем следующую по приоритету
                # next_tarifs = AbonTariff.objects.filter(tariff_priority__gt = self.tariff_priority, abon=self.abon)
                next_tarifs = [tr for tr in ats if tr.tariff_priority > at.tariff_priority][:2]
                #next_tarifs = filter(lambda tr: tr.tariff_priority > at.tariff_priority, ats)[:2]

                # и если что-нибудь из списка следующих услуг вернулось - то активируем
                if len(next_tarifs) > 0:
                    next_tarifs[0].activate(author)

                # удаляем запись о текущей услугу.
                at.delete()

    # есть-ли доступ у абонента к услуге, смотрим в tariff_app.custom_tariffs.<TariffBase>.manage_access()
    def is_access(self):
        ats = AbonTariff.objects.filter(abon=self).exclude(time_start=None)
        if not ats or ats.count() < 1: return False
        trf = ats[0].tariff
        ct = trf.get_calc_type()(ats[0])
        if ct.manage_access(self):
            return True
        else:
            return False

    # создаём абонента из структуры агента
    def build_agent_struct(self):
        if self.ip_address:
            user_ip = self.ip_address.int_ip()
        else:
            return
        inst_tariff = self.active_tariff()
        if inst_tariff:
            agent_trf = TariffStruct(inst_tariff.id, inst_tariff.speedIn, inst_tariff.speedOut)
        else:
            agent_trf = TariffStruct()
        return AbonStruct(self.pk, user_ip, agent_trf)


class InvoiceForPayment(models.Model):
    abon = models.ForeignKey(Abon)
    status = models.BooleanField(default=False)
    amount = models.FloatField(default=0.0)
    comment = models.CharField(max_length=128)
    date_create = models.DateTimeField(auto_now_add=True)
    date_pay = models.DateTimeField(blank=True, null=True)
    author = models.ForeignKey(UserProfile, related_name='+')

    def __str__(self):
        return "%s -> %.2f" % (self.abon.username, self.amount)

    def set_ok(self):
        self.status = True
        self.date_pay = timezone.now()

    def get_prev_invoice(self):
        return self.objects.order

    class Meta:
        ordering = ('date_create',)
        db_table = 'abonent_inv_pay'


# Log for pay system "AllTime"
class AllTimePayLog(models.Model):
    pay_id = models.CharField(max_length=36, unique=True, primary_key=True)
    date_add = models.DateTimeField(auto_now_add=True)
    summ = models.FloatField(default=0.0)

    def __str__(self):
        return self.pay_id

    class Meta:
        db_table = 'all_time_pay_log'
        ordering = ('date_add',)


# log for all terminals
class AllPayLog(models.Model):
    pay_id = models.CharField(max_length=64, primary_key=True)
    date_action = models.DateTimeField(auto_now_add=True)
    summ = models.FloatField(default=0.0)
    pay_system_name = models.CharField(max_length=16)

    def __str__(self):
        return self.pay_system_name

    class Meta:
        db_table = 'all_pay_log'
        ordering = ('date_action',)


class AbonRawPassword(models.Model):
    account = models.OneToOneField(Abon, primary_key=True)
    passw_text = models.CharField(max_length=64)

    def __str__(self):
        return "%s - %s" % (self.account, self.passw_text)

    class Meta:
        db_table = 'abon_raw_password'


def abon_post_save(sender, instance, **kwargs):
    #try:
    tm = Transmitter()
    agent_abon = instance.build_agent_struct()
    if agent_abon is None:
        return True
    if kwargs['created']:
        # создаём абонента
        tm.add_user(agent_abon)
    else:
        # обновляем абонента на NAS
        tm.update_user(agent_abon)
        # если не активен то приостановим услугу
        if instance.is_active:
            tm.start_user(agent_abon)
        else:
            tm.pause_user(agent_abon)

    #except NasFailedResult:
    #    return True


def abon_del_signal(sender, instance, **kwargs):
    try:
        ab = instance.build_agent_struct()
        # подключаемся к NAS'у
        tm = Transmitter()
        # нашли абонента, и удаляем его на NAS
        tm.remove_user(ab)
    except NasFailedResult:
        return True


def abontariff_post_save(sender, instance, **kwargs):
    # Тут или подключение абону услуги, или изменение приоритета
    if not kwargs['created']:
        # если изменение приоритета то не говорим об этом NAS'у
        return
    if instance.abon.ip_address is None:
        return
    try:
        agent_abon = instance.abon.build_agent_struct()
        if agent_abon is None:
            return True
        tm = Transmitter()
        tm.update_user(agent_abon)
    except NasFailedResult:
        return True


def abontariff_del_signal(sender, instance, **kwargs):
    if not instance.is_started():
        # если удаляем не активную услугу то говорить об этом NAS'у не обязательно
        return
    if instance.abon.ip_address is None:
        # если у абонента нет ip то и создавать правило не на кого
        return
    try:
        agent_abon = instance.abon.build_agent_struct()
        tm = Transmitter()
        tm.pause_user(agent_abon)
    except NasFailedResult:
        return True


models.signals.post_save.connect(abon_post_save, sender=Abon)
models.signals.post_delete.connect(abon_del_signal, sender=Abon)

models.signals.post_save.connect(abontariff_post_save, sender=AbonTariff)
models.signals.post_delete.connect(abontariff_del_signal, sender=AbonTariff)
