#!/bin/bash

FNAME="$1"

if [[ -z "$FNAME" ]]; then
  echo "Нужно имя файла дампа netflow"
  exit 1
fi

CUR_DIR=`dirname $0`

DUMP_FILE="$CUR_DIR/$FNAME"
PATH=/usr/local/sbin:/usr/local/bin:/usr/bin


flow-print -f3 < ${DUMP_FILE} | ${CUR_DIR}/to_mysql \
| mysql -uroot -p jungagent --password=ps
