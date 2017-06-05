#!/usr/bin/env python3
import os
import sys
from rq import Connection, Worker
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
from agent import NasFailedResult, NasNetworkError
from django.core.exceptions import ValidationError


"""
  Заустить этот скрипт как демон, он соединяет redis и django
"""
if __name__ == '__main__':
    try:
        django.setup()
        with Connection():
            qs = sys.argv[1:] or ['default']
            w = Worker(qs)
            w.work()
    except (NasNetworkError, NasFailedResult) as e:
        print('NAS:', e)
    except (ValidationError, ValueError) as e:
        print('ERROR:', e)
