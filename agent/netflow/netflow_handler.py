#!/usr/bin/env python3
import MySQLdb
import sys
import os
from importlib import import_module


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("File name of netflow required")
        exit(1)

    FNAME = sys.argv[1]

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = '/tmp/djing_flow'
    tmp_ipuser_file = '/tmp/ipuser.txt'
    tmp_dump_file = '%s/djing_flow_dump.tmp' % tmp_dir

    os.chdir(cur_dir)
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)
    os.rename('/tmp/djing_flow/%s' % FNAME, tmp_dump_file)

    sys.path.append('../../')
    local_settings = import_module('djing.local_settings')

    db = MySQLdb.connect(
        host=local_settings.DATABASES['default']['HOST'],
        user=local_settings.DATABASES['default']['USER'],
        passwd=local_settings.DATABASES['default']['PASSWORD'],
        db=local_settings.DATABASES['default']['NAME'],
        charset='utf8'
    )
    cursor = db.cursor()

    sql = r'SELECT abonent.ip_address, acc.username ' \
          r'FROM abonent ' \
          r'LEFT JOIN accounts_app_userprofile AS acc ON (acc.id = abonent.userprofile_ptr_id) ' \
          r'WHERE abonent.ip_address != 0'
    ln = cursor.execute(sql)
    with open(tmp_ipuser_file, 'w') as f:
        f.write("count: %d\n" % ln)
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            f.write("%d-%s\n" % row)
    db.close()

    os.system(
        'bash -c "export LD_LIBRARY_PATH=. && '
        '%(CUR_DIR)s/djing_flow %(TMP_IPUSER_FILE)s < %(TMP_DUMP)s | '
        '/usr/bin/mysql -u%(DB_USER)s -h %(HOST)s -p %(DB_NAME)s --password=%(DB_PASSW)s"' % {
            'CUR_DIR': cur_dir,
            'TMP_IPUSER_FILE': tmp_ipuser_file,
            'TMP_DUMP': tmp_dump_file,
            'DB_USER': local_settings.DATABASES['default']['USER'],
            'HOST': local_settings.DATABASES['default']['HOST'],
            'DB_NAME': local_settings.DATABASES['default']['NAME'],
            'DB_PASSW': local_settings.DATABASES['default']['PASSWORD']
        })

    os.remove(tmp_dump_file)
    os.remove(tmp_ipuser_file)
