#!/usr/bin/env python
# encoding: utf-8
"""Script to dump data from STDIN into files

Useful for example to:
- debug procmail rules
- save email messages for futher testing/
  processing with the forwarder-script.

"""

import sys
import os
import time


DUMPPATH="/tmp/mail_dumps"


def check_dir(ospath):
    """checks if path exists and tries to create it if not
    """
    if os.path.exists(ospath):
        return True
    else:
        try:
            os.path.mkdir(ospath)
            print "created subdir: %s" % ospath
            return True
        except IOError:
            print "Error creating path: %s" % ospath
            sys.exit(1)


def generate_filename():
    """generates filename from date+time

    @returns:   filename including path
    """
    name = int(time.time())     # e.g. 1359558393
    name = str(name)+'.msg'     # add file extension
    check_dir(DUMPPATH)         # bails out on error
    name = DUMPPATH+os.path.sep+name
    return name


def dump_to_file(data):
    """dump given data into a file
    """
    name = generate_filename()
    print "saving into: %s" % name
    with open(name, 'w') as f:
        f.write(data)


def main():
    data = sys.stdin.read()
    dump_to_file(data)


if __name__ == '__main__':
    main()
