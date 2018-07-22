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
import struct
import sys
import time
import traceback

actormap = {
    4: 'TrPlayerController_0',
    7: 'TrFlagCTF_BloodEagle_0',
    8: 'TrFlagCTF_DiamondSword_0'
}

propertymap = {
    21: 'PlayerReplicationInfo',
    55: 'Team'
}


class ParseError(Exception):
    pass

def toint(bits):
    zerobytes = bytes( (0,0,0,0) )
    longbytes = (bits.tobytes() + zerobytes)[0:4]
    return struct.unpack('<L', longbytes)[0]

def getnbits(n, bits):
    if n > len(bits):
        raise EOFError
    return bits[0:n], bits[n:]

def getstring(bits):
    stringbytes = bits.tobytes()
    result = []
    for b in stringbytes:
        if b != 0:
            result.append(chr(b))
        else:
            break

    return ''.join(result), bits[(len(result) + 1) * 8:]

class PacketWriter():
    def __init__(self, outfile):
        self.offset = 0
        self.outfile = outfile
        self.indentlevels = []

    def _writeindentedline(self, something):
        self.outfile.write(self.offset * ' ' + something + '\n')

    def writefield(self, bits, description):
        if bits:
            self._writeindentedline('%s %s' % (bits.to01(), description))
            self.offset += len(bits)
        else:
            self._writeindentedline('x %s' % description)
            self.offset += 1
        self.indentlevels.append(self.offset)

    def writerest(self, message, bits):
        self.offset = 0
        self.indentlevels = []
        if len(bits) > 0:
            self._writeindentedline(message + ': ' + bits.to01() + '\n')

    def writeline(self, line):
        if self.offset != 0:
            raise RuntimeError('Cannot write line in the middle of another')
        self.outfile.write(line + '\n')

    def exdent(self, count):
        self.indentlevels = self.indentlevels[:-count]
        self.offset = self.indentlevels[-1]

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

