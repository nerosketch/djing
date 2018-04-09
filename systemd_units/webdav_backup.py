#!/usr/bin/env python3
from sys import argv
from datetime import datetime, timedelta
import webdav.client as wc

options = {
    'webdav_hostname': "https://webdav.yandex.ru/",
    'webdav_login': "YANDEX USERNAME",
    'webdav_password': "YANDEX PASSWORD"
}


def remove_old_files(border_time: datetime, client):
    # files that older than border_time will be removed
    for file in client.list('ISBackups'):
        fdate = datetime.strptime(file, 'djing%Y-%m-%d_%H.%M.%S.sql.gz')
        if fdate < border_time:
            del_fname = 'ISBackups/%' % file
            client.clean(del_fname)
            print("rm %s" % del_fname)


if __name__ == '__main__':
    reqfile = argv[1]
    try:
        client = wc.Client(options)
        if reqfile == 'rotate':
            border_time = datetime.now() - timedelta(month=3)
            remove_old_files(border_time, client)
        else:
            client.upload_sync(remote_path="ISBackups/%s" % reqfile, local_path="/var/backups/%s" % reqfile)
    except wc.WebDavException as we:
        print(we, type(we))
