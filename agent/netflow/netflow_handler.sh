#!/usr/bin/env bash

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
mkdir -p /tmp/djing_flow
mv $DUMP_FILE $TMP_DUMP

./djing_flow < $TMP_DUMP | /usr/bin/mysql -uDB_USER -h <DB_IP> -p djingdb --password=PASSWORD

rm $TMP_DUMP
