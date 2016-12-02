#!/usr/bin/env bash

# $1 - 'start' or 'change'
# $2 - mode
# $3 - dev ip
# $4 - state
# $5 - recipient telephone
# $6 - description


text=''
if [[ "$1" == "start" ]]
then
  text="Новая задача"
else
  text="Изменение задачи"
fi

FULLTEXT="TO $5: $text: $3, $2. $6"

echo "$FULLTEXT" >> /tmp/task_sms.log

#/usr/bin/gammu-smsd-inject TEXT $5 -text "$FULLTEXT" -unicode
