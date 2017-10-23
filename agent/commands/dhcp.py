# -*- coding: utf-8 -*-
from django.core.exceptions import MultipleObjectsReturned
from django.utils.translation import ugettext as _
from abonapp.models import Abon
from devapp.models import Device, Port


def dhcp_commit(client_ip, client_mac, switch_mac, switch_port):
    try:
        dev = Device.objects.get(mac_addr=switch_mac)
        mngr_class = dev.get_manager_klass()

        port = _('<never mind>')
        if mngr_class.is_use_device_port():
            port = Port.objects.get(device=dev, num=switch_port)
            abon = Abon.objects.get(dev_port=port, device=dev)
        else:
            abon = Abon.objects.get(device=dev)
        if not abon.is_dynamic_ip:
            print('D:', _('User settings is not dynamic'))
            return
        if not abon.is_access():
            print('D:', 'User %s is not access to service' % abon.username)
            return
        abon.ip_address = client_ip
        abon.is_dhcp = True
        abon.save(update_fields=['ip_address'])
        #print('S:', _("Ip address:'%s' update for '%s' successfull, on port: %s") % (client_ip, abon.get_short_name(), port))
    except Abon.DoesNotExist:
        print('N:', _("User with device '%s' does not exist") % dev)
    except Device.DoesNotExist:
        print('N:', _('Device with mac %s not found') % switch_mac)
    except Port.DoesNotExist:
        print('N:', _('Port %d on device with mac %s does not exist') % (int(switch_port), switch_mac))
    except MultipleObjectsReturned as e:
        print('E:', 'MultipleObjectsReturned:', type(e), e)


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
