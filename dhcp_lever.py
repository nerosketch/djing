#!/usr/bin/env python3
import sys
import socket


def die(text):
    print(text)
    exit(1)

'''
obj = {
    'client_ip': ip2int('127.0.0.1'),
    'client_mac': 'aa:bb:cc:dd:ee:ff',
    'switch_mac': 'aa:bb:cc:dd:ee:ff',
    'switch_port': 3,
    'cmd': 'commit'
}
'''


def send_to(data, addr='127.0.0.1', port=5436):
    from pickle import dumps
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((addr, port))
            data = dumps(data)
            s.send(data)
    except ConnectionRefusedError:
        print('ERROR: connection refused')


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 3:
        die('Too few arguments, exiting...')
    action = argv[1]
    if action == 'commit':
        if len(argv) < 6:
            die('Too few arguments, exiting...')
        dat = {
            'client_ip': argv[2],
            'client_mac': argv[3],
            'switch_mac': argv[4],
            'switch_port': int(argv[5]),
            'cmd': 'commit'
        }
        send_to(dat)
    elif action == 'expiry' or action == 'release':
        dat = {
            'client_ip': argv[2],
            'cmd': action
        }
        send_to(dat)