def main(infilename):
    outfilename = infilename + '_parsed.txt'

    with open(infilename, 'rt') as infile:
        with open(outfilename, 'wt') as outfile:
            packetwriter = PacketWriter(outfile)
            
            for linenr, line in enumerate(infile.readlines()):

                line = line.strip()

                if not line:
                    continue

                packetsizestr, bindatastr = line.split()

                packetsize = int(packetsizestr)
                bindata = bitarray(bindatastr, endian='little')
                originalbindata = bitarray(bindata)

                if packetsize != len(bindata) / 8:
                    raise RuntimeError('Packet size does not match number of bits on line %d' % (linenr + 1))

                packetwriter.writeline('Packet with size %d' % packetsize)

                shiftedstrings = [findshiftedstrings(bindata, i) for i in range(8)]

                seqnrbits, bindata = getnbits(14, bindata)
                seqnr = toint(seqnrbits)
                packetwriter.writefield(seqnrbits, '(seqnr = %d)' % seqnr)

                try:
                    state = 'flag1'
                    while len(bindata) > 0:
                        if state == 'flag1':
                            flag1bits, bindata = getnbits(1, bindata)
                            flag1 = toint(flag1bits)
                            packetwriter.writefield(flag1bits, '(flag1 = %d)' % flag1)

                            if flag1:
                                numbits, bindata = getnbits(14, bindata)
                                num = toint(numbits)
                                packetwriter.writefield(numbits, '(num = %d)' % num)
                                continue
                            else:
                                state = 'flag1a'

                        elif state == 'flag1a':
                            flag1abits, bindata = getnbits(2, bindata)
                            flag1a = toint(flag1abits)
                            packetwriter.writefield(flag1abits, '(flag1a = %d)' % flag1a)

                            if flag1a == 0b00:
                                channelbits, bindata = getnbits(10, bindata)
                                channel = toint(channelbits)
                                packetwriter.writefield(channelbits, '(channel = %d)' % channel)

                                sizebits, bindata = getnbits(8, bindata)
                                size = toint(sizebits)
                                packetwriter.writefield(sizebits, '(size = %d)' % size)

                                payloadbits, bindata = getnbits(size, bindata)

                                if len(payloadbits) == 16:
                                    unknownbits, payloadbits = getnbits(6, payloadbits)
                                    packetwriter.writefield(unknownbits, '(unknown)')
                                    
                                    propertybits, payloadbits = getnbits(6, payloadbits)
                                    property_ = toint(propertybits)
                                    packetwriter.writefield(propertybits, '(property = %d:%s)' % (property_, propertymap.get(property_, '???')))
                                    
                                    actorbits, payloadbits = getnbits(4, payloadbits)
                                    actor = toint(actorbits)
                                    packetwriter.writefield(actorbits, '(actor = %d:%s)' % (actor, actormap.get(actor, '???')))
                                else:
                                    packetwriter.writefield(payloadbits, '(payload)')

                                endmarkerbits, bindata = getnbits(7, bindata)
                                theend = 'yes' if endmarkerbits[6] else 'no'
                                packetwriter.writefield(endmarkerbits, '(theend? = %s)' % theend)

                                if endmarkerbits == bitarray('0000001'):
                                    break

                            elif flag1a == 0b10:
                                unknownbits, bindata = getnbits(10, bindata)
                                packetwriter.writefield(unknownbits, '')

                                counterbits, bindata = getnbits(5, bindata)
                                counter = toint(counterbits)
                                packetwriter.writefield(counterbits, '(counter = %d)' % counter)

                                unknownbits, bindata = getnbits(17, bindata)
                                packetwriter.writefield(unknownbits, '')

                                nrofitemsbits, bindata = getnbits(5, bindata)
                                nrofitems = toint(nrofitemsbits)
                                packetwriter.writefield(nrofitemsbits, '(nr of items = %d)' % nrofitems)

                                while True:
                                    part1flags, bindatatmp = getnbits(2, bindata)
                                    if toint(part1flags) == 0b01:
                                        packetwriter.writefield(part1flags, '(end of list)')
                                        bindata = bindatatmp
                                        state = 'flag1'
                                        break
                                    
                                    part1bits, bindata = getnbits(168, bindata)
                                    packetwriter.writefield(part1bits, '')

                                    part1name, bindata = getstring(bindata)
                                    packetwriter.writefield(None, '(%s)' % part1name)

                                    part2flags, _ = getnbits(2, bindata)
                                    nbits = 144 if part2flags[1] else 128
                                    part2bits, bindata = getnbits(nbits, bindata)
                                    packetwriter.writefield(part2bits, '')
                                    
                                    part2name, bindata = getstring(bindata)
                                    packetwriter.writefield(None, '(%s)' % part2name)

                                    packetwriter.exdent(4)

                            elif flag1a == 0b01:
                                break
                            elif flag1a == 0b11:
                                break
                            else:
                                raise ParseError('Unknown value for flag1a: %s' % flag1a)
                        else:
                            raise ParseError('Unknown value for state: %s' % state)

                except UnicodeEncodeError as e:
                    packetwriter.writerest('ERROR: Failed conversion to unicode (%s)' % str(e), bindata)
                except EOFError:
                    packetwriter.writerest('ERROR: Attempted to read more bits than what\'s left', bindata)
                else:
                    # Don't report an error when the only bits left are the last few of the last byte
                    if len(bindata) > 7 or toint(bindata) != 0:
                        packetwriter.writerest('ERROR: Bits left after parsing', bindata)
                    else:
                        packetwriter.writerest('Bits left over in the last byte', bindata)

                if any(shiftedstrings):
                    packetwriter.writeline('    String overview:')
                    packetwriter.writeline('    ' + originalbindata.to01())
                    for i, shiftedstring in enumerate(shiftedstrings):
                        if shiftedstring:
                            packetwriter.writeline('    %s%s (shifted by %d bits)' % (' ' * i, shiftedstring, i))
                    packetwriter.writeline('')
                
if __name__ == '__main__':
    try:
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
    except Exception as e:
        traceback.print_exc()
        time.sleep(5)
        sys.exit(-1)
