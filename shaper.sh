#!/usr/bin/bash

IfNet=em0
IfUsr=em1

f=/sbin/ipfw

${f} -f flush
${f} -f pipe flush
${f} -f table all flush


# Разрешаем ICMP
${f} add 50 allow icmp from any to any


# список разрешённых пользователей - table15
${f} add 501 allow ip from "table(15)" to any out recv ${IfUsr} xmit ${IfNet}


# На каждый тарифный план по пайпу
${f} pipe 212 config bw 1152Kbit/s mask src-ip 0xffffffff noerror
${f} pipe 213 config bw 1152Kbit/s mask dst-ip 0xffffffff noerror

# создаём эти пайпы
${f} add 1001 pipe tablearg ip from "table(12)" to any out recv ${IfUsr} xmit ${IfNet}
${f} add 1002 pipe tablearg ip from any to "table(13)" out recv ${IfNet} xmit ${IfUsr}

# ------- Так добавляются пользователи
${f} table 12 add 10.0.172.138/32 212
${f} table 13 add 10.0.172.138/32 213
