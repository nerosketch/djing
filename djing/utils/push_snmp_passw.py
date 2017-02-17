# -*- coding: utf-8 -*-
import telnetlib
from mydefs import ping
from socket import error
from multiprocessing import Process


# Пробуем настроить свичи через telnet на snmp


def cmd(ip):
    tn = telnetlib.Telnet(ip)
    tn.read_until("login: ")
    tn.write("\n")
    tn.read_until("Password: ")
    tn.write("\n")

    tn.write("create snmp community ertNjuWr ReadWrite\n")
    tn.write("save\n")
    tn.write("save config\n")
    tn.write("save config config_id 1\n")

    tn.write("log\n")
    print((tn.read_all()))
    tn.close()


def prc(ip):
    try:
        if ping(ip):
            cmd(ip)
    except error:
        print(('Error connect to', ip))


if __name__ == '__main__':
    proc_list = list()
    with open('swips.txt', 'r') as f:
        for ln in f:
            ip = ln.strip()
            p = Process(target=prc, args=(ip,))
            p.start()
            proc_list.append(p)
    for proc in proc_list:
        proc.join()
