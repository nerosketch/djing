#!/bin/bash

# Action
ACT=$1
if [[ ${ACT} == '' ]]; then
  echo 'Need the action type parameter'
  exit
fi


# old mac address
if [[ $2 =~ ^([0-9A-Fa-f]{1,2}[:-]){5}([0-9A-Fa-f]{1,2})$ ]]; then
  MAC=$2
else
  echo "Bad mac $MAC addr"
  exit
fi


# part code
if [[ $3 =~ ^[a-zA-Z]+$ ]]; then
  PART_CODE=$3
else
  echo 'code must contains only letters'
  exit
fi


DHCP_MACS='/etc/dhcp/macs.conf'
PATH=/usr/local/sbin:/usr/local/bin:/usr/bin:/bin


# if just remove device
if [[ ${ACT} == 'del' ]]; then
  sed -i "/${MAC}/d" ${DHCP_MACS}
  exit
fi


# If exist mac with code
if grep "^subclass\ \"${PART_CODE}\" \"${MAC}\";$" "${DHCP_MACS}" > /dev/null; then
  # mac is already exists, quit
  exit
else

  # If mac existing in another group
  if grep "${MAC}" ${DHCP_MACS} > /dev/null; then
    # remove it
    sed -i "/${MAC}/d" ${DHCP_MACS}
  fi

  # add new mac
  echo "subclass \"${PART_CODE}\" \"${MAC}\";" >> ${DHCP_MACS}
  sudo systemctl restart isc-dhcp-server.service
fi
