#!/bin/bash

PATH=/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin

DIRECTORY=`dirname $(readlink -e "$0")`
tmp_ipuser_file='/tmp/ipuser.txt'

cd "$DIRECTORY"

read -r mysql_database mysql_user mysql_passw mysql_host mysql_port <<< `python3 -c "\
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location('local_settings', '../../djing/local_settings.py')
ls = module_from_spec(spec)
spec.loader.exec_module(ls)
db = ls.DATABASES
ldb = db.get('default')
print('%s %s %s %s %d' % (ldb['NAME'], ldb['USER'],
ldb['PASSWORD'], ldb['HOST'], ldb.get('PORT', 3306)))"`

if ! ping -c 1 ${mysql_host} &> /dev/null; then
    echo "Host ${mysql_host} is not accessible"
fi

# Формируем список абонентов и их id
sql='SELECT INET_ATON(ip_address) as uip, baseaccount_ptr_id FROM abonent WHERE INET_ATON(ip_address) != "NULL";'

count=`mysql -u${mysql_user} -h ${mysql_host} -p --password=${mysql_passw} -D ${mysql_database} -P ${mysql_port} -NBe "select COUNT(*) from abonent WHERE INET_ATON(ip_address) != 'NULL';"`
echo "count: $count" > ${tmp_ipuser_file}

mysql -u ${mysql_user} -h ${mysql_host} -p --password=${mysql_passw} -P ${mysql_port} -D ${mysql_database} -NBe "${sql}" | while read -r uip uid;
do
    echo "${uip}-${uid}" >> ${tmp_ipuser_file}
done

# Сигналим коллекторам чтоб они сбросили дамп в папку /tmp/djing_flow/dump
for fl in /run/flow.pid.*; do
    kill -HUP `cat ${fl}`
    sleep 0.1
done
sleep 1

# Экспортируем всё в mysql
export LD_LIBRARY_PATH=.

flow-cat /tmp/djing_flow/dump/*/*.dmp | ./djing_flow -i ${tmp_ipuser_file} -c | mysql -u ${mysql_user} -h ${mysql_host} -p -D ${mysql_database} -P ${mysql_port} --password=${mysql_passw}

rm -f ${tmp_ipuser_file}
rm -f /tmp/djing_flow/dump/*/*.dmp
rm -f /tmp/djing_flow/*/ft*
