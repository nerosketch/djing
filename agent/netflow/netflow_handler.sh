#!/bin/sh

DUMP_DIR="/var/db/flows"

DUMP_FILE="$DUMP_DIR/$1"
PATH=/usr/local/sbin:/usr/local/bin:/usr/bin
CUR_DIR=`dirname $0`


flow-print -f3 < ${DUMP_FILE} | ${CUR_DIR}/netflow_handler.py \
| mysql -uroot -p jungagent --password=ps
