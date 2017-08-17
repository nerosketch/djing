#!/usr/bin/env python3
import sys
from redis import Redis
from rq import Queue


def die(text):
    print(text)
    exit(1)


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 3:
        die('Too few arguments, exiting...')
    action = argv[1]
    q = Queue(connection=Redis())
    if action == 'commit':
        if len(argv) < 6:
            die('Too few arguments, exiting...')
        q.enqueue('agent.commands.dhcp.dhcp_commit', argv[2], argv[3], argv[4], int(argv[5]))
    elif action == 'expiry':
        q.enqueue('agent.commands.dhcp.dhcp_expiry', argv[2])
    elif action == 'release':
        q.enqueue('agent.commands.dhcp.dhcp_release', argv[2])
