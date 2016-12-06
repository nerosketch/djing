#!/bin/env python2
# coding=utf-8

import os
import MySQLdb
from json import dumps


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")

    db = MySQLdb.connect(host="localhost", user="root", passwd="ps", db="nodeny", charset='utf8')
    cursor = db.cursor()

    result = dict()

    # выбираем абонентов
    sql = r"SELECT users.name, users.fio, data0._adr_telefon, dictionary.v, data0._adr_house, data0._birthday, users.grp FROM users LEFT JOIN data0 ON (data0.uid=users.id) LEFT JOIN dictionary ON (dictionary.k=data0._adr_street AND dictionary.type='street')"
    cursor.execute(sql)
    result['users'] = list()
    res = cursor.fetchone()
    while res:
        result['users'].append({
            'name': res[0],
            'fio': res[1],
            'tel': res[2],
            'addr': u"ул. %s д. %s" % (res[3], res[4]),
            'birth': int(res[5]),
            'grp': int(res[6])
        })
        res = cursor.fetchone()

    # выбираем группы
    sql = r'SELECT grp_id, grp_name FROM user_grp'
    cursor.execute(sql)
    result['groups'] = list()
    res = cursor.fetchone()
    while res:
        result['groups'].append({
            'gid': int(res[0]),
            'gname': res[1]
        })
        res = cursor.fetchone()

    db.close()
    f = open('dump.json', 'w')
    f.write(dumps(result, ensure_ascii=False).encode('utf8'))
    f.close()
