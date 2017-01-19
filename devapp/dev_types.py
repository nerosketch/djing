# -*- coding: utf-8 -*-
from base_intr import DevBase, SNMPBaseWorker, BasePort


oids = {
    'reboot': '.1.3.6.1.4.1.2021.8.1.101.1',
    'get_ports': {
        'names': 'IF-MIB::ifDescr',
        'stats': 'IF-MIB::ifAdminStatus',
        'macs': 'IF-MIB::ifPhysAddress',
        'speeds': 'IF-MIB::ifHighSpeed'
    },
    'name': 'SNMPv2-SMI::mib-2.47.1.1.1.1.7.1',
    'toggle_port': '.1.3.6.1.2.1.2.2.1.7'
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
        ln = len(nams)
        for n in range(0, ln):
            status = True if int(stats[n]) == 1 else False
            res.append(DLinkPort(n+1, nams[n], status, macs[n], int(speeds[n]), self))
        return res

    def get_device_name(self):
        return self.get_item(oids['name'])


DEVICE_TYPES = (
    ('Dl', DLinkDevice),
)


# Example usage
if __name__ == '__main__':
    dev = DLinkDevice('10.115.1.105', 'ertNjuWr', 2)

    print('DevName:', dev.get_device_name())
    ports = dev.get_ports()
    print 'gports'
    for port in ports:
        assert issubclass(port.__class__, BasePort)
        print('\tPort:', port.nm, port.st, port.mac(), port.sp)


    # Disable 2 port
    #print ports[1].disable()
    # Enable 2 port
    print ports[1].enable()
