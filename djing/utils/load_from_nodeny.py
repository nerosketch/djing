#!/bin/env python3
# coding=utf-8

import MySQLdb
from json import dumps



def load_users(cursor, grp_id):
    # выбираем абонентов
    sql = r"SELECT users.name, users.fio, data0._adr_telefon, dictionary.v AS street, data0._adr_house, data0._birthday, users.grp, INET_NTOA(ip_pool.ip) AS ip, users.balance, AES_DECRYPT(users.passwd, 'Vu6saiZa') as decr_passwd FROM users LEFT JOIN data0 ON (data0.uid = users.id) LEFT JOIN dictionary ON (dictionary.k = data0._adr_street AND dictionary.type = 'street') LEFT JOIN ip_pool ON (ip_pool.uid = users.id) WHERE users.grp = %d" % grp_id
    cursor.execute(sql)
    users = [{
        'name': str(res[0]),
        'fio': str(res[1]),
        'tel': str(res[2]),
        'street': str(res[3] or ''),
        'house': str(res[4]),
        'birth': res[5],
        'grp': int(res[6]),
        'ip': str(res[7] or ''),
        'balance': float(res[8]),
        'passw': res[9].decode("utf-8") if res[9] is not None else ''
    } for res in cursor.fetchall()]
    return users



def load_groups(cursor):
    # выбираем группы
    sql = r'SELECT grp_id, grp_name FROM user_grp'
    cursor.execute(sql)
    groups = list()
    for res in cursor.fetchall():
        users = load_users(cursor=cursor, grp_id=int(res[0]))
        groups.append({
            'gid': int(res[0]),
            'gname': res[1],
            'users': users
        })
    return groups



if __name__ == "__main__":
    db = MySQLdb.connect(host="127.0.0.1", user="<username>", passwd="<password>", db="db", charset='utf8')
    cursor = db.cursor()

    result = dict()

    result['groups'] = load_groups(cursor=cursor)
    db.close()
    f = open('dump.json', 'w')
    f.write(dumps(result, ensure_ascii=False))
    f.close()
