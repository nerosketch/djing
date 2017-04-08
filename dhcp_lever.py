#!/usr/bin/env python3
import os
import sys
import django
from django.core.exceptions import MultipleObjectsReturned, ValidationError
from django.utils.translation import ugettext as _
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
django.setup()
from agent import NasFailedResult, NasNetworkError
from abonapp.models import Abon, Opt82
from ip_pool.models import IpPoolItem


def die(text):
    print(text)
    exit(1)


def get_82_opts(switch_mac, switch_port):
    try:
        opt82 = Opt82.objects.get(mac=switch_mac, port=switch_port)
    except MultipleObjectsReturned:
        Opt82.objects.filter(mac=switch_mac, port=switch_port)[1:].delete()
        return get_82_opts(switch_mac, switch_port)
    except Opt82.DoesNotExist:
        opt82 = Opt82.objects.create(mac=switch_mac, port=switch_port)
    return opt82


def get_or_create_pool_item(ip):
    try:
        ip_item = IpPoolItem.objects.get(ip=ip)
    except IpPoolItem.DoesNotExist:
        ip_item = IpPoolItem.objects.create(ip=ip)
    except MultipleObjectsReturned:
        IpPoolItem.objects.filter(ip=ip)[1:].delete()
        return get_or_create_pool_item(ip)
    return ip_item


def dhcp_commit(client_ip, client_mac, switch_mac, switch_port):
    opt82 = get_82_opts(switch_mac, switch_port)
    if opt82 is None:
        print(_("ERROR: opt82 with mac:%s and port:%d does not exist in db") % (switch_mac, switch_port))
        return
    try:
        abon = Abon.objects.get(opt82=opt82)
        abon.ip_address = get_or_create_pool_item(client_ip)
        abon.is_dhcp = True
        abon.save(update_fields=['ip_address'])
        print(_('Ip address update for %s successfull') % abon.get_short_name())
    except Abon.DoesNotExist:
        print('ERROR: abon with option82(%s-%d) does not exist' % (opt82.mac, opt82.port))


def dhcp_expiry(client_ip):
    try:
        ip_item = IpPoolItem.objects.get(ip=client_ip)
        abon = Abon.objects.get(ip_address=ip_item)
        abon.ip_address = None
        abon.is_dhcp = True
        abon.save(update_fields=['ip_address'])
    except IpPoolItem.DoesNotExist:
        pass
    except Abon.DoesNotExist:
        pass


def dhcp_release(client_ip):
    dhcp_expiry(client_ip)


def main(argv):
    if len(argv) < 3:
        die(_('Too few arguments, exiting...'))
    action = argv[1]
    if action == 'commit':
        if len(argv) < 6:
            die(_('Too few arguments, exiting...'))
        dhcp_commit(argv[2], argv[3], argv[4], int(argv[5]))
    elif action == 'expiry':
        dhcp_expiry(argv[2])
    elif action == 'release':
        dhcp_release(argv[2])


if __name__ == "__main__":
    try:
        main(sys.argv)
    except (NasNetworkError, NasFailedResult) as e:
        print('NAS:', e)
    except (ValidationError, ValueError) as e:
        print('ERROR:', e)
