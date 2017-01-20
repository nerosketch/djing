#!/bin/env python2
import sys
import socket
import struct
from re import sub
from datetime import datetime


def ip2int(strip):
    return struct.unpack("!I", socket.inet_aton(strip))[0]


def convert(query):
    dat = sub(r'\s+', ' ', query.strip('\n')).split(' ')

    if len(dat) == 1:
        return

    src_ip = ip2int(dat[0])
    dst_ip = ip2int(dat[1])
    proto = int(dat[2])
    src_port = int(dat[3])
    dst_port = int(dat[4])
    octets = int(dat[5])
    packets = int(dat[6])

    sql = ",(%d,%d,%d,%d,%d,%d,%d)" % (
        src_ip, dst_ip, proto, src_port, dst_port, octets, packets
    )
    return sql


if __name__ == '__main__':
    f = sys.stdin
    table_name = "flowstat_%s" % datetime.now().strftime("%d%m%Y")
    print(("CREATE TABLE IF NOT EXISTS %s (" % table_name))
    print("`id` int(10) AUTO_INCREMENT NOT NULL,")
    print("`src_ip` INT(10) UNSIGNED NOT NULL,")
    print("`dst_ip` INT(10) UNSIGNED NOT NULL,")
    print("`proto` smallint(2) unsigned NOT NULL DEFAULT 0,")
    print("`src_port` smallint(5) unsigned NOT NULL DEFAULT 0,")
    print("`dst_port` smallint(5) unsigned NOT NULL DEFAULT 0,")
    print("`octets` INT unsigned NOT NULL DEFAULT 0,")
    print("`packets` INT unsigned NOT NULL DEFAULT 0,")
    print("PRIMARY KEY (`id`)")
    print(") ENGINE=MyISAM DEFAULT CHARSET=utf8;")
    ins_sql = r"INSERT INTO %s(`src_ip`, `dst_ip`, `proto`, `src_port`, `dst_port`, `octets`, `packets`) VALUES" % table_name

    # always none
    f.readline()

    while True:
        n = 0xfff
        rs = convert(f.readline())
        if not rs: exit()
        # without first comma
        print(ins_sql)
        print((rs[1:]))
        while n > 0:
            rs = convert(f.readline())
            if not rs: exit()
            print(rs)
            n -= 1
        print(';')

    f.close()
