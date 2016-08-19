#!/bin/env python2
import sys
import socket
import struct
from re import sub


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

    sql = ",(%s,%s,%d,%d,%d,%d,%d)" % (
        hex(src_ip), hex(dst_ip), proto, src_port, dst_port, octets, packets
    )
    return sql


if __name__=='__main__':
    f=sys.stdin
    print("INSERT INTO flowstat(`src_ip`, `dst_ip`, `proto`, `src_port`, `dst_port`, `octets`, `packets`) VALUES")

    # always none
    f.readline()

    # first line
    rs = convert(f.readline())
    # without first comma
    print(rs[1:])

    while True:
        rs = convert(f.readline())
        if not rs:
            break
        print(rs)
    f.close()
