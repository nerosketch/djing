#!/bin/bash


# old mac address
if [[ $1 =~ ^([0-9A-Fa-f]{1,2}[:-]){5}([0-9A-Fa-f]{1,2})$ ]]; then
  MAC=$1
else
  echo "Bad mac $MAC addr"
  exit
fi


# part code
if [[ $2 =~ ^[a-zA-Z]+$ ]]; then
  PART_CODE=$2
else
  echo 'code must contains only letters'
  exit
fi


DHCP_PATH='/home/bashmak/Projects/djing/macs'
PATH=/usr/local/sbin:/usr/local/bin:/usr/bin:/bin


if grep "${MAC}" "${DHCP_PATH}/${PART_CODE}.conf" > /dev/null; then
  # mac is already exists
  exit
else
  # add new mac
  echo "subclass \"${PART_CODE}\" \"${MAC}\";" >> "${DHCP_PATH}/${PART_CODE}.conf"
fi
