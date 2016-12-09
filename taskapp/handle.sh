#!/usr/bin/env bash

FIRST="$1"              # $1 - 'start' or 'change'
FAIL_MODE="$2"          # $2 - mode
DEVICE_IP="$3"          # $3 - dev ip
STATE="$4"              # $4 - state
AUTHOR_TEL="$5"         # $5 - author telephone
RECIPIENT_TEL="$6"      # $6 - recipient telephone
DESCR="$7"              # $7 - description
ABON_FIO="$8"           # $8 - abon fio
ABON_ADDR="$9"          # $9 - abon address
ABON_TEL="${10}"        # $10- abon telephone
ABON_GRP="${11}"        # $11- имя группы абонента


text=''
if [[ "$FIRST" == "start" ]]
then
  text="Нов"
else
  text="Изм"
fi

# Если задача 'На выполнении' то молчим
if [[ "$STATE" == "C" ]]
then
  exit
fi

# Если задача завершена
if [[ "$STATE" == "F" ]]
then
  text="Задача завершена"
  # Меняем телефон назначения на телефон автора, т.к. при завершении
  # идёт оповещение автору о выполнении
  RECIPIENT_TEL="$AUTHOR_TEL"
fi

FULLTEXT="$text: $ABON_FIO. $ABON_ADDR $ABON_TEL. $ABON_GRP. $FAIL_MODE. $DESCR"

echo "TO $RECIPIENT_TEL: $FULLTEXT" >> /tmp/task_sms.log

/usr/bin/gammu-smsd-inject EMS $RECIPIENT_TEL -text "$FULLTEXT" -unicode
