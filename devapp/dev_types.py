import re
from typing import AnyStr, Iterable, Optional, Dict
from datetime import timedelta
from easysnmp import EasySNMPTimeoutError
from transliterate import translit
from django.utils.translation import gettext_lazy as _, gettext

from djing.lib import RuTimedelta, safe_int
from djing.lib.tln.tln import ValidationError as TlnValidationError, register_onu_ZTE_F660
from .base_intr import (
    DevBase, SNMPBaseWorker, BasePort, DeviceImplementationError,
    ListOrError, DeviceConfigurationError
)


def _norm_name(name: str, replreg=None):
    if replreg is None:
        return re.sub(pattern='\W{1,255}', repl='', string=name, flags=re.IGNORECASE)
    return replreg.sub('', name)


def plain_ip_device_mon_template(device) -> Optional[AnyStr]:
    if not device:
        raise ValueError

    parent_host_name = _norm_name("%d%s" % (
        device.parent_dev.pk, translit(device.parent_dev.comment, language_code='ru', reversed=True)
    )) if device.parent_dev else None

    host_name = _norm_name("%d%s" % (device.pk, translit(device.comment, language_code='ru', reversed=True)))
    mac_addr = device.mac_addr
    r = (
        "define host{",
        "\tuse				generic-switch",
        "\thost_name		%s" % host_name,
        "\taddress			%s" % device.ip_address,
        "\tparents			%s" % parent_host_name if parent_host_name is not None else '',
        "\t_mac_addr		%s" % mac_addr if mac_addr is not None else '',
        "}\n"
    )
    return '\n'.join(i for i in r if i)


class DLinkPort(BasePort):
    def __init__(self, num, name, status, mac, speed, snmp_worker):
        BasePort.__init__(self, num, name, status, mac, speed)
        if not issubclass(snmp_worker.__class__, SNMPBaseWorker):
            raise TypeError
        self.snmp_worker = snmp_worker

    def disable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % ('.1.3.6.1.2.1.2.2.1.7', self.num), 2
        )

    def enable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % ('.1.3.6.1.2.1.2.2.1.7', self.num), 1
        )


class DLinkDevice(DevBase, SNMPBaseWorker):
    def __init__(self, dev_instance):
        DevBase.__init__(self, dev_instance)
        SNMPBaseWorker.__init__(self, dev_instance.ip_address, dev_instance.man_passw, 2)

    @staticmethod
    def description():
        return _('DLink switch')

    def reboot(self):
        return self.get_item('.1.3.6.1.4.1.2021.8.1.101.1')

    def get_ports(self) -> ListOrError:
        interfaces_count = safe_int(self.get_item('.1.3.6.1.2.1.2.1.0'))
        nams = list(self.get_list('.1.3.6.1.4.1.171.10.134.2.1.1.100.2.1.3'))
        stats = list(self.get_list('.1.3.6.1.2.1.2.2.1.7'))
        macs = list(self.get_list('.1.3.6.1.2.1.2.2.1.6'))
        speeds = list(self.get_list('.1.3.6.1.2.1.2.2.1.5'))
        res = []
        try:
            for n in range(interfaces_count):
                status = True if int(stats[n]) == 1 else False
                res.append(DLinkPort(
                    n + 1,
                    nams[n] if len(nams) > 0 else '',
                    status,
                    macs[n] if len(macs) > 0 else _('does not fetch the mac'),
                    int(speeds[n]) if len(speeds) > 0 else 0,
                    self))
            return res
        except IndexError:
            return DeviceImplementationError('Dlink port index error'), res

    def get_device_name(self):
        return self.get_item('.1.3.6.1.2.1.1.1.0')

    def uptime(self) -> timedelta:
        uptimestamp = safe_int(self.get_item('.1.3.6.1.2.1.1.8.0'))
        tm = RuTimedelta(timedelta(seconds=uptimestamp / 100)) or RuTimedelta(timedelta())
        return tm

    def get_template_name(self):
        return 'ports.html'

    def has_attachable_to_subscriber(self) -> bool:
        return True

    @staticmethod
    def is_use_device_port():
        return True

    @staticmethod
    def validate_extra_snmp_info(v: str) -> None:
        # Dlink has no require snmp info
        pass

    def monitoring_template(self, *args, **kwargs) -> Optional[str]:
        device = self.db_instance
        return plain_ip_device_mon_template(device, *args, **kwargs)

    def register_device(self, extra_data: Dict):
        pass


