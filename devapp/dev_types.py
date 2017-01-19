# -*- coding: utf-8 -*-
from mydefs import RuTimedelta, safe_int
from base_intr import DevBase, SNMPBaseWorker, BasePort



oids = {
    'reboot': '.1.3.6.1.4.1.2021.8.1.101.1',
    'get_ports': {
        'names': '.1.3.6.1.4.1.171.10.134.2.1.1.100.2.1.3',
        'stats': '.1.3.6.1.2.1.2.2.1.7',
        'macs': '.1.3.6.1.2.1.2.2.1.6',
        'speeds': '.1.3.6.1.2.1.31.1.1.1.15'
    },
    'name': '.1.3.6.1.2.1.1.1.0',
    'position': '.1.3.6.1.2.1.1.5.0',
    'toggle_port': '.1.3.6.1.2.1.2.2.1.7',
    'uptime': '.1.3.6.1.2.1.1.8.0'
}


class DLinkPort(BasePort):

    def __init__(self, num, name, status, mac, speed, snmpWorker):
        BasePort.__init__(self, num, name, status, mac, speed)
        assert issubclass(snmpWorker.__class__ , SNMPBaseWorker)
        self.snmp_worker = snmpWorker

    # выключаем этот порт
    def disable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % (oids['toggle_port'], self.num),
            2
        )

    # включаем этот порт
    def enable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % (oids['toggle_port'], self.num),
            1
        )


class DLinkDevice(DevBase, SNMPBaseWorker):

    def __init__(self, ip, snmp_community, ver=2):
        DevBase.__init__(self)
        SNMPBaseWorker.__init__(self, ip, snmp_community, ver)

    @staticmethod
    def description():
        return u"Свич D'Link"

    def reboot(self):
        pass

    def get_ports(self):
        nams = self.get_list(oids['get_ports']['names'])
        stats = self.get_list(oids['get_ports']['stats'])
        macs = self.get_list(oids['get_ports']['macs'])
        speeds = self.get_list(oids['get_ports']['speeds'])
        res = []
        ln = len(speeds)
        for n in range(0, ln):
            status = True if int(stats[n]) == 1 else False
            res.append(DLinkPort(
                n+1,
                nams[n] if len(nams) > 0 else u'не получил имя',
                status,
                macs[n] if len(macs) > 0 else u'не нашёл мак',
                int(speeds[n]) if len(speeds) > 0 else 0,
            self))
        return res

    def get_device_name(self):
        return self.get_item(oids['name'])

    def uptime(self):
        uptimestamp = safe_int(self.get_item(oids['uptime']))
        tm = RuTimedelta(seconds=uptimestamp/100) or RuTimedelta()
        return tm


DEVICE_TYPES = (
    ('Dl', DLinkDevice),
)
