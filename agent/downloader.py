#!/usr/bin/env python3
from urllib import request
from hashlib import sha256

API_AUTH_SECRET = 'piodpaosdpa_sd&3jf[owfafogjaspioha*a'
FILE_LINK = 'http://localhost:8000/dev/nagios/hosts/'

"""
    Example script that downloads config
    file from web via api hash.
"""


def calc_hash(data):
    if type(data) is str:
        result_data = data.encode('utf-8')
    else:
        result_data = bytes(data)
    return sha256(result_data).hexdigest()


if __name__ == '__main__':
    sign = calc_hash(API_AUTH_SECRET)
    request.urlretrieve("%s?sign=%s" % (FILE_LINK, sign), 'nagios_objects.cfg')