class ONUdev(BasePort):
    def __init__(self, num, name, status, mac, speed, signal, snmp_worker):
        super(ONUdev, self).__init__(num, name, status, mac, speed)
        if not issubclass(snmp_worker.__class__, SNMPBaseWorker):
            raise TypeError
        self.snmp_worker = snmp_worker
        self.signal = signal

    def disable(self):
        pass

    def enable(self):
        pass

    def __str__(self):
        return "%d: '%s' %s" % (self.num, self.nm, self.mac())


class OLTDevice(DevBase, SNMPBaseWorker):
    def __init__(self, dev_instance):
        DevBase.__init__(self, dev_instance)
        SNMPBaseWorker.__init__(self, dev_instance.ip_address, dev_instance.man_passw, 2)

    @staticmethod
    def description():
        return gettext('PON OLT')

    def reboot(self):
        pass

    def get_ports(self) -> ListOrError:
        nms = self.get_list('.1.3.6.1.4.1.3320.101.10.1.1.79')
        res = []
        try:
            for nm in nms:
                n = int(nm)
                status = self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.26.%d' % n)
                signal = self.get_item('.1.3.6.1.4.1.3320.101.10.5.1.5.%d' % n)
                onu = ONUdev(
                    num=n,
                    name=self.get_item('.1.3.6.1.2.1.2.2.1.2.%d' % n),
                    status=True if status == '3' else False,
                    mac=self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.3.%d' % n),
                    speed=0,
                    signal=int(signal) / 10 if signal != 'NOSUCHINSTANCE' else 0,
                    snmp_worker=self)
                res.append(onu)
        except EasySNMPTimeoutError as e:
            return EasySNMPTimeoutError(
                "%s (%s)" % (gettext('wait for a reply from the SNMP Timeout'), e)
            ), res
        return res

    def get_device_name(self):
        return self.get_item('.1.3.6.1.2.1.1.5.0')

    def uptime(self):
        up_timestamp = safe_int(self.get_item('.1.3.6.1.2.1.1.9.1.4.1'))
        tm = RuTimedelta(timedelta(seconds=up_timestamp / 100)) or RuTimedelta(timedelta())
        return tm

    def get_template_name(self):
        return 'olt.html'

    def has_attachable_to_subscriber(self) -> bool:
        return False

    @staticmethod
    def is_use_device_port():
        return False

    @staticmethod
    def validate_extra_snmp_info(v: str) -> None:
        # Olt has no require snmp info
        pass

    def monitoring_template(self, *args, **kwargs) -> Optional[str]:
        device = self.db_instance
        return plain_ip_device_mon_template(device)

    def register_device(self, extra_data: Dict):
        pass


