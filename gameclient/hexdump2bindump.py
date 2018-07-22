#!/usr/bin/env python3
#
# Copyright (C) 2018  Maurice van der Pot <griffon26@kfk4ever.com>
#
# This file is part of taserver
# 
# taserver is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# taserver is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with taserver.  If not, see <http://www.gnu.org/licenses/>.
#
    
from bitarray import bitarray
import sys

def main(infilename):

    if infilename.endswith('hexdump'):
        outfilename = infilename[:-7] + 'bindump'
    else:
        outfilename = infilename + '.bindump'

    with open(infilename, 'rt') as infile:
        with open(outfilename, 'wt') as outfile:

            lastoffset = -1
            hexoverall = []
            
            for linenum, line in enumerate(infile):
                line = line.strip()
                
                if not line:
                    continue

                offsettext, rest = line.split('  ', maxsplit=1)
                hexpart, asciipart = rest.split('   ', maxsplit=1)

                lineoffset = int(offsettext, 16)
                if lineoffset > lastoffset:
                    lastoffset = lineoffset
                else:
                    print('Warning: found non-increasing offset on line %d: %s\n' % (linenum + 1, offsettext) +
                          '\n' +
                          'This is probably caused by a known bug in Wireshark,\n' +
                          'so we\'ll just ignore this and stop parsing here.\n'
                          'Everything up to this point has been parsed successfully.')
                    break

                hexthisline = [int('0x%s' % hextext, 16) for hextext in hexpart.split()]
                hexoverall.extend(hexthisline)

                if len(hexthisline) < 16:
                    hexbytes = bytes(hexoverall)
                    hexoverall = []
                    
                    bits = bitarray(endian='little')
                    bits.frombytes(hexbytes)

                    outfile.write('%05d  %s\n' % (len(hexbytes), bits.to01()))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: %s <inputfile.hexdump>')
        sys.exit(-1)
        
    main(sys.argv[1])
