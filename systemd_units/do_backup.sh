#!/bin/bash

PATH=/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin

cd /var/backups

file="djing`date "+%Y-%m-%d_%H.%M.%S"`.sql.gz"

mysql_passw=MYSQL ROOT PASSWORD

echo show tables | mysql -uroot -p$mysql_passw djingdb | \
	grep -v '^flowstat' | grep -v 'traflost' | grep -v '^Tables' | \
	xargs mysqldump -R -Q --add-locks -uroot --password=$mysql_passw djingdb $1 | gzip > $file

chmod 400 $file
./webdav_backup.py $file

# удаляем старые
find . -name "djing20??-??-??_??.??.??.sql.gz" -mtime +30 -type f -delete