class OnuDevice(DevBase, SNMPBaseWorker):
    def __init__(self, dev_instance):
        DevBase.__init__(self, dev_instance)
        dev_ip_addr = None
        if dev_instance.ip_address:
            dev_ip_addr = dev_instance.ip_address
        else:
            parent_device = dev_instance.parent_dev
            if parent_device is not None and parent_device.ip_address:
                dev_ip_addr = parent_device.ip_address
        if dev_ip_addr is None:
            raise DeviceImplementationError(gettext(
                'Ip address or parent device with ip address required for ONU device'
            ))
        SNMPBaseWorker.__init__(self, dev_ip_addr, dev_instance.man_passw, 2)

    @staticmethod
    def description() -> AnyStr:
        return gettext('PON ONU')

    def reboot(self):
        pass

    def get_ports(self) -> ListOrError:
        return []

    def get_device_name(self):
        pass

    def uptime(self):
        pass

    def get_template_name(self):
        return "onu.html"

    def has_attachable_to_subscriber(self) -> bool:
        return True

    @staticmethod
    def is_use_device_port():
        return False

    def get_details(self):
        if self.db_instance is None:
            return
        num = safe_int(self.db_instance.snmp_extra)
        if num == 0:
            return
        try:
            status = self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.26.%d' % num)
            signal = self.get_item('.1.3.6.1.4.1.3320.101.10.5.1.5.%d' % num)
            distance = self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.27.%d' % num)
            mac = ':'.join('%x' % ord(i) for i in self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.3.%d' % num))
            # uptime = self.get_item('.1.3.6.1.2.1.2.2.1.9.%d' % num)
            signal = safe_int(signal)
            if status.isdigit():
                return {
                    'status': status,
                    'signal': signal / 10 if signal != 0 else 0,
                    'name': self.get_item('.1.3.6.1.2.1.2.2.1.2.%d' % num),
                    'mac': mac,
                    'distance': int(distance) / 10 if distance.isdigit() else 0
                }
        except EasySNMPTimeoutError as e:
            return {'err': "%s: %s" % (_('ONU not connected'), e)}

    @staticmethod
    def validate_extra_snmp_info(v: str) -> None:
        # DBCOM Onu have en integer snmp port
        try:
            int(v)
        except ValueError:
            raise TlnValidationError(_('Onu snmp field must be en integer'))

    def monitoring_template(self, *args, **kwargs) -> Optional[str]:
        device = self.db_instance
        if not device:
            return
        host_name = _norm_name("%d%s" % (device.pk, translit(device.comment, language_code='ru', reversed=True)))
        snmp_item = device.snmp_extra
        mac = device.mac_addr
        if device.ip_address:
            address = device.ip_address
        elif device.parent_dev:
            address = device.parent_dev.ip_address
        else:
            address = None
        r = (
            "define host{",
            "\tuse				device-onu",
            "\thost_name		%s" % host_name,
            "\taddress			%s" % address if address else None,
            "\t_snmp_item		%s" % snmp_item if snmp_item is not None else '',
            "\t_mac_addr		%s" % mac if mac is not None else '',
            "}\n"
        )
        return '\n'.join(i for i in r if i)

    def register_device(self, extra_data: Dict):
        pass


class EltexPort(BasePort):
    def __init__(self, snmp_worker, *args, **kwargs):
        BasePort.__init__(self, *args, **kwargs)
        if not issubclass(snmp_worker.__class__, SNMPBaseWorker):
            raise TypeError
        self.snmp_worker = snmp_worker

    def disable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % ('.1.3.6.1.2.1.2.2.1.7', self.num),
            2
        )

    def enable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % ('.1.3.6.1.2.1.2.2.1.7', self.num),
            1
        )


class EltexSwitch(DLinkDevice):
    @staticmethod
    def description():
        return _('Eltex switch')

    def get_ports(self) -> ListOrError:
        res = []
        for i, n in enumerate(range(49, 77), 1):
            speed = self.get_item('.1.3.6.1.2.1.2.2.1.5.%d' % n)
            res.append(EltexPort(self,
                                 i,
                                 self.get_item('.1.3.6.1.2.1.31.1.1.1.18.%d' % n),
                                 self.get_item('.1.3.6.1.2.1.2.2.1.8.%d' % n),
                                 self.get_item('.1.3.6.1.2.1.2.2.1.6.%d' % n),
                                 int(speed),
                                 ))
        return res

    def get_device_name(self):
        return self.get_item('.1.3.6.1.2.1.1.5.0')

    def uptime(self):
        uptimestamp = safe_int(self.get_item('.1.3.6.1.2.1.1.3.0'))
        tm = RuTimedelta(timedelta(seconds=uptimestamp / 100)) or RuTimedelta(timedelta())
        return tm

    def has_attachable_to_subscriber(self) -> bool:
        return True

    @staticmethod
    def is_use_device_port():
        return False

    def monitoring_template(self, *args, **kwargs) -> Optional[str]:
        device = self.db_instance
        return plain_ip_device_mon_template(device)


