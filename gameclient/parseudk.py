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

import argparse
from bitarray import bitarray
import string
import udk

def findshiftedstrings(bindata, bitoffset):
    emptychar = ' '
    continuationchar = '.'
    stringstart = None
    strings = []
    shiftedbytes = bindata[bitoffset:].tobytes()
    linechars = []
    stringchars = []
    for byteoffset, b in enumerate(shiftedbytes):
        if b == 0:
            if len(stringchars) > 3:
                linechars.extend(stringchars + [continuationchar] * ((len(stringchars) + 1) * 7 + 1))
                stringend = bitoffset + byteoffset * 8
                strings.append((stringstart, stringend, stringchars))
                stringchars = []
            else:
                linechars.extend([emptychar] * (len(stringchars) + 1) * 8)
                stringchars = []
            
        elif chr(b) in string.ascii_letters + string.digits + string.punctuation + ' ':
            if len(stringchars) == 0:
                stringstart = bitoffset + byteoffset * 8
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
        return result, strings

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
        for i, result in enumerate(shiftedstrings):
            if result:
                shiftedstring, strings = result
                #outfile.write('-------------------------\n')
                outfile.write('    %s%s (shifted by %d bits)\n' % (' ' * i, shiftedstring, i))

                #bitoffset = 0
                #for stringstart, stringend, stringchars in strings:
                #    outfile.write('    : (size = %d) %s\n' % (stringstart - bitoffset, bindata[bitoffset:stringstart].to01()))
                #    outfile.write('    : (size = %d, "%s") %s\n' % (stringend - stringstart, ''.join(stringchars), bindata[stringstart:stringend].to01()))
                #    bitoffset = stringend
                #if len(bindata) > bitoffset:
                #    outfile.write('    : (size = %d) %s\n' % (len(bindata) - bitoffset, bindata[bitoffset:].to01()))

        #outfile.write('-------------------------\n')
        outfile.write('\n')


def main(infilename, debug):
    outfilename = infilename + '_parsed.txt'

    with open(infilename, 'rt') as infile:
        with open(outfilename, 'wt') as outfile:
            print('Writing output to %s...' % outfilename)
            
            parser = udk.Parser()

            for i, bindata in enumerate(binfile2packetbits(infile)):
                print('Parsing packet %d...' % (i + 1))
                packet, bitsleft, errormsg = parser.parsepacket(bindata,
                                                                debug = debug,
                                                                exception_on_failure = False)

                outfile.write(packet.tostring() + '\n')
                if bitsleft:
                    outfile.write('Error: parsing failed with the following message:\n'
                                  '    %s\n' % errormsg +
                                  'At this point the following bits still had to be parsed:\n' +
                                  '    %s\n\n' % bitsleft.to01())
                outputshiftedstrings(outfile, bindata)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 
        'This program will parse a binary dump of gameserver packets '
        'such as the one written by gameclient.py, parses it and writes '
        'the result into a text file with the same name as the input, '
        'but with a _parsed.txt suffix')
    parser.add_argument('filename', type=str, help='the bindump file to parse')
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()

    main(args.filename, args.debug)
