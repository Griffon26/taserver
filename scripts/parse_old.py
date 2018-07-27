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

import io
import os
import struct
import sys
import time

last_seen_seqnr = None

class ParseError(Exception):
    pass

def indentlevel2string(i):
    return '  ' * i

def peekshort(infile):
    values = infile.read(2)
    infile.seek(-2, 1)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<H', values)[0]

def readbyte(infile):
    return infile.read(1)[0]

def readshort(infile):
    values = infile.read(2)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<H', values)[0]

def readlong(infile):
    values = infile.read(4)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<L', values)[0]

def readbytearray(infile, length):
    return infile.read(length)

def readstring(infile, length):
    return infile.read(length).decode('utf-8')

def bytearray2ascii(ba):
    return ''.join([chr(b) if 0x20 <= b <= 0x7F else '.' for b in ba])

def bytearray2hex(ba):
    return ' '.join(['%02X' % b for b in ba])

def index2prefix(i):
    return '%-3d: ' % i

def offset2string(offset):
    ''' Put a ` character after the offset to facilitate text searches '''
    return '%08X`  ' % offset

def desc2suffix(desc):
    return ' (%s)' % desc if desc else ''

def enum2desc(enumid):
    knownenums = {
        0x0014 : 'class menu content',
        0x0070 : 'chat message',
        0x009e : 'message type (2=public, 3=team, 6=private)',
        0x00b1 : 'server join step 1',
        0x00b2 : 'server join step 2',
        0x00b3 : 'server disconnect',
        0x00ec : '"/report" command',
        0x011b : 'player online/join notification',
        0x0175 : 'promotion code',
        0x018c : '"/votekick" command',
        0x01a4 : 'motd/report text',
        0x01b5 : 'watch now menu content',
        0x021a : 'game mode',
        0x0246 : 'two bytes unknown + port + IP (9002 server)',
        0x024f : 'two bytes unknown + port + IP (game server)',
        0x026f : 'purchase name',
        0x0296 : 'player rank (unused)',
        0x02b1 : 'internal map name',
        0x02b2 : 'map id',
        0x02b6 : 'map name',
        0x02c4 : 'match id?',
        0x02c7 : 'server id',
        0x02e6 : 'message text',
        0x02fc : 'std message id',
        0x02fe : 'sender name',
        0x0300 : 'map+gamemode, server or region name',
        0x0348 : 'player id',
        0x034a : 'player name',
        0x0448 : 'region id',
        0x0452 : 'team id',
        0x0494 : 'login name',
        0x049e : 'version number',
        0x04cb : 'player xp',
        0x053d : 'ping time',
        0x0592 : 'player vote',
        0x05d3 : 'player gold',
        0x05dc : 'player rank progress',
        0x0669 : 'promotion code',
        0x06de : 'clan tag',
        0x0704 : 'player id to kick',
        0x0705 : 'player name to kick'
    }
    return knownenums[enumid] if enumid in knownenums else None

def dumperror(infile, outfile, offset):
    outfile.write('\n\n************\n')
    outfile.write('Parse error occurred at offset 0x%08X. Next bunch of bytes were:\n' % offset)
    for l in range(20):
        value = readbytearray(infile, 16)
        outfile.write('%08X: %s  %s\n' % (offset, bytearray2hex(value), bytearray2ascii(value)))
        offset += 16

toplevelids_enumblockarray = (20, 51, 53, 58, 61, 65, 76, 109, 111, 112,
                              133, 176, 177, 178, 179, 180, 213, 236,
                              251, 284, 283, 325, 373, 374, 375, 386,
                              387, 395, 396, 407, 437, 444, 454, 456)

enumids_salt = (995,)
enumids_sizedcontent = (19, 130, 162, 163, 170, 171, 420, 422, 444, 452,
                        524, 538, 609, 623, 687, 689, 694, 742, 766, 768,
                        842, 859, 892, 1079, 1118, 1128, 1172, 1595, 1641,
                        1720, 1758, 1769, 1797)
enumids_arrayofenumblockarrays = (233, 254, 278, 290, 295, 306, 312, 324, 1483, 1586, 1587,
                                  1598, 1634, 1662, 1665, 1675, 1723, 1775)
