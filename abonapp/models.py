from datetime import datetime
from ipaddress import ip_address
from typing import Optional

from django.conf import settings
from django.core import validators
from django.core.validators import RegexValidator
from django.db import models, connection, transaction
from django.db.models.signals import post_delete, pre_delete, post_init
from django.dispatch import receiver
from django.shortcuts import resolve_url
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, gettext

from accounts_app.models import UserProfile, MyUserManager, BaseAccount
from agent import Transmitter, AbonStruct, TariffStruct, NasFailedResult, NasNetworkError
from group_app.models import Group
from djing.lib import LogicError
from ip_pool.models import IpLeaseModel, NetworkModel
from tariff_app.models import Tariff, PeriodicPay
from bitfield import BitField


class AbonLog(models.Model):
    abon = models.ForeignKey('Abon', models.CASCADE)
    amount = models.FloatField(default=0.0)
    author = models.ForeignKey(UserProfile, models.CASCADE, related_name='+', blank=True, null=True)
    comment = models.CharField(max_length=128)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'abonent_log'
        permissions = (
            ('can_view_abonlog', _('Can view subscriber logs')),
        )
        ordering = ('-date',)

    def __str__(self):
        return self.comment


class AbonTariff(models.Model):
    tariff = models.ForeignKey(Tariff, models.CASCADE, related_name='linkto_tariff')

    time_start = models.DateTimeField(null=True, blank=True, default=None)

    deadline = models.DateTimeField(null=True, blank=True, default=None)

    def calc_amount_service(self):
        amount = self.tariff.amount
        return round(amount, 2)

    # is used service now, if time start is present than it activated
    def is_started(self):
        return False if self.time_start is None else True

    def __str__(self):
        return "%s: %s" % (
            self.deadline,
            self.tariff.title
        )

    class Meta:
        db_table = 'abonent_tariff'
        permissions = (
            ('can_complete_service', _('finish service perm')),
        )
        verbose_name = _('Abon service')
        verbose_name_plural = _('Abon services')
        ordering = ('time_start',)


