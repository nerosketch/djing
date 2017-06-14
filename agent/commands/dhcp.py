# -*- coding: utf-8 -*-
from django.core.exceptions import MultipleObjectsReturned
from django.utils.translation import ugettext as _
from abonapp.models import Abon, Opt82


def get_82_opts(switch_mac, switch_port):
    try:
        opt82 = Opt82.objects.get(mac=switch_mac, port=switch_port)
    except MultipleObjectsReturned:
        Opt82.objects.filter(mac=switch_mac, port=switch_port)[1:].delete()
        return get_82_opts(switch_mac, switch_port)
    except Opt82.DoesNotExist:
        opt82 = Opt82.objects.create(mac=switch_mac, port=switch_port)
    return opt82


def dhcp_commit(client_ip, client_mac, switch_mac, switch_port):
    opt82 = get_82_opts(switch_mac, switch_port)
    if opt82 is None:
        print(_("ERROR: opt82 with mac:%s and port:%d does not exist in db") % (switch_mac, switch_port))
        return
    try:
        abon = Abon.objects.get(opt82=opt82)
        if not abon.is_access():
            return
        abon.ip_address = client_ip
        abon.is_dhcp = True
        abon.save(update_fields=['ip_address'])
        print(_('Ip address update for %s successfull') % abon.get_short_name())
    except Abon.DoesNotExist:
        print('ERROR: abon with option82(%s-%d) does not exist' % (opt82.mac, opt82.port))


def dhcp_expiry(client_ip):
    try:
        abon = Abon.objects.get(ip_address=client_ip)
        abon.ip_address = None
        abon.is_dhcp = True
        abon.save(update_fields=['ip_address'])
    except Abon.DoesNotExist:
        pass


def dhcp_release(client_ip):
    dhcp_expiry(client_ip)
