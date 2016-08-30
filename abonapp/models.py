# -*- coding: utf-8 -*-
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.datetime_safe import datetime
from agent import get_TransmitterClientKlass, Abonent, Tariff as AgentTariff
from ip_pool.models import IpPoolItem
from tariff_app.models import Tariff
from django.db import models
from djing import settings
from django.core.validators import DecimalValidator
from accounts_app.models import UserProfile


class LogicError(Exception):

    def __init__(self, value):
         self.value = value

    def __unicode__(self):
        return repr(self.value)


class AbonGroup(models.Model):
    title = models.CharField(max_length=127)
    address = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = 'abonent_groups'

    def __unicode__(self):
        return self.title


class AbonLog(models.Model):
    abon = models.ForeignKey('Abon')
    amount = models.FloatField(default=0.0)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    comment = models.CharField(max_length=128)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'abonent_log'

    def __unicode__(self):
        return self.comment


class AbonTariffManager(models.Manager):

    def update_priorities(self, abonent):
        abon_tariff_list = AbonTariff.objects.filter(abon=abonent).order_by('tariff_priority')

        # Обновляем приоритеты, чтоб по порядку были
        at_pr = 0
        for at in abon_tariff_list:
            at.tariff_priority = at_pr
            at_pr += 1
            at.save()


class AbonTariff(models.Model):
    abon = models.ForeignKey('Abon')
    tariff = models.ForeignKey(Tariff, related_name='linkto_tariff')
    tariff_priority = models.PositiveSmallIntegerField(default=0)

    # время начала действия, остальные что не начали действие - NULL
    time_start = models.DateTimeField(null=True, blank=True, default=None)

    objects = AbonTariffManager()

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
        target_abtar.save()
        self.tariff_priority = tmp_prior
        self.save()

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
        target_abtar.save()
        self.save()

    # Считает текущую стоимость услуг согласно выбранной для тарифа логики оплаты (см. в документации)
    def calc_amount_service(self):
        calc_obj = self.tariff.get_calc_type()
        # calc_obj - instance of tariff_app.custom_tariffs.TariffBase
        amount = calc_obj.calc_amount(self)
        return round(amount, 2)

    # досрочно завершает услугу
    def finish_and_activate_next_tariff(self, author):

        # выберем следующие по приоритету услуги
        next_tarifs = AbonTariff.objects.filter(tariff_priority__gt = self.tariff_priority, abon=self.abon)[:1]

        if next_tarifs.count() < 1:
            raise LogicError(u'У абонента нет следующих назначенных услуг')

        # 0й элемент это следующая подключаемая услуга
        next_tarifs[0].time_start = timezone.now()
        next_tarifs[0].save()

        # сколько денег стоят потраченные ресурсы
        used_services = self.calc_amount_service()

        #теперь к текущему баллансу добавляем сумму не потраченных ресурсов, т.к. полная сумма тарифа списывается при покупке тарифа
        ret_amount = self.tariff.amount - used_services
        self.abon.ballance += ret_amount
        self.abon.save()

        AbonLog.objects.create(
            abon   = self.abon,
            amount = ret_amount,
            author = author,
            comment = u'Досрочное завершение услуги %s' % (self.tariff.title)
        )

    def __unicode__(self):
        return "%d: '%s' - '%s'" % (
            self.tariff_priority,
            self.tariff.title,
            self.abon.get_short_name()
        )

    class Meta:
        ordering = ('tariff_priority',)
        db_table = 'abonent_tariff'
        unique_together = (('abon', 'tariff', 'tariff_priority'),)


