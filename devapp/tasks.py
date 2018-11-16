from typing import Iterable
from subprocess import run
from celery import shared_task
from devapp.models import Device


@shared_task
def onu_register(device_ids: Iterable[int]):
    with open('/etc/dhcp/macs.conf', 'w') as f:
        for dev_id in device_ids:
            dev = Device.objects.get(pk=dev_id)
            if not dev.has_attachable_to_subscriber() or dev.mac_addr is None:
                continue
            group_code = dev.group.code
            if not group_code:
                continue
            try:
                mn = dev.get_manager_klass()
                dev_code = mn.tech_code
                f.write('subclass "%(group_code)s.%(dev_code)s" "%(mac)s";\n' % {
                    'group_code': group_code,
                    'mac': dev.mac_addr,
                    'dev_code': dev_code
                })
            except TypeError:
                continue
    run(('/usr/bin/sudo', 'systemctl', 'restart', 'isc-dhcp-server.service'))
