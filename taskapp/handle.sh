#!/usr/bin/env bash

# $1 - 'start' or 'change'
# $2 - mode
# $3 - dev ip
# $4 - state
# $5 - recipient telephone
# $6 - description
# $7 - abon fio
# $8 - abon address
# $9 - abon telephone


text=''
if [[ "$1" == "start" ]]
then
  text="Нов:"
else
  text="Изм:"
fi

FULLTEXT="TO $5: $text: $7. $8 $9. $2. $6"

echo "$FULLTEXT" >> /tmp/task_sms.log

#/usr/bin/gammu-smsd-inject TEXT $5 -text "$FULLTEXT" -unicode
