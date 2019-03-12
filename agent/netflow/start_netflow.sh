#!/usr/bin/env bash

PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/bin

mkdir -p /tmp/djing_flow

flow-capture -R /var/www/djing/agent/netflow/netflow_handler.py -p /run/flow.pid -w /tmp/djing_flow -n1 -N0 0/0/6343
