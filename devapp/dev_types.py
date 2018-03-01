# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from mydefs import RuTimedelta, safe_int
from datetime import timedelta
from easysnmp import EasySNMPTimeoutError
from .base_intr import DevBase, SNMPBaseWorker, BasePort, DeviceImplementationError


class DLinkPort(BasePort):

    def __init__(self, num, name, status, mac, speed, snmpWorker):
        BasePort.__init__(self, num, name, status, mac, speed)
        if not issubclass(snmpWorker.__class__ , SNMPBaseWorker):
            raise TypeError
        self.snmp_worker = snmpWorker

    # выключаем этот порт
    def disable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % ('.1.3.6.1.2.1.2.2.1.7', self.num), 2
        )

    # включаем этот порт
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

    def get_ports(self):
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
                    n+1,
                    nams[n] if len(nams) > 0 else _('does not fetch the name'),
                    status,
                    macs[n] if len(macs) > 0 else _('does not fetch the mac'),
                    int(speeds[n]) if len(speeds) > 0 else 0,
                self))
            return res
        except IndexError:
            raise DeviceImplementationError('Dlink port index error')

    def get_device_name(self):
        return self.get_item('.1.3.6.1.2.1.1.1.0')

    def uptime(self):
        uptimestamp = safe_int(self.get_item('.1.3.6.1.2.1.1.8.0'))
        tm = RuTimedelta(timedelta(seconds=uptimestamp/100)) or RuTimedelta(timedelta())
        return tm

    def get_template_name(self):
        return 'ports.html'

    @staticmethod
    def has_attachable_to_subscriber():
        return True

    @staticmethod
    def is_use_device_port():
        return True


class ONUdev(BasePort):
    def __init__(self, num, name, status, mac, speed, signal, snmpWorker):
        super(ONUdev, self).__init__(num, name, status, mac, speed)
        if not issubclass(snmpWorker.__class__, SNMPBaseWorker):
            raise TypeError
        self.snmp_worker = snmpWorker
        self.signal = signal

    # выключаем этот порт
    def disable(self):
        pass

    # включаем этот порт
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
        return _('PON OLT')

    def reboot(self):
        pass

    def get_ports(self):
        nms = self.get_list('.1.3.6.1.4.1.3320.101.10.1.1.79')

        res = []
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
            snmpWorker=self)
            res.append(onu)
        return res

    def get_device_name(self):
        return self.get_item('.1.3.6.1.2.1.1.5.0')

    def uptime(self):
        uptimestamp = safe_int(self.get_item('.1.3.6.1.2.1.1.9.1.4.1'))
        tm = RuTimedelta(timedelta(seconds=uptimestamp/100)) or RuTimedelta(timedelta())
        return tm

    def get_template_name(self):
        return 'olt.html'

    @staticmethod
    def has_attachable_to_subscriber():
        return False

    @staticmethod
    def is_use_device_port():
        return False


class OnuDevice(DevBase, SNMPBaseWorker):

    def __init__(self, dev_instance):
        DevBase.__init__(self, dev_instance)
        SNMPBaseWorker.__init__(self, dev_instance.ip_address, dev_instance.man_passw, 2)

    @staticmethod
    def description():
        return _('PON ONU')

    def reboot(self):
        pass

    def get_ports(self):
        pass

    def get_device_name(self):
        pass

    def uptime(self):
        pass

    def get_template_name(self):
        return "onu.html"

    @staticmethod
    def has_attachable_to_subscriber():
        return True

    @staticmethod
    def is_use_device_port():
        return False

    def get_details(self):
        if self.db_instance is None:
            return
        num = self.db_instance.snmp_item_num
        if num == 0:
            return
        try:
            status = self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.26.%d' % num)
            signal = self.get_item('.1.3.6.1.4.1.3320.101.10.5.1.5.%d' % num)
            distance = self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.27.%d' % num)
            mac = ':'.join(['%x' % ord(i) for i in self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.3.%d' % num)])
            uptime = self.get_item('.1.3.6.1.2.1.2.2.1.9.%d' % num)
            return {
                'status': status,
                'signal': int(signal) / 10 if signal != 'NOSUCHINSTANCE' else 0,
                'name': self.get_item('.1.3.6.1.2.1.2.2.1.2.%d' % num),
                'mac': mac,
                'distance': int(distance) / 10 if distance != 'NOSUCHINSTANCE' else 0
            }
        except EasySNMPTimeoutError as e:
            return {'err': "%s: %s" % (_('ONU not connected'), e)}



class EltexPort(BasePort):

    def __init__(self, snmpWorker, *args, **kwargs):
        BasePort.__init__(self, *args, **kwargs)
        if not issubclass(snmpWorker.__class__, SNMPBaseWorker):
            raise TypeError
        self.snmp_worker = snmpWorker

    # выключаем этот порт
    def disable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % ('.1.3.6.1.2.1.2.2.1.7', self.num),
            2
        )

    # включаем этот порт
    def enable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % ('.1.3.6.1.2.1.2.2.1.7', self.num),
            1
        )


class EltexSwitch(DLinkDevice):

    @staticmethod
    def description():
        return _('Eltex switch')

    def get_ports(self):
        #nams = self.get_list('.1.3.6.1.4.1.171.10.134.2.1.1.100.2.1.3')
        stats = list(self.get_list('.1.3.6.1.2.1.2.2.1.7'))
        oper_stats = list(self.get_list('.1.3.6.1.2.1.2.2.1.8'))
        #macs = self.get_list('.1.3.6.1.2.1.2.2.1.6')
        speeds = list(self.get_list('.1.3.6.1.2.1.31.1.1.1.15'))
        res = []
        for n in range(28):
            res.append(EltexPort(self,
                n+1,
                '',#nams[n] if len(nams) > 0 else _('does not fetch the name'),
                True if int(stats[n]) == 1 else False,
                '',#macs[n] if len(macs) > 0 else _('does not fetch the mac'),
                int(speeds[n]) if len(speeds) > 0 and int(oper_stats[n]) == 1 else 0,
            ))
        return res

    def get_device_name(self):
        return self.get_item('.1.3.6.1.2.1.1.5.0')

    def uptime(self):
        uptimestamp = safe_int(self.get_item('.1.3.6.1.2.1.1.3.0'))
        tm = RuTimedelta(timedelta(seconds=uptimestamp/100)) or RuTimedelta(timedelta())
        return tm

    @staticmethod
    def has_attachable_to_subscriber():
        return True

    @staticmethod
    def is_use_device_port():
        return False
