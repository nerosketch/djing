# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

from netsnmp import Session, VarList, Varbind


class DevBase(object):
    __metaclass__ = ABCMeta

    @staticmethod
    def description():
        """Возвращает текстовое описание"""

    @abstractmethod
    def reboot(self):
        """Перезагружает устройство"""

    @abstractmethod
    def get_statistics(self):
        """Получаем статистику"""

    @abstractmethod
    def get_vlan(self):
        """Получаем инфу о VLAN"""

    @abstractmethod
    def get_ports(self):
        """Получаем инфу о портах"""

    @abstractmethod
    def toggle_port(self, port_num):
        pass


class Port(object):

    def __init__(self, num, name, status, mac, speed):
        self.num = int(num)
        self.nm = name
        self.st = status
        self._mac = mac
        self.sp = speed

    def mac(self):
        m = self._mac
        return "%x:%x:%x:%x:%x:%x" % (ord(m[0]), ord(m[1]), ord(m[2]), ord(m[3]), ord(m[4]), ord(m[5]))


class SNMPBaseWorker(object):
    ses = None

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

    def __init__(self, ip, passw='public', ver=2):
        self.ses = Session(DestHost=ip, Version=ver, Community=passw)

    def _get_vars(self, oid):
        vs = VarList(Varbind(oid))
        return self.ses.walk(vs)

    def _get_var(self, oid):
        var = VarList(Varbind(oid))
        return self.ses.get(var)

    # Enable/Disable port
    def toggle_port(self, port_num, status=True):
        vs = VarList(Varbind(
            tag="%s.%d" % (self.oids['toggle_port'], port_num),
            val=1 if status else 2,
            type='INTEGER'
        ))
        return self.ses.set(vs)

    def get_ports(self):
        nams = self._get_vars(self.oids['get_ports']['names'])
        stats = self._get_vars(self.oids['get_ports']['stats'])
        macs = self._get_vars(self.oids['get_ports']['macs'])
        speeds = self._get_vars(self.oids['get_ports']['speeds'])
        res = []
        ln = len(nams)
        for n in range(0, ln):
            res.append(Port(n, nams[n], bool(stats[n]), macs[n], int(speeds[n])))
        return res

    def get_name(self):
        return self._get_var(self.oids['name'])


# Example usage
if __name__ == '__main__':
    wrk = SNMPBaseWorker('10.115.1.104', 'private', 2)
    print(wrk.get_name())
    for pr in wrk.get_ports():
        assert isinstance(pr, Port)
        print(pr.nm, pr.st, pr.mac(), pr.sp)

    # Enable 2 port
    print wrk.toggle_port(2, True)
    # Disable 2 port
    print wrk.toggle_port(2, False)
