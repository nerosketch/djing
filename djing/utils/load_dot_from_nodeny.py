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
    sql = r"SELECT location, descr FROM places WHERE location LIKE 'Сад_%'"
    cursor.execute(sql)
    places = list()
    res = cursor.fetchone()
    while res:
        places.append({
            'loc': res[0],
            'descr': res[1]
        })
        res = cursor.fetchone()

    db.close()
    f = open('../../places.json', 'w')
    f.write(dumps(places, ensure_ascii=False).encode('utf8'))
    f.close()
