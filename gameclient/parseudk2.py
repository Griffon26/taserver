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
import string
import sys
import time
import traceback
import udk

def findshiftedstrings(bindata, i):
    emptychar = ' '
    continuationchar = '.'
    shiftedbytes = bindata[i:].tobytes()
    linechars = []
    stringchars = []
    for b in shiftedbytes:
        if b == 0:
            if len(stringchars) > 3:
                linechars.extend(stringchars + [continuationchar] * ((len(stringchars) + 1) * 7 + 1))
                stringchars = []
            else:
                linechars.extend([emptychar] * (len(stringchars) + 1) * 8)
                stringchars = []
            
        elif chr(b) in string.ascii_letters + string.digits + string.punctuation + ' ':
            stringchars.append(chr(b))
            
        else:
            linechars.extend([emptychar] * len(stringchars) * 8)
            stringchars = []
            linechars.extend([emptychar] * 8)

    if len(stringchars) > 3:
        linechars.extend(stringchars + [continuationchar] * ((len(stringchars) + 1) * 7 + 1))
    else:
        linechars.extend([emptychar] * (len(stringchars) + 1) * 8)

    result = ''.join(linechars)
    if result.strip() == '':
        return None
    else:
        return result

def binfile2packetbits(infile):
    for linenr, line in enumerate(infile.readlines()):

        line = line.strip()

        if not line:
            continue

        packetsizestr, bindatastr = line.split()

        packetsize = int(packetsizestr)
        bindata = bitarray(bindatastr, endian='little')

        if packetsize != len(bindata) / 8:
            raise RuntimeError('Packet size does not match number of bits on line %d' % (linenr + 1))

        yield bindata

def outputshiftedstrings(outfile, bindata):
    shiftedstrings = [findshiftedstrings(bindata, i) for i in range(8)]

    if any(shiftedstrings):
        outfile.write('    String overview:\n')
        outfile.write('    %s\n' % bindata.to01())
        for i, shiftedstring in enumerate(shiftedstrings):
            if shiftedstring:
                outfile.write('    %s%s (shifted by %d bits)\n' % (' ' * i, shiftedstring, i))
        outfile.write('\n')

def main(infilename):
    outfilename = infilename + '_parsed2.txt'
    binoutfilename = infilename + '2'

    with open(infilename, 'rt') as infile:
        with open(outfilename, 'wt') as outfile:
            print('Writing output to %s...' % outfilename)
            
            parser = udk.Parser()

            for i, bindata in enumerate(binfile2packetbits(infile)):
                print('Parsing packet %d...' % (i + 1))
                packet = parser.parsepacket(bindata, debug = False)
                outfile.write(packet.tostring() + '\n')

                outputshiftedstrings(outfile, bindata)
                
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: %s <captureddatabindump>' % sys.argv[0])
        print('')
        print('This program will parse a binary dump of gameserver packets')
        print('such as the one written by gameclient.py, parses it and writes')
        print('the result into a text file with the same name as the input,')
        print('but with a _parsed.txt suffix')
        exit(0)

    infilename = sys.argv[1]
    
    main(infilename)
