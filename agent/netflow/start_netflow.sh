#!/usr/bin/env bash

PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/bin

if ! [ -n "$1" ]; then
    echo 'Missing port parameter'
    exit
fi

port=$1
DIRECTORY=`dirname $(readlink -e "$0")`
mkdir -p /tmp/djing_flow/${port}

flow-capture -R "${DIRECTORY}/netflow_handler.sh ${port}" -p /run/flow.pid -w /tmp/djing_flow/${port} -n1 -N0 0/0/${port}
