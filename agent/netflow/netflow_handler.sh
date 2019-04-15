#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "missing filename"
    exit
fi

fname=$1
PATH=/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin

cd /tmp/djing_flow
mkdir -p dump
mv ${fname} dump/${fname}.dmp
