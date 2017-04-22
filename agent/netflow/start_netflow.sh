#!/usr/bin/env bash

PATH=/usr/local/sbin:/usr/local/bin:/usr/bin

flow-capture -R /srv/http/djing/agent/netflow/netflow_handler.sh -p /run/flow.pid -w /tmp/djing_flow -n1 -N0 0/0/6343
