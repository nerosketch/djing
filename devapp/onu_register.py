#!/usr/bin/env python3
from typing import Iterable
from subprocess import run


def onu_register(devices: Iterable):
    with open('/etc/dhcp/macs.conf', 'w') as f:
        for dev in devices:
            if dev.has_attachable_to_subscriber():
                f.write('subclass "%(code)s" "%(mac)s";\n' % {
                    'code': dev.group.code,
                    'mac': dev.mac_addr
                })
    run(('/usr/bin/sudo', 'systemctl', 'restart', 'isc-dhcp-server.service'))
