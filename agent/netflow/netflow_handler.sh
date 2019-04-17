#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "missing port"
    exit
fi

if [ -z "$2" ]; then
    echo "missing filename"
    exit
fi

fname=$2
port=$1
PATH=/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin

cd /tmp/djing_flow
mkdir -p dump/${port}
echo "mv ${port}/${fname} dump/${port}/${fname}.dmp" >> /tmp/mv.log
mv ${port}/${fname} dump/${port}/${fname}.dmp