enumids_onebyte = (111, 506, 713, 806, 1090, 1131, 1396, 1426, 1494, 1510, 1537,
                   1596, 1651, 1691, 1692, 1795)
enumids_twobytes = (775, 1341, 1536)
enumids_threebytes = (110,)
enumids_fourbytes = (25, 53, 109,
                     115, 139, 141, 149, 157, 158, 186, 191, 195, 198, 212, 407,
                     419, 448, 449, 457, 483, 488, 523, 525, 537, 539, 543, 549,
                     552, 578, 595, 601, 602, 604, 605, 606, 607, 611, 621, 626,
                     627, 662, 664, 665, 675, 683, 684, 690, 691, 693, 695, 702,
                     708, 711, 726, 727, 728, 732, 748, 749, 751, 756, 764, 767, 793,
                     817, 819, 835, 836, 837, 838, 839, 840, 858, 867, 873, 875,
                     876, 895, 896, 901, 920, 932, 948, 974, 992, 1009, 1013, 1021, 1050, 1066, 1067,
                     1070, 1071, 1096, 1106, 1111, 1112, 1138, 1161, 1182, 1189, 1190,
                     1191, 1192, 1193, 1194, 1211, 1227, 1233, 1237, 1241, 1274,
                     1282, 1366, 1368, 1386, 1399, 1405, 1407, 1418, 1425, 1430,
                     1431, 1464, 1484, 1487, 1491, 1500, 1513, 1518, 1538, 1544,
                     1546, 1548, 1557, 1565,
                     1571, 1581, 1582, 1583, 1590, 1591, 1592, 1593, 1594, 1597,
                     1631, 1632, 1633, 1635, 1636, 1642, 1649, 1650, 1652, 1653,
                     1654, 1655, 1663, 1664, 1667, 1668, 1676, 1689, 1719, 1721, 1722,
                     1725, 1727, 1728, 1737, 1770, 1774, 1777, 1781, 1786, 1793, 1796)
enumids_eightbytes = (8, 183, 471, 501, 582, 591, 771, 1049, 1076, 1236, 1406, 1506, 1508)
enumids_authentication = (86,)

def parsesalt(infile, outfile, nestinglevel):
    salt = bytearray2hex(readbytearray(infile, 16))
    outfile.write(salt + ' (salt)\n')

def parsesizedcontent(infile, outfile, nestinglevel, desc):
    length = readshort(infile)
    text = readstring(infile, length)
    outfile.write('"%s"%s\n' % (text, desc2suffix(desc)))

def parsearrayofenumblockarrays(infile, outfile, nestinglevel):
    size = readshort(infile)
    outfile.write('arrayofenumblockarrays size %d\n' % size)
    for i in range(size):
        parseenumblockarray(infile, outfile, nestinglevel + 1, True, prefix=index2prefix(i))

def parseonebyte(infile, outfile, nestinglevel, desc):
    value = readbyte(infile)
    outfile.write('%02X%s\n' % (value, desc2suffix(desc)))
    
def parsetwobytes(infile, outfile, nestinglevel, desc):
    value = readshort(infile)
    outfile.write('%04X%s\n' % (value, desc2suffix(desc)))

def parsethreebytes(infile, outfile, nestinglevel, desc):
    value = bytearray2hex(readbytearray(infile, 3))
    outfile.write('%s%s\n' % (value, desc2suffix(desc)))

def parsefourbytes(infile, outfile, nestinglevel, desc):
    value = readlong(infile)
    outfile.write('%08X%s\n' % (value, desc2suffix(desc)))

def parseeightbytes(infile, outfile, nestinglevel, desc):
    value = bytearray2hex(readbytearray(infile, 8))
    outfile.write('%s%s\n' % (value, desc2suffix(desc)))

def parseauthenticationbytes(infile, outfile, nestinglevel):
    size = readlong(infile)
    outfile.write('%d bytes containing authentication data based on your password\n' % size)
    readbytearray(infile, size)

