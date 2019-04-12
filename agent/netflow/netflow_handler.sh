#!/usr/bin/env bash

if [-n "$1" ]; then
    echo "missing filename"
    exit
fi

fname=$1
PATH=/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin

cd /tmp/djing_flow
mkdir -p /tmp/djing_flow/dump
mv ${fname} /tmp/djing_flow/dump/${fname}.dmp
