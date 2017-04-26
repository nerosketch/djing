#!/bin/bash

FNAME="$1"

if [[ -z "$FNAME" ]]; then
  echo "Нужно имя файла дампа netflow"
  exit 1
fi

CUR_DIR=`dirname $0`

DUMP_FILE="/tmp/djing_flow/$FNAME"
PATH=/usr/local/sbin:/usr/local/bin:/usr/bin
TMP_DUMP=/tmp/djing_flow/djing_flow_dump.tmp

cd $CUR_DIR

mv $DUMP_FILE $TMP_DUMP


./djing_flow < $TMP_DUMP | /usr/bin/mysql -uUSER -h <IP Database> -p <DBUSER> --password=<DB_PASSWORD>

rm $TMP_DUMP