def parseenumfield(infile, outfile, nestinglevel, prefix = ''):
    offset = infile.tell()
    enumid = readshort(infile)
    outfile.write(offset2string(offset) + indentlevel2string(nestinglevel) + prefix + 'enumfield %04X ' % enumid)

    if enumid in toplevelids_enumblockarray and nestinglevel == 0:
        parseenumblockarray(infile, outfile, nestinglevel + 1, False, desc=enum2desc(enumid))
        
    elif enumid in enumids_salt:
        parsesalt(infile, outfile, nestinglevel + 1)
    elif enumid in enumids_sizedcontent or (nestinglevel != 0 and enumid == 444):
        try:
            parsesizedcontent(infile, outfile, nestinglevel + 1, enum2desc(enumid))
        except UnicodeDecodeError:
            offset = infile.tell()
            dumperror(infile, outfile, offset)
            raise ParseError('Unable to decode some bytes as unicode')
    elif enumid in enumids_arrayofenumblockarrays:
        parsearrayofenumblockarrays(infile, outfile, nestinglevel + 1)
    elif enumid in enumids_onebyte:
        parseonebyte(infile, outfile, nestinglevel + 1, enum2desc(enumid))
    elif enumid in enumids_twobytes:
        parsetwobytes(infile, outfile, nestinglevel + 1, enum2desc(enumid))
    elif enumid in enumids_threebytes:
        parsethreebytes(infile, outfile, nestinglevel + 1, enum2desc(enumid))
    elif enumid in enumids_fourbytes:
        parsefourbytes(infile, outfile, nestinglevel + 1, enum2desc(enumid))
    elif enumid in enumids_eightbytes:
        parseeightbytes(infile, outfile, nestinglevel + 1, enum2desc(enumid))
    elif enumid in enumids_authentication:
        parseauthenticationbytes(infile, outfile, nestinglevel + 1)
    else:
        offset = infile.tell()
        dumperror(infile, outfile, offset)
        raise ParseError('Unknown enumtype %d (0x%04X) at offset 0x%08X' % (enumid, enumid, offset))

def parseenumblockarray(infile, outfile, nestinglevel, newline, prefix='', desc=''):
    offset = infile.tell()
    length = readshort(infile)
    if newline:
        outfile.write(offset2string(offset) + indentlevel2string(nestinglevel))
    outfile.write(prefix + 'enumblockarray length %d%s\n' % (length, desc2suffix(desc)))
    for i in range(length):
        parseenumfield(infile, outfile, nestinglevel + 1, index2prefix(i))

def parseseqack(infile, outfile):
    offset = infile.tell()
    seq = readlong(infile)
    if last_seen_seqnr and seq != last_seen_seqnr + 1:
        dumperror(infile, outfile, offset)
        raise ParseError('Invalid sequence number %d (0x%08X) at offset 0x%08X (expected %d (0x%08X))' % (seq, seq, offset, last_seen_seqnr, last_seen_seqnr))
    ack = readlong(infile)
    outfile.write(offset2string(offset) + 'seq %08X ack %08X\n' % (seq, ack))

def parse(infile):
    try:
        packetidx = 0
        while True:
            startoffset = infile.tell()
            outfile = io.StringIO()
            nextvalue = peekshort(infile)

            # FIXME: That we have to look at the first short to see how 
            # many items are in this packet probably indicates that we 
            # interpret the packet structure incorrectly.
            if nextvalue == 0x01BC:
                itemcount = 2
            elif nextvalue == 0x003D:
                itemcount = 12
            else:
                itemcount = 1

            outfile.write('--------------------------------------------------------------------------\n')
            try:
                for i in range(itemcount):
                    parseenumfield(infile, outfile, 0, index2prefix(i))
                parseseqack(infile, outfile)

            except ParseError as e:
                outfile.write(str(e))
                break
            finally:
                outfile.seek(0)
                yield startoffset, outfile.read()
            
            packetidx += 1
    except EOFError:
        pass

