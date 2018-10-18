#!/bin/bash

PATH=/usr/bin:/usr/sbin:/bin

cd /var/backups

file="djing`date "+%Y-%m-%d_%H.%M.%S"`.sql.gz"

export PGPASSWORD=POSTGRES ROOT PASSWORD

pg_dump -O -d djing -h localhost -U djing | gzip > $file

chmod 400 $file
./webdav_backup.py $file

# удаляем старые
find . -name "djing20??-??-??_??.??.??.sql.gz" -mtime +30 -type f -delete