def conv_signal(lvl: int) -> float:
    if lvl == 65535: return 0.0
    r = 0
    if 0 < lvl < 30000:
        r = lvl * 0.002 - 30
    elif 60000 < lvl < 65534:
        r = (lvl - 65534) * 0.002 - 30
    return round(r, 2)


class Olt_ZTE_C320(OLTDevice):
    @staticmethod
    def description():
        return gettext('OLT ZTE C320')

    def get_fibers(self):
        fibers = ({
            'fb_id': fiber_id,
            'fb_name': fiber_name,
            'fb_onu_num': safe_int(self.get_item('.1.3.6.1.4.1.3902.1012.3.13.1.1.13.%d' % int(fiber_id)))
        } for fiber_name, fiber_id in self.get_list_keyval('.1.3.6.1.4.1.3902.1012.3.13.1.1.1'))
        return fibers

    def get_ports_on_fiber(self, fiber_num: int) -> Iterable:

        onu_types = self.get_list_keyval('.1.3.6.1.4.1.3902.1012.3.28.1.1.1.%d' % fiber_num)
        onu_ports = self.get_list('.1.3.6.1.4.1.3902.1012.3.28.1.1.2.%d' % fiber_num)
        onu_signals = self.get_list('.1.3.6.1.4.1.3902.1012.3.50.12.1.1.10.%d' % fiber_num)

        # Real sn in last 3 octets
        onu_sns = self.get_list('.1.3.6.1.4.1.3902.1012.3.28.1.1.5.%d' % fiber_num)
        onu_prefixs = self.get_list('.1.3.6.1.4.1.3902.1012.3.50.11.2.1.1.%d' % fiber_num)
        onu_list = ({
            'onu_type': onu_type_num[0],
            'onu_port': onu_port,
            'onu_signal': conv_signal(safe_int(onu_signal)),
            'onu_sn': onu_prefix + ''.join('%.2X' % ord(i) for i in onu_sn[-4:]),  # Real sn in last 4 octets,
            'snmp_extra': "%d.%d" % (fiber_num, safe_int(onu_type_num[1])),
        } for onu_type_num, onu_port, onu_signal, onu_sn, onu_prefix in zip(
            onu_types, onu_ports, onu_signals, onu_sns, onu_prefixs
        ))

        return onu_list

    def get_units_unregistered(self, fiber_num: int) -> Iterable:
        sn_num_list = self.get_list_keyval('.1.3.6.1.4.1.3902.1012.3.13.3.1.2.%d' % fiber_num)
        firmware_ver = self.get_list('.1.3.6.1.4.1.3902.1012.3.13.3.1.11.%d' % fiber_num)
        loid_passws = self.get_list('.1.3.6.1.4.1.3902.1012.3.13.3.1.9.%d' % fiber_num)
        loids = self.get_list('.1.3.6.1.4.1.3902.1012.3.13.3.1.8.%d' % fiber_num)

        return ({
            'mac': ':'.join('%x' % ord(i) for i in sn[-6:]),
            'firmware_ver': frm_ver,
            'loid_passw': loid_passw,
            'loid': loid,
            'sn': sn
        } for frm_ver, loid_passw, loid, (sn, num) in zip(
            firmware_ver, loid_passws, loids, sn_num_list
        ))

    def uptime(self):
        up_timestamp = safe_int(self.get_item('.1.3.6.1.2.1.1.3.0'))
        tm = RuTimedelta(timedelta(seconds=up_timestamp / 100)) or RuTimedelta(timedelta())
        return tm

    def get_long_description(self):
        return self.get_item('.1.3.6.1.2.1.1.1.0')

    def get_hostname(self):
        return self.get_item('.1.3.6.1.2.1.1.5.0')

    def get_template_name(self):
        return 'olt_ztec320.html'


