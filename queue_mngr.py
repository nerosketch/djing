#!/usr/bin/env python3
import os
from pickle import loads
from pid.decorator import pidfile
import socket
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
from mydefs import LogicError

'''
obj = {
    'client_ip': ip2int('127.0.0.1'),
    'client_mac': 'aa:bb:cc:dd:ee:ff',
    'switch_mac': 'aa:bb:cc:dd:ee:ff',
    'switch_port': 3,
    'cmd': 'commit'
}
'''


def on_new_data(client_sock, ip):
    try:
        data = client_sock.recv(16384)
        data = loads(data)
        action = data['cmd']
        if action == 'commit':
            dhcp_commit(
                data['client_ip'], data['client_mac'],
                data['switch_mac'], data['switch_port']
            )
        elif action == 'expiry':
            dhcp_expiry(data['client_ip'])
        elif action == 'release':
            dhcp_release(data['client_ip'])
    except LogicError as e:
        print('LogicError', e)
    finally:
        client_sock.close()


@pidfile(pidname='queue_mngr.py.pid', piddir='/run')
def serve(addr='127.0.0.1', port=5436):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((addr, port))
            s.listen(3)
            print('ready')
            while True:
                conn, client_addr = s.accept()
                on_new_data(conn, client_addr)
    except ConnectionRefusedError:
        print('ERROR: connection refused')


if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
    django.setup()
    from agent.commands.dhcp import dhcp_commit, dhcp_expiry, dhcp_release

    serve()
