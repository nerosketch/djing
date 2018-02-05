#!/usr/bin/env python3
import sys
import re
from hashlib import sha256
import requests

API_AUTH_SECRET = 'your api key'

SERVER_DOMAIN = 'http://localhost:8000'


IP_REGEXP = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'


def calc_hash(data):
    if type(data) is str:
        result_data = data.encode('utf-8')
    else:
        result_data = bytes(data)
    return sha256(result_data).hexdigest()


def check_sign(get_list, sign):
    hashed = '_'.join(get_list)
    my_sign = calc_hash(hashed)
    return sign == my_sign


def validate(regexp, string):
    if not bool(re.match(regexp, string)):
        raise ValueError
    return string


def validate_status(text):
    if not text in ('UP', 'DOWN', 'UNREACHABLE'):
        raise ValueError
    return text


def send_request(ip, status, sign):
    r = requests.get(
        "%(domain)s/dev/on_device_down/" % {'domain': SERVER_DOMAIN},
        params={
            'ip': ip,
            'status': status,
            'sign': sign
        })
    if r.status_code == 200:
        print(r.json())
    else:
        print('Status:', r.status_code, r.text)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('You forget parameters, example of usage:\n'
              '$ python3 ./monitoring_agent.py 192.168.0.100 DOWN|UP|UNREACHABLE')
        exit(0)

    if API_AUTH_SECRET == 'your api key':
        raise NotImplementedError('You must specified secret api key')

    dev_ip = validate(IP_REGEXP, sys.argv[1])
    status = validate_status(sys.argv[2])

    sign = calc_hash('_'.join((dev_ip, status, API_AUTH_SECRET)))

    send_request(dev_ip, status, sign)
