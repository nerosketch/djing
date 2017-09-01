# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from mydefs import RuTimedelta, safe_int
from datetime import timedelta
from .base_intr import DevBase, SNMPBaseWorker, BasePort


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

    def __init__(self, ip, snmp_community, ver=2):
        DevBase.__init__(self)
        SNMPBaseWorker.__init__(self, ip, snmp_community, ver)

    @staticmethod
    def description():
        return _('DLink switch')

    def reboot(self):
        return self.get_item('.1.3.6.1.4.1.2021.8.1.101.1')

    def get_ports(self):
        nams = self.get_list('.1.3.6.1.4.1.171.10.134.2.1.1.100.2.1.3')
        stats = self.get_list('.1.3.6.1.2.1.2.2.1.7')
        macs = self.get_list('.1.3.6.1.2.1.2.2.1.6')
        speeds = self.get_list('.1.3.6.1.2.1.31.1.1.1.15')
        res = []
        ln = len(speeds)
        for n in range(ln):
            status = True if int(stats[n]) == 1 else False
            res.append(DLinkPort(
                n+1,
                nams[n] if len(nams) > 0 else _('does not fetch the name'),
                status,
                macs[n] if len(macs) > 0 else _('does not fetch the mac'),
                int(speeds[n]) if len(speeds) > 0 else 0,
            self))
        return res

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

    def __init__(self, ip, snmp_community, ver=2):
        DevBase.__init__(self)
        SNMPBaseWorker.__init__(self, ip, snmp_community, ver)

    @staticmethod
    def description():
        return _('PON OLT')

    def reboot(self):
        pass

    def get_ports(self):
        nms = self.get_list('.1.3.6.1.4.1.3320.101.10.1.1.79')

        res = []
        for nm in nms:
            nm = int(nm)
            status = int(self.get_item('.1.3.6.1.2.1.2.2.1.8.%d' % nm))
            signal = self.get_item('.1.3.6.1.4.1.3320.101.10.5.1.5.%d' % nm)
            onu = ONUdev(
                nm,
                self.get_item('.1.3.6.1.2.1.2.2.1.2.%d' % nm),
                True if status == 1 else False,
                self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.3.%d' % nm),
                self.get_item('.1.3.6.1.4.1.3320.101.10.1.1.27.%d' % nm),
                int(signal) / 10 if signal != 'NOSUCHINSTANCE' else 0,
            self)
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
        stats = self.get_list('.1.3.6.1.2.1.2.2.1.7')
        oper_stats = self.get_list('.1.3.6.1.2.1.2.2.1.8')
        #macs = self.get_list('.1.3.6.1.2.1.2.2.1.6')
        speeds = self.get_list('.1.3.6.1.2.1.31.1.1.1.15')
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
        return False

    @staticmethod
    def is_use_device_port():
        return False
