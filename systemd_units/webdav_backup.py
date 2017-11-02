#!/usr/bin/env python3
import webdav.client as wc
from webdav.client import WebDavException
from sys import argv


options = {
    'webdav_hostname': "https://webdav.yandex.ru/",
    'webdav_login': "YANDEX USERNAME",
    'webdav_password': "YANDEX PASSWORD"
}

if __name__ == '__main__':
    reqfile = argv[1]
    try:
        client = wc.Client(options)
        client.upload_sync(remote_path="ISBackups/%s" % reqfile, local_path="/var/backups/%s" % reqfile)
    except WebDavException as we:
        print(we, type(we))

