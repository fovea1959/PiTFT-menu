#!/usr/bin/env python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 fileencoding=latin-1

# from https://stackoverflow.com/questions/5060710/format-of-dev-input-event
# see Treviño's answer

import struct
import time
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input', default='/dev/input/touchscreen', nargs='?', help='input file')
parser.add_argument('-1', '--one', action='store_true', help='quit after 1st event received')
            
args = parser.parse_args()

#long int, long int, unsigned short, unsigned short, unsigned int
FORMAT = 'llHHI'
EVENT_SIZE = struct.calcsize(FORMAT)

#open file in binary mode
with open(args.input, 'rb') as in_file:
    while True:
        event = in_file.read(EVENT_SIZE)
        if not event:
            break

        if args.one:
            break

        (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)
        if type != 0 or code != 0 or value != 0:
            print('Event type %u, code %u, value %u at %d.%d' % \
                (type, code, value, tv_sec, tv_usec))
        else:
            # Events with code, type and value == 0 are 'separator' events
            print('===========================================')
