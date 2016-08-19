# -*- coding: utf-8 -*-
from base_intr import DevBase, SNMPBaseWorker


class DLinkDevice(DevBase):

    @staticmethod
    def description():
        return u"Свич D'Link"

    def reboot(self):
        pass


DEVICE_TYPES = (
    ('Dl', DLinkDevice),
)


class SNMPDlinkWorker(SNMPBaseWorker):
    oids = {
        'reboot': '.1.3.6.1.4.1.2021.8.1.101.1',
        'get_ports': {
            'names': 'IF-MIB::ifDescr',
            'stats': 'IF-MIB::ifAdminStatus',
            'macs': 'IF-MIB::ifPhysAddress',
            'speeds': 'IF-MIB::ifHighSpeed'
        },
        'name': 'SNMPv2-SMI::mib-2.47.1.1.1.1.7.1'
    }
