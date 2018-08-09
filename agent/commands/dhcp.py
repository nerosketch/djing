from typing import Optional
from django.core.exceptions import MultipleObjectsReturned
from abonapp.models import Abon
from devapp.models import Device, Port
from ip_pool.models import IpLeaseModel


def dhcp_commit(client_ip: str, client_mac: str, switch_mac: str, switch_port: int) -> Optional[str]:
    try:
        dev = Device.objects.get(mac_addr=switch_mac)
        mngr_class = dev.get_manager_klass()

        if mngr_class.get_is_use_device_port():
            abon = Abon.objects.get(dev_port__device=dev,
                                    dev_port__num=switch_port,
                                    device=dev)
        else:
            abon = Abon.objects.get(device=dev)
        if not abon.is_dynamic_ip:
            return 'User settings is not dynamic'
        client_ips = tuple(str(ip) for ip in abon.ip_addresses.all())
        if client_ip in client_ips:
            return 'Ip address already existed'
        add_lease_result = abon.add_lease(client_ip, mac_addr=client_mac, network=None)
        if add_lease_result is None:
            if abon.is_access():
                abon.sync_with_nas(created=False)
            else:
                return 'User %s is not access to service' % abon.username
        else:
            return add_lease_result
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
        return 'MultipleObjectsReturned:' + ' '.join((type(e), e, str(switch_port)))


def dhcp_expiry(client_ip: str) -> Optional[str]:
    try:
        lease = IpLeaseModel.objects.get(ip=client_ip)
        lease.is_active = False
        lease.save(update_fields=('is_active',))
        abon = Abon.objects.filter(ip_addresses=lease).first()
        if abon is None:
            return "Subscriber with ip %s does not exist" % client_ip
        abon.sync_with_nas(created=False)
    except IpLeaseModel.DoesNotExist:
        pass


def dhcp_release(client_ip: str) -> Optional[str]:
    return dhcp_expiry(client_ip)
