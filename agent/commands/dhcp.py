# -*- coding: utf-8 -*-
from typing import Optional
from django.core.exceptions import MultipleObjectsReturned
from abonapp.models import Abon
from devapp.models import Device, Port


def dhcp_commit(client_ip: str, client_mac: str, switch_mac: str, switch_port: int) -> Optional[str]:
    try:
        dev = Device.objects.get(mac_addr=switch_mac)
        mngr_class = dev.get_manager_klass()

        if mngr_class.is_use_device_port():
            abon = Abon.objects.get(dev_port__device=dev,
                                    dev_port__num=switch_port,
                                    device=dev)
        else:
            abon = Abon.objects.get(device=dev)
        if not abon.is_dynamic_ip:
            print('D:', 'User settings is not dynamic')
            return
        if not abon.is_access():
            print('D:', 'User %s is not access to service' % abon.username)
            return
        if abon.ip_address != client_ip:
            abon.ip_address = client_ip
            abon.save(update_fields=['ip_address'])
            abon.sync_with_nas(created=False)
    except Abon.DoesNotExist:
        return "User with device with mac '%s' does not exist" % switch_mac
    except Device.DoesNotExist:
        return 'Device with mac %s not found' % switch_mac
    except Port.DoesNotExist:
        return 'Port %(switch_port)d on device with mac %(switch_mac)s does not exist' % {
            'switch_port': int(switch_port),
            'switch_mac': switch_mac
        }
    except MultipleObjectsReturned as e:
        return 'MultipleObjectsReturned:' + ' '.join([type(e), e, str(switch_port)])


def dhcp_expiry(client_ip) -> Optional[str]:
    try:
        abon = Abon.objects.get(ip_address=client_ip)
        abon.ip_address = None
        abon.save(update_fields=['ip_address'])
        abon.sync_with_nas(created=False)
    except Abon.DoesNotExist:
        return "Subscriber with ip %s does not exist" % client_ip


def dhcp_release(client_ip) -> Optional[str]:
    return dhcp_expiry(client_ip)
