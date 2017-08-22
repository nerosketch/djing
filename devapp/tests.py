from django.test import TestCase
from . import dev_types


class DevTest(TestCase):

    def setUp(self):
        pass

    def snmp(self):
        dev = dev_types.DLinkDevice('10.115.1.105', '<community>', 2)

        print(('DevName:', dev.get_device_name()))
        ports = dev.get_ports()
        print('gports')
        for port in ports:
            if not issubclass(port.__class__, dev_types.BasePort):
                raise TypeError
            print(('\tPort:', port.nm, port.st, port.mac(), port.sp))
        # Disable 2 port
        print((ports[1].disable()))
        # Enable 2 port
        print((ports[1].enable()))
