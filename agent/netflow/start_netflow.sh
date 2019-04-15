#!/usr/bin/env bash

PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/bin

if ! [ -n "$1" ]; then
    echo 'Missing port parameter'
    exit
fi

port=$1
DIRECTORY=`dirname $(readlink -e "$0")`
mkdir -p /tmp/djing_flow

flow-capture -R ${DIRECTORY}/netflow_handler.sh -p /run/flow.pid -w /tmp/djing_flow -n1 -N0 0/0/${port}
