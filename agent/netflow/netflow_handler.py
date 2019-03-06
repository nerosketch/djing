#!/usr/bin/env python3
import MySQLdb
import sys
import os
from importlib import import_module


USING_DB = 'default'


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
    usedb = local_settings.DATABASES.get(USING_DB)

    db = MySQLdb.connect(
        host=usedb['HOST'],
        user=usedb['USER'],
        passwd=usedb['PASSWORD'],
        db=usedb['NAME'],
        charset='utf8'
    )
    cursor = db.cursor()

    sql = (
        "SELECT INET_ATON(ip_address) as uip, baseaccount_ptr_id FROM abonent "
        "WHERE INET_ATON(ip_address) != 'NULL';"
    )
    ln = cursor.execute(sql)
    with open(tmp_ipuser_file, 'w') as f:
        f.write("count: %d\n" % ln)
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            f.write("%d-%d\n" % row)
    db.close()

    os.system(
        '/bin/bash -c "export LD_LIBRARY_PATH=. && '
        '%(CUR_DIR)s/djing_flow %(TMP_IPUSER_FILE)s < %(TMP_DUMP)s | '
        '/usr/bin/mysql -u%(DB_USER)s -h %(HOST)s -p %(DB_NAME)s --password=%(DB_PASSW)s"' % {
            'CUR_DIR': cur_dir,
            'TMP_IPUSER_FILE': tmp_ipuser_file,
            'TMP_DUMP': tmp_dump_file,
            'DB_USER': usedb['USER'],
            'HOST': usedb['HOST'],
            'DB_NAME': usedb['NAME'],
            'DB_PASSW': usedb['PASSWORD']
        })

    os.remove(tmp_dump_file)
    os.remove(tmp_ipuser_file)