def hexdump2indentandbytesperline(hexdumpfile):
    lastoffset = {
        False : -1,
        True : -1
    }
    for linenum, line in enumerate(hexdumpfile):
        indent = line.startswith('   ')
        line = line.strip()
        
        if not line:
            continue
        
        offsettext, rest = line.split('  ', maxsplit=1)
        hexpart, asciipart = rest.split('   ', maxsplit=1)

        lineoffset = int(offsettext, 16)
        if lineoffset > lastoffset[indent]:
            lastoffset[indent] = lineoffset
        else:
            print('Warning: found non-increasing offset on line %d: %s\n' % (linenum + 1, offsettext) +
                  '\n' +
                  'This is probably caused by a known bug in Wireshark,\n' +
                  'so we\'ll just ignore this and stop parsing here.\n'
                  'Everything up to this point has been parsed successfully.')
            break

        hexline = [int('0x%s' % hextext, 16) for hextext in hexpart.split()]

        yield indent, hexline

def hexdump2indentandbytesperblock(hexdumpfile):
    lastindent = None
    collectedbytes = []
    for indent, hexline in hexdump2indentandbytesperline(hexdumpfile):

        if lastindent is None:
            lastindent = indent
        
        if indent != lastindent:
            yield lastindent, collectedbytes
            collectedbytes = []
            lastindent = indent

        collectedbytes.extend(hexline)

    if collectedbytes:
        yield indent, collectedbytes

def removepacketsizes(indent, bytestreamin):
    packetboundaries = []
    bytestreamout = io.BytesIO()

    rawoffset = 0
    offset = 0
    while True:
        packetsizebytes = bytestreamin.read(2)
        rawoffset += 2
        if len(packetsizebytes) == 0:
            break
        packetboundaries.append(offset)
        packetsize = struct.unpack('<H', packetsizebytes)[0]
        if packetsize == 0:
            packetsize = 1450
        packetbodybytes = bytestreamin.read(packetsize)
        bytestreamout.write(packetbodybytes)
        if len(packetbodybytes) != packetsize:
            raise ParseError('The number of bytes available in the file (%d) is not equal ' % len(packetbodybytes) +
                             'to the number of bytes expected (%d) starting at offset ' % packetsize +
                             '0x%08X in the %s datastream' % (rawoffset, "indented" if indent else "not indented"))
        offset += packetsize
        rawoffset += packetsize
    
    bytestreamout.seek(0)
    return packetboundaries, bytestreamout

def payloadoffset2rawoffset(payloadoffset, packetboundaries):
    rawoffset = payloadoffset
    for boundary in packetboundaries:
        if payloadoffset > boundary:
            rawoffset += 2

    return rawoffset

def indentandrawoffset2globaloffset(indent, rawoffset, offsetlist):
    for i, (ind, start, end) in enumerate(offsetlist):
        if indent == ind and start <= rawoffset < end:
            return i
    raise RuntimeError('There\'s a bug in this code. This statement should not have been reached.')

if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print('Usage: %s <captureddatahexdump>' % sys.argv[0])
        print('')
        print('This program will parse a wireshark hexdump of communication')
        print('between the TA client and the login server (port 9000) and')
        print('dump it into a text file')
        exit(0)

    infilename = sys.argv[1]

    with open(infilename, 'rt') as infile:
        with open(infilename + '_parsed.txt', 'wt') as outfile:
            offsets = {
                False : 0,
                True : 0
            }
            offsetlist = []
            data = {
                False : io.BytesIO(),
                True : io.BytesIO()
            }
            for indent, hexbytes in hexdump2indentandbytesperblock(infile):
                offsetlist.append( (indent, offsets[indent], offsets[indent] + len(hexbytes)) )
                offsets[indent] += len(hexbytes)
                data[indent].write(bytes(hexbytes))

            packetboundaries = {}
            payloaddata = {}
            parsedbyoffset = {}
            for i in (False, True):
                data[i].seek(0)
                packetboundaries[i], payloaddata[i] = removepacketsizes(i, data[i])
                for payloadoffset, parsedoutput in parse(payloaddata[i]):
                    rawoffset = payloadoffset2rawoffset(payloadoffset, packetboundaries[i])
                    globaloffset = indentandrawoffset2globaloffset(i, rawoffset, offsetlist)
                    parsedbyoffset[(globaloffset, rawoffset)] = (i, parsedoutput)

            for key in sorted(parsedbyoffset.keys()):
                indent, parsedoutput = parsedbyoffset[key]
                for line in parsedoutput.splitlines():
                    outfile.write(('    ' if indent else '') + line + '\n')



