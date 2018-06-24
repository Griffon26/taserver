#!/usr/bin/env python3

def hexdump(data):
    bytelist = [ '%02X' % b for b in data ]
    offset = 0
    while len(bytelist) > offset + 16:
        print('%04X: %s' % (offset, ' '.join(bytelist[offset:offset + 16])))
        offset += 16
    print('%04X: %s' % (offset, ' '.join(bytelist[offset:])))


