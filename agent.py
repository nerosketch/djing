#!/bin/env python2

import os
from agent import main


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")

    while True:
        main(debug=True)
        print "Exit from main, reload..."
