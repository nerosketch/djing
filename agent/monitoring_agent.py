#!/usr/bin/env python3
import sys
import re
from hashlib import sha256
from typing import Iterable, Union, AnyStr

import requests

API_AUTH_SECRET = 'your api key'

SERVER_DOMAIN = 'http://localhost:8000'

MAC_ADDR_REGEX = r'^([0-9A-Fa-f]{1,2}[:-]){5}([0-9A-Fa-f]{1,2})$'


def calc_hash(data):
    if type(data) is str:
        result_data = data.encode('utf-8')
    else:
        result_data = bytes(data)
    return sha256(result_data).hexdigest()


def check_sign(get_list: Iterable, sign_str: str):
    hashed = '_'.join(get_list)
    my_sign = calc_hash(hashed)
    return sign_str == my_sign


def validate(regexp: Union[bytes, str], string: AnyStr):
    if not re.match(regexp, string):
        raise ValueError
    return string


def validate_status(text: str):
    if text not in ('UP', 'DOWN', 'UNREACHABLE'):
        raise ValueError
    return text


def send_request(mac, stat, sign_hash):
    r = requests.get(
        "%(domain)s/dev/on_device_event/" % {'domain': SERVER_DOMAIN},
        params={
            'mac': mac,
            'status': stat,
            'sign': sign_hash
        })
    if r.status_code == 200:
        print(r.json())
    else:
        print('Status:', r.status_code, r.text)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('You forget parameters, example of usage:\n'
              '$ python3 ./monitoring_agent.py a2:c3:12:46:1f:92 DOWN|UP|UNREACHABLE')
        exit(0)

    if API_AUTH_SECRET == 'your api key':
        raise NotImplementedError('You must specified secret api key')

    dev_mac = validate(MAC_ADDR_REGEX, sys.argv[1])
    status = validate_status(sys.argv[2])

    vars_to_hash = [dev_mac, status]
    vars_to_hash.sort()
    vars_to_hash.append(API_AUTH_SECRET)
    sign = calc_hash('_'.join(vars_to_hash))

    send_request(dev_mac, status, sign)