class Abon(UserProfile):
    current_tariffs = models.ManyToManyField(Tariff, through=AbonTariff)
    group = models.ForeignKey(AbonGroup, models.SET_NULL, blank=True, null=True)
    ballance = models.FloatField(default=0.0, validators=[DecimalValidator])
    ip_address = models.OneToOneField(IpPoolItem, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=256)

    _act_tar_cache = None

    def active_tariff(self):
        if self._act_tar_cache:
            return self._act_tar_cache

        ats = AbonTariff.objects.filter(abon=self)[:1]

        if ats.count() > 0:
            self._act_tar_cache = ats[0].tariff
            return ats[0].tariff
        else:
            self._act_tar_cache = None
            return

    def save_form(self, abonform_instance):
        try:
            cd = abonform_instance.cleaned_data
            tel = cd['telephone']
            self.username = cd['username'] or tel[1:]
            self.fio = cd['fio']
            self.telephone = tel
            self.is_admin = False
            self.ip_address = get_object_or_404(IpPoolItem, ip=cd['ip_address'])
            self.is_active = True
            self.group = cd['group']
            self.address = cd['address']
        except Http404:
            raise LogicError(u'Введённый IP адрес не добавлен в ip pool')
        except MultipleObjectsReturned:
            raise LogicError(u'Введённый IP адрес не определён')

    class Meta:
        db_table = 'abonent'

    def make_pay(self, curuser, how_match_to_pay=0.0):
        AbonLog.objects.create(
            abon   =  self,
            amount = -how_match_to_pay,
            author =  curuser,
            comment = u'Снятие со счёта средств'
        )
        self.ballance -= how_match_to_pay

    def add_ballance(self, current_user, amount):
        AbonLog.objects.create(
            abon   = self,
            amount = amount,
            author = current_user,
            comment = u'Пополнение счёта через админку'
        )
        self.ballance += amount

    def buy_tariff(self, tariff, author):
        if self.ballance >= tariff.amount:
            # денег достаточно, можно покупать
            self.ballance -= tariff.amount

            # выбераем связь ТарифАбонент с самым низким приоритетом
            abtrf = AbonTariff.objects.filter(abon=self).order_by('-tariff_priority')[:1]
            abtrf = abtrf[0] if abtrf.count() > 0 else None

            # создаём новую связь с приоритетом ещё ниже
            new_abtar = AbonTariff(
                abon=self,
                tariff=tariff,
                tariff_priority=abtrf.tariff_priority+1 if abtrf else -1
            )

            # Если это первая услуга в списке (фильтр по приоритету ничего не вернул)
            if not abtrf:
                # значит она сразу стаёт активной
                new_abtar.time_start = timezone.now()

            new_abtar.save()

            # шлём сигнал о том что абонент купил первую услугу, а значит можно пользоваться инетом
            # сигнал можно слать только после того как будет сохранён новый объект AbonTariff
            if self.is_active and not abtrf:
                tc = get_TransmitterClientKlass()()
                act_tar = self.active_tariff()
                agent_abon = Abonent(
                    self.id,
                    self.ip_address.int_ip(),
                    AgentTariff(
                        act_tar.id if act_tar else 0,
                        act_tar.speedIn if act_tar else 0.0,
                        act_tar.speedOut if act_tar else 0.0
                    )
                )
                tc.signal_abon_refresh_info(agent_abon)
                tc.signal_abon_open_inet(agent_abon)

            # Запись об этом в лог
            AbonLog.objects.create(
                abon = self, amount = -tariff.amount,
                author = author,
                comment = u'Покупка тарифного плана через админку, тариф "%s"' % tariff.title
            )
        else:
            raise LogicError(u'Недостаточно денег на счету абонента')

    # Пробует подключить новую услугу если пришло время
    def activate_next_tariff(self, author):
        ats = AbonTariff.objects.filter(abon=self).order_by('tariff_priority')

        nw = datetime.now(tz=timezone.get_current_timezone())

        for at in ats:
            # Если времени активации нет, то это ещё не активированный тариф
            if not at.time_start:
                return

            # время к началу месяца
            to_start_month = datetime(nw.year, nw.month, 1, tzinfo=timezone.get_current_timezone())

            # проверяем расстояние от Сегодня до начала этого месяца.
            # И от заказа тарифа до начала этого месяца
            if (nw - at.time_start) > (nw - to_start_month):
                # Заказ из прошлого месяца, срок действия закончен
                print u'Заказ из прошлого месяца, срок действия закончен'

                # выберем следующую по приоритету
                #next_tarifs = AbonTariff.objects.filter(tariff_priority__gt = self.tariff_priority, abon=self.abon)
                next_tarifs = filter(lambda tr: tr.tariff_priority > at.tariff_priority, ats)[:2]

                # и если что-нибудь вернулось то активируем, давая время начала действия
                if next_tarifs.count() > 0:
                    next_tarifs[0].time_start = nw
                    next_tarifs[0].save()

                # завершаем текущую услугу.
                at.delete()

                # Создаём лог о завершении услуги
                AbonLog.objects.create(
                    abon   = self,
                    amount = 0,
                    author = author,
                    comment = u'Завершение услуги по истечению срока действия'
                )


class InvoiceForPayment(models.Model):
    abon = models.ForeignKey(Abon)
    status = models.BooleanField(default=False)
    amount = models.FloatField(default=0.0)
    comment = models.CharField(max_length=128)
    date_create = models.DateTimeField(auto_now_add=True)
    date_pay = models.DateTimeField(blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

    def __unicode__(self):
        return "%s -> %d $" % (self.abon.username, self.amount)

    def set_ok(self):
        self.status = True
        self.date_pay = datetime.now()

    def get_prev_invoice(self):
        return self.objects.order

    class Meta:
        ordering = ('date_create',)
        db_table = 'abonent_inv_pay'


#def abon_save_signal(sender, instance, **kwargs):
#    if not kwargs['created']:
#        # if not create (change only)
#        print "Kw1", instance.username, instance.is_active


#models.signals.post_save.connect(abon_save_signal, sender=Abon)
