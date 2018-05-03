import socket
import struct


def ip2int(addr):
    try:
        return struct.unpack("!I", socket.inet_aton(addr))[0]
    except:
        return 0


def int2ip(addr):
    try:
        return socket.inet_ntoa(struct.pack("!I", addr))
    except:
        return ''