class AbonStreet(models.Model):
    name = models.CharField(max_length=64)
    group = models.ForeignKey(Group, models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'abon_street'
        verbose_name = _('Street')
        verbose_name_plural = _('Streets')
        ordering = ('name',)


class AbonManager(MyUserManager):
    def get_queryset(self):
        return super(MyUserManager, self).get_queryset().filter(is_admin=False)


class Abon(BaseAccount):
    current_tariff = models.ForeignKey(AbonTariff, null=True, blank=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(Group, models.SET_NULL, blank=True, null=True, verbose_name=_('User group'))
    ballance = models.FloatField(default=0.0)
    ip_addresses = models.ManyToManyField(IpLeaseModel, verbose_name=_('Ip addresses'))
    # ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name=_('Ip Address'))
    description = models.TextField(_('Comment'), null=True, blank=True)
    street = models.ForeignKey(AbonStreet, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Street'))
    house = models.CharField(_('House'), max_length=12, null=True, blank=True)
    device = models.ForeignKey('devapp.Device', null=True, blank=True, on_delete=models.SET_NULL)
    dev_port = models.ForeignKey('devapp.Port', null=True, blank=True, on_delete=models.SET_NULL)
    is_dynamic_ip = models.BooleanField(default=False)

    MARKER_FLAGS = (
        ('icon_donkey', _('Donkey')),
        ('icon_fire', _('Fire')),
        ('icon_ok', _('Ok')),
        ('icon_king', _('King')),
        ('icon_tv', _('TV')),
        ('icon_smile', _('Smile')),
        ('icon_dollar', _('Dollar')),
        ('icon_service', _('Service')),
        ('icon_mrk', _('Marker'))
    )
    markers = BitField(flags=MARKER_FLAGS, default=0)

    def get_flag_icons(self):
        """
        Return icon list of set flags from self.markers
        :return: ['m-icon-donkey', 'm-icon-tv', ...]
        """
        return tuple("m-%s" % name for name, state in self.markers if state)

    def is_markers_empty(self):
        return int(self.markers) == 0

    def active_tariff(self):
        return self.current_tariff

    objects = AbonManager()

    class Meta:
        db_table = 'abonent'
        permissions = (
            ('can_buy_tariff', _('Buy service perm')),
            ('can_view_passport', _('Can view passport')),
            ('can_add_ballance', _('fill account')),
            ('can_ping', _('Can ping'))
        )
        verbose_name = _('Abon')
        verbose_name_plural = _('Abons')
        ordering = ('fio',)

    def add_ballance(self, current_user, amount, comment):
        AbonLog.objects.create(
            abon=self,
            amount=amount,
            author=current_user if isinstance(current_user, UserProfile) else None,
            comment=comment
        )
        self.ballance += amount

    def pick_tariff(self, tariff, author, comment=None, deadline=None):
        if not isinstance(tariff, Tariff):
            raise TypeError

        amount = round(tariff.amount, 2)

        if tariff.is_admin and author is not None:
            if not author.is_staff:
                raise LogicError(_('User that is no staff can not buy admin services'))

        if self.current_tariff is not None:
            if self.current_tariff.tariff == tariff:
                # if service already connected
                raise LogicError(_('That service already activated'))
            else:
                # if service is present then speak about it
                raise LogicError(_('Service already activated'))

        # if not enough money
        if self.ballance < amount:
            raise LogicError(_('not enough money'))

        new_abtar = AbonTariff.objects.create(
            deadline=deadline, tariff=tariff
        )
        self.current_tariff = new_abtar

        # charge for the service
        self.ballance -= amount

        self.save()

        # make log about it
        AbonLog.objects.create(
            abon=self, amount=-tariff.amount,
            author=author,
            comment=comment or _('Buy service default log')
        )

    # Destroy the service if the time has come
    def bill_service(self, author):
        abon_tariff = self.active_tariff()
        if abon_tariff is None:
            return
        nw = timezone.now()
        # if service is overdue
        if nw > abon_tariff.deadline:
            print("Service %s for user %s is overdued, end service" % (abon_tariff.tariff, self))
            abon_tariff.delete()

    # is subscriber have access to service, view in tariff_app.custom_tariffs.<TariffBase>.manage_access()
    def is_access(self) -> bool:
        if not self.is_active:
            return False
        abon_tariff = self.active_tariff()
        if abon_tariff is None:
            return False
        trf = abon_tariff.tariff
        ct = trf.get_calc_type()(abon_tariff)
        return ct.manage_access(self)

    # make subscriber from agent structure
    def build_agent_struct(self):
        abon_addresses = tuple(ip_address(i.ip) for i in self.ip_addresses.filter(is_active=True))
        # if not abon_addresses:
        #     return
        abon_tariff = self.active_tariff()
        if abon_tariff is None:
            agent_trf = None
        else:
            trf = abon_tariff.tariff
            agent_trf = TariffStruct(trf.id, trf.speedIn, trf.speedOut)
        if len(abon_addresses) > 0:
            return AbonStruct(self.pk, abon_addresses, agent_trf, self.is_access())
        raise LogicError(_('You have not any active leases'))

    def sync_with_nas(self, created: bool) -> Optional[Exception]:
        agent_abon = self.build_agent_struct()
        if agent_abon is None or len(agent_abon.ips) < 1:
            return _('Account has no one active ips')
        try:
            tm = Transmitter()
            if created:
                tm.add_user(agent_abon)
            else:
                tm.update_user(agent_abon)
        except (NasFailedResult, NasNetworkError, ConnectionResetError) as e:
            print('ERROR:', e)
            return e

    def get_absolute_url(self):
        return resolve_url('abonapp:abon_home', self.group.id, self.username)

    def add_lease(self, ip: str, network: Optional[NetworkModel], mac_addr=None):
        existed_client_ips = tuple(l.ip for l in self.ip_addresses.all())
        if ip not in existed_client_ips:
            lease = IpLeaseModel.objects.create_from_ip(ip=ip, net=network, mac=mac_addr)
            if lease is None:
                return 'Error while creating a ip lease'
            self.ip_addresses.add(lease)


class PassportInfo(models.Model):
    series = models.CharField(_('Pasport serial'), max_length=4, validators=(validators.integer_validator,))
    number = models.CharField(_('Pasport number'), max_length=6, validators=(validators.integer_validator,))
    distributor = models.CharField(_('Distributor'), max_length=64)
    date_of_acceptance = models.DateField()
    abon = models.OneToOneField(Abon, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'passport_info'
        verbose_name = _('Passport Info')
        verbose_name_plural = _('Passport Info')
        ordering = ('series',)

    def __str__(self):
        return "%s %s" % (self.series, self.number)


class InvoiceForPayment(models.Model):
    abon = models.ForeignKey(Abon, models.CASCADE)
    status = models.BooleanField(default=False)
    amount = models.FloatField(default=0.0)
    comment = models.CharField(max_length=128)
    date_create = models.DateTimeField(auto_now_add=True)
    date_pay = models.DateTimeField(blank=True, null=True)
    author = models.ForeignKey(UserProfile, related_name='+', on_delete=models.SET_NULL, blank=True, null=True)

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
        permissions = (
            ('can_view_invoiceforpayment', _('Can view invoice for payment')),
        )
        verbose_name = _('Debt')
        verbose_name_plural = _('Debts')


class AllTimePayLogManager(models.Manager):
    @staticmethod
    def by_days():
        cur = connection.cursor()
        cur.execute(r'SELECT SUM(summ) as alsum, DATE_FORMAT(date_add, "%Y-%m-%d") AS pay_date FROM  all_time_pay_log '
                    r'GROUP BY DATE_FORMAT(date_add, "%Y-%m-%d")')
        while True:
            r = cur.fetchone()
            if r is None: break
            summ, dat = r
            yield {'summ': summ, 'pay_date': datetime.strptime(dat, '%Y-%m-%d')}


# Log for pay system "AllTime"
class AllTimePayLog(models.Model):
    abon = models.ForeignKey(Abon, models.SET_DEFAULT, blank=True, null=True, default=None)
    pay_id = models.CharField(max_length=36, unique=True, primary_key=True)
    date_add = models.DateTimeField(auto_now_add=True)
    summ = models.FloatField(default=0.0)
    trade_point = models.CharField(_('Trade point'), max_length=20, default=None, null=True, blank=True)
    receipt_num = models.BigIntegerField(_('Receipt number'), default=0)

    objects = AllTimePayLogManager()

    def __str__(self):
        return self.pay_id

    class Meta:
        db_table = 'all_time_pay_log'
        ordering = ('-date_add',)


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
        ordering = ('-date_action',)


class AbonRawPassword(models.Model):
    account = models.OneToOneField(Abon, models.CASCADE, primary_key=True)
    passw_text = models.CharField(max_length=64)

    def __str__(self):
        return "%s - %s" % (self.account, self.passw_text)

    class Meta:
        db_table = 'abon_raw_password'


class AdditionalTelephone(models.Model):
    abon = models.ForeignKey(Abon, models.CASCADE, related_name='additional_telephones')
    telephone = models.CharField(
        max_length=16,
        verbose_name=_('Telephone'),
        # unique=True,
        validators=(RegexValidator(
            getattr(settings, 'TELEPHONE_REGEXP', r'^(\+[7,8,9,3]\d{10,11})?$')
        ),)
    )
    owner_name = models.CharField(max_length=127)

    def __str__(self):
        return "%s - (%s)" % (self.owner_name, self.telephone)

    class Meta:
        db_table = 'additional_telephones'
        ordering = ('owner_name',)
        permissions = (
            ('can_view_additionaltelephones', _('Can view additional telephones')),
        )
        verbose_name = _('Additional telephone')
        verbose_name_plural = _('Additional telephones')


class PeriodicPayForId(models.Model):
    periodic_pay = models.ForeignKey(PeriodicPay, models.CASCADE, verbose_name=_('Periodic pay'))
    last_pay = models.DateTimeField(_('Last pay time'), blank=True, null=True)
    next_pay = models.DateTimeField(_('Next time to pay'))
    account = models.ForeignKey(Abon, models.CASCADE, verbose_name=_('Account'))

    def payment_for_service(self, author=None, now=None):
        """
        Charge for the service and leave a log about it
        """
        if now is None:
            now = timezone.now()
        if self.next_pay < now:
            pp = self.periodic_pay
            amount = pp.calc_amount()
            next_pay_date = pp.get_next_time_to_pay(self.last_pay)
            abon = self.account
            with transaction.atomic():
                abon.add_ballance(author, -amount, comment=gettext('Charge for "%(service)s"') % {
                    'service': self.periodic_pay
                })
                abon.save(update_fields=('ballance',))
                self.last_pay = now
                self.next_pay = next_pay_date
                self.save(update_fields=('last_pay', 'next_pay'))

    def __str__(self):
        return "%s %s" % (self.periodic_pay, self.next_pay)

    class Meta:
        db_table = 'periodic_pay_for_id'
        ordering = ('last_pay',)


@receiver(post_delete, sender=Abon)
def abon_del_signal(sender, **kwargs):
    abon = kwargs["instance"]
    try:
        ab = abon.build_agent_struct()
        if ab is None:
            return True
        tm = Transmitter()
        tm.remove_user(ab)
    except (NasFailedResult, NasNetworkError):
        return True


@receiver(post_init, sender=AbonTariff)
def abon_tariff_post_init(sender, **kwargs):
    abon_tariff = kwargs["instance"]
    if getattr(abon_tariff, 'time_start') is None:
        abon_tariff.time_start = timezone.now()
    calc_obj = abon_tariff.tariff.get_calc_type()(abon_tariff)
    if getattr(abon_tariff, 'deadline') is None:
        abon_tariff.deadline = calc_obj.calc_deadline()


@receiver(pre_delete, sender=AbonTariff)
def abontariff_pre_delete(sender, **kwargs):
    abon_tariff = kwargs["instance"]
    try:
        abon = Abon.objects.get(current_tariff=abon_tariff)
        ab = abon.build_agent_struct()
        if ab is None:
            return True
        tm = Transmitter()
        tm.remove_user(ab)
    except Abon.DoesNotExist:
        print('ERROR: Abon.DoesNotExist')
    except (NasFailedResult, NasNetworkError, ConnectionResetError) as e:
        print('NetErr:', e)
        return True
