#!/bin/sh

#########################################################
# ВАЖНО! Биллинг пока ограничен количеством тарифных планов
# не больше 1000
#########################################################




f="/sbin/ipfw -q"

lan=em1 # Clients
wan=em0 # Inet


${f} -f flush
${f} table all flush

sysctl net.inet.ip.fw.one_pass=0

# dns
${f} table 100 add 8.8.8.8    # google public dns
${f} table 100 add 8.8.4.4    # google public dns2
${f} table 100 add 77.88.8.8  # yandex base dns
${f} table 100 add 77.88.8.1  # yandex base dns2


# ssh access
${f} add 50 allow tcp from any to me 22
${f} add 51 allow tcp from me 22 to any


# loopback
${f} add 100 allow ip from any to any via lo0


# в таблице 100 приоритетный траффик.
# это dns, платёжки..
${f} add 500 allow ip from table\(100\) to any
${f} add 501 allow ip from any to table\(100\)



# в таблице 10 разрешённые пользователи
# блокируем трафик всем кто не в ней
${f} add 1001 deny ip from not table\(10\) to any via $wan

# если у абонентов есть внешние адреса (не через NAT)
#${f} add 1101 deny ip from any to not table\(10\) via $wan




# по 2 пайпа на тарифный план, на вход и выход
#${f} pipe 212 config bw 1152Kbit/s mask src-ip 0xffffffff noerror
#${f} pipe 213 config bw 1152Kbit/s mask dst-ip 0xffffffff noerror

# добавляем пайпы в таблицу
${f} add 2001 pipe 212 ip from table\(10\) to any via $wan
${f} add 2002 pipe 213 ip from any to table\(11\) via $wan

#----------------------
# так добавляем абонентов чтоб резать скорость, надо указать номер их пайпа
#${f} table 10 add 10.0.172.138/32 212
#${f} table 11 add 10.0.172.138/32 2212
#----------------------




# тут будем поджимать пользователей когда не хватает канала