class ZteOnuDevice(OnuDevice):
    @staticmethod
    def description():
        return _('ZTE PON ONU')

    def get_details(self) -> Optional[Dict]:
        if self.db_instance is None:
            return
        snmp_extra = self.db_instance.snmp_extra
        if not snmp_extra:
            return
        try:
            fiber_num, onu_num = snmp_extra.split('.')
            fiber_num, onu_num = int(fiber_num), int(onu_num)
            status = self.get_item('.1.3.6.1.4.1.3902.1012.3.50.12.1.1.1.%d.%d.1' % (fiber_num, onu_num))
            signal = self.get_item('.1.3.6.1.4.1.3902.1012.3.50.12.1.1.10.%d.%d.1' % (fiber_num, onu_num))
            distance = self.get_item('.1.3.6.1.4.1.3902.1012.3.50.12.1.1.18.%d.%d.1' % (fiber_num, onu_num))
            name = self.get_item('.1.3.6.1.4.1.3902.1012.3.50.11.2.1.1.%d.%d' % (fiber_num, onu_num))
            return {
                'status': status,
                'signal': conv_signal(safe_int(signal)),
                'name': name,
                'distance': int(distance) / 10 if distance != 'NOSUCHINSTANCE' else 0
            }
        except ValueError:
            pass

    def get_template_name(self):
        return 'onu_for_zte.html'

    @staticmethod
    def validate_extra_snmp_info(v: str) -> None:
        # for example 268501760.5
        try:
            fiber_num, onu_port = v.split('.')
            int(fiber_num), int(onu_port)
        except ValueError:
            raise TlnValidationError(_('Zte onu snmp field must be two dot separated integers'))

    def monitoring_template(self, *args, **kwargs) -> Optional[str]:
        device = self.db_instance
        if not device:
            return
        host_name = _norm_name("%d%s" % (device.pk, translit(device.comment, language_code='ru', reversed=True)))
        snmp_item = device.snmp_extra
        mac = device.mac_addr
        if device.ip_address:
            address = device.ip_address
        elif device.parent_dev:
            address = device.parent_dev.ip_address
        else:
            address = None
        r = (
            "define host{",
            "\tuse				dev-onu-zte-f660",
            "\thost_name		%s" % host_name,
            "\taddress			%s" % address if address else None,
            "\t_snmp_item		%s" % snmp_item if snmp_item is not None else '',
            "\t_mac_addr		%s" % mac if mac is not None else '',
            "}\n"
        )
        return '\n'.join(i for i in r if i)

    def register_device(self, extra_data: Dict):
        if extra_data is None:
            raise DeviceConfigurationError('You have not info in extra_data field, please fill it in JSON')
        device = self.db_instance
        ip = None
        if device.ip_address:
            ip = device.ip_address
        elif device.parent_dev:
            ip = device.parent_dev.ip_address
        if ip:
            mac = str(device.mac_addr).encode()

            # Format serial number from mac address
            # because saved mac address was make from serial number
            sn = (b'%.2X' % int(x, base=16) for x in mac.split(b':')[-4:])
            sn = b"ZTEG%s" % b''.join(sn)

            telnet = extra_data.get('telnet')
            if telnet is None:
                raise DeviceConfigurationError('For ZTE configuration needed "telnet" section in extra_data')
            login = telnet.get('login')
            password = telnet.get('password')
            if login is None or password is None:
                raise DeviceConfigurationError('For ZTE configuration needed login and'
                                               ' password for telnet access in extra_data')
            stack_num, rack_num, fiber_num, new_onu_port_num = register_onu_ZTE_F660(
                olt_ip=ip, onu_sn=sn, login_passwd=(login.encode(), password.encode()),
                onu_mac=mac
            )
            bin_snmp_fiber_number = "10000{0:08b}{1:08b}00000000".format(rack_num, fiber_num)
            snmp_fiber_num = int(bin_snmp_fiber_number, base=2)
            device.snmp_extra = "%d.%d" % (snmp_fiber_num, new_onu_port_num)
            device.save(update_fields=('snmp_extra',))
