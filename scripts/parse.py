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

from typing import cast, Optional, Union, List, Set, Dict, Tuple, Generator, TextIO, BinaryIO

import csv
import io
import os
import struct
import sys
import time

class ParseError(Exception):
    pass


def indentlevel2string(i):
    return '  ' * i


def peek_short(infile: BinaryIO) -> int:
    values = infile.read(2)
    infile.seek(-2, 1)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<H', values)[0]


def read_byte(infile: BinaryIO) -> int:
    return infile.read(1)[0]


def read_short(infile: BinaryIO) -> int:
    values = infile.read(2)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<H', values)[0]


def read_long(infile: BinaryIO) -> int:
    values = infile.read(4)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<L', values)[0]


def read_bytearray(infile: BinaryIO, length) -> bytes:
    return infile.read(length)


def read_string(infile: BinaryIO, length) -> str:
    return infile.read(length).decode('utf-8')


def bytearray2ascii(ba: bytes) -> str:
    return ''.join([chr(b) if 0x20 <= b <= 0x7F else '.' for b in ba])


def bytearray2hex(ba: bytes) -> str:
    return ' '.join(['%02X' % b for b in ba])


def index2prefix(i: int) -> str:
    return '%-3d: ' % i


def offset2string(offset: int) -> str:
    ''' Put a ` character after the offset to facilitate text searches '''
    return '%08X`  ' % offset


def desc2suffix(desc):
    return ' (%s)' % desc if desc else ''


class ParserConfigError(Exception):
    pass


class Parser():
    def __init__(self, enumfields_file: str, fieldvalues_file: str) -> None:
        def load_known_values_dict(fname: str, id_idx: int, value_idx: int) -> Dict[int, Set[str]]:
            d: Dict[int, Set[str]] = dict()
            with open(fname, 'r') as f:
                r = csv.reader(f)
                for row in r:
                    if not row[value_idx].strip():
                        # No defined value
                        continue
                    val = int(row[id_idx], 0)
                    if val not in d:
                        d[val] = set()
                    d[val].add(row[value_idx])
            return d

        def load_enum_kinds_dict(fname: str) -> Dict[str, Set[int]]:
            d: Dict[str, Set[int]] = {
                'onebyte': set(),
                'twobytes': set(),
                'threebytes': set(),
                'fourbytes': set(),
                'eightbytes': set(),
                'sizedcontent': set(),
                'enumblockarray': set(),
                'arrayofenumblockarrays': set(),
                'authentication': set(),
                'salt': set(),
            }
            with open(fname, 'r') as f:
                r = csv.reader(f)
                for row in r:
                    if row[1].lower() not in d:
                        raise ParserConfigError()
                    d[row[1].lower()].add(int(row[0], 0))
            return d

        self.known_enum_fields = load_known_values_dict(enumfields_file, 0, 2)
        self.known_field_values = load_known_values_dict(fieldvalues_file, 0, 1)
        self.enum_ids = load_enum_kinds_dict(enumfields_file)

        self.infile: BinaryIO = None
        self.outfile: TextIO = None
        self.last_seen_seqnr = None

    def get_description(self, enumid: int, value: Optional[Union[str, int]]) -> str:
        desc = ''
        if enumid in self.known_enum_fields:
            enumStr = '%04X' % enumid
            valuesStr = ', '.join(self.known_enum_fields[enumid])
            desc += f' (field 0x{enumStr}: {valuesStr})'
        if value is None:
            return desc
        try:
            possible_values = set()
            if type(value) is str:
                hexVal = int(cast(str, value), 16)
                if hexVal in self.known_field_values:
                    possible_values.update(self.known_field_values[hexVal])
                decVal = int(cast(str, value), 10)
            else:
                decVal = cast(int, value)
            if decVal in self.known_field_values:
                possible_values.update(self.known_field_values[decVal])
            if len(possible_values) > 0:
                valuesStr = ', '.join(possible_values)
                desc += f' (value {decVal}: {valuesStr})'
        except ValueError:
            pass
        return desc

    def parse(self, infile: BinaryIO) -> Generator[Tuple[int, str], None, None]:
        self.infile = infile
        try:
            packet_idx = 0
            while True:
                start_offset = self.infile.tell()
                self.outfile = io.StringIO()
                next_value = peek_short(self.infile)

                # FIXME: That we have to look at the first short to see how 
                # many items are in this packet probably indicates that we 
                # interpret the packet structure incorrectly.
                if next_value == 0x01BC:
                    item_count = 2
                elif next_value == 0x003D:
                    item_count = 12
                else:
                    item_count = 1

                self.outfile.write('--------------------------------------------------------------------------\n')
                try:
                    for i in range(item_count):
                        self.parse_enumfield(0, index2prefix(i))
                    self.parse_seq_ack()

                except ParseError as e:
                    self.outfile.write(str(e))
                    break
                finally:
                    self.outfile.seek(0)
                    yield start_offset, self.outfile.read()

                packet_idx += 1
        except EOFError:
            pass

    def parse_sizedcontent(self, enumid: int, nesting_level: int) -> None:
        length = read_short(self.infile)
        text = read_string(self.infile, length)
        self.outfile.write(f'"{text}"{self.get_description(enumid, text)}\n')

    def parse_onebyte(self, enumid: int, nesting_level: int) -> None:
        value = read_byte(self.infile)
        self.outfile.write('%02X%s\n' % (value, self.get_description(enumid, value)))

    def parse_twobytes(self, enumid: int, nesting_level: int) -> None:
        value = read_short(self.infile)
        self.outfile.write('%04X%s\n' % (value, self.get_description(enumid, value)))

    def parse_threebytes(self, enumid: int, nesting_level: int) -> None:
        value = bytearray2hex(read_bytearray(self.infile, 3))
        self.outfile.write('%s%s\n' % (value, self.get_description(enumid, value)))

    def parse_fourbytes(self, enumid, nesting_level):
        value = read_long(self.infile)
        self.outfile.write('%08X%s\n' % (value, self.get_description(enumid, value)))

    def parse_eightbytes(self, enumid: int, nesting_level: int) -> None:
        value = read_bytearray(self.infile, 8)
        self.outfile.write('%s%s\n' % (bytearray2hex(value), self.get_description(enumid, -1)))

    def parse_authentication(self, enumid: int, nesting_level: int) -> None:
        size = read_long(self.infile)
        self.outfile.write(f'{size} bytes containing authentication data based on your password\n')
        read_bytearray(self.infile, size)

    def parse_salt(self, enumid: int, nesting_level: int) -> None:
        salt = bytearray2hex(read_bytearray(self.infile, 16))
        self.outfile.write(f'{salt} (salt)\n')

    def parse_seq_ack(self) -> None:
        offset = self.infile.tell()
        seq = read_long(self.infile)
        if self.last_seen_seqnr and seq != self.last_seen_seqnr + 1:
            self.dump_error(offset)
            raise ParseError('Invalid sequence number %d (0x%08X) at offset 0x%08X (expected %d (0x%08X))'
                             % (seq, seq, offset, self.last_seen_seqnr, self.last_seen_seqnr))
        ack = read_long(self.infile)
        self.outfile.write(offset2string(offset) + 'seq %08X ack %08X\n' % (seq, ack))

    def parse_enumblockarray(self, enumid: int, nesting_level: int, newline: bool, prefix='') -> None:
        offset = self.infile.tell()
        length = read_short(self.infile)
        if newline:
            self.outfile.write(offset2string(offset) + indentlevel2string(nesting_level))
        self.outfile.write(f'{prefix}enumblockarray length {length}{self.get_description(enumid, None)}\n')
        for i in range(length):
            self.parse_enumfield(nesting_level + 1, index2prefix(i))

    def parse_arrayofenumblockarrays(self, enumid: int, nesting_level: int) -> None:
        size = read_short(self.infile)
        self.outfile.write(f'arrayofenumblockarrays size {size}\n')
        for i in range(size):
            self.parse_enumblockarray(-1, nesting_level + 1, True, prefix=index2prefix(i))

    def parse_enumfield(self, nesting_level: int, prefix='') -> None:
        offset = self.infile.tell()
        enumid = read_short(self.infile)
        self.outfile.write(offset2string(offset) + indentlevel2string(nesting_level) + prefix + 'enumfield %04X ' % enumid)

        if enumid in self.enum_ids['enumblockarray'] and nesting_level == 0:
            self.parse_enumblockarray(enumid, nesting_level + 1, False)
        elif enumid in self.enum_ids['salt']:
            self.parse_salt(enumid, nesting_level + 1)
        elif enumid in self.enum_ids['sizedcontent'] or (nesting_level != 0 and enumid == 444):
            try:
                self.parse_sizedcontent(enumid, nesting_level + 1)
            except UnicodeDecodeError:
                offset = self.infile.tell()
                self.dump_error(offset)
                raise ParseError('Unable to decode some bytes as unicode')
        elif enumid in self.enum_ids['arrayofenumblockarrays']:
            self.parse_arrayofenumblockarrays(enumid, nesting_level + 1)
        elif enumid in self.enum_ids['onebyte']:
            self.parse_onebyte(enumid, nesting_level + 1)
        elif enumid in self.enum_ids['twobytes']:
            self.parse_twobytes(enumid, nesting_level + 1)
        elif enumid in self.enum_ids['threebytes']:
            self.parse_threebytes(enumid, nesting_level + 1)
        elif enumid in self.enum_ids['fourbytes']:
            self.parse_fourbytes(enumid, nesting_level + 1)
        elif enumid in self.enum_ids['eightbytes']:
            self.parse_eightbytes(enumid, nesting_level + 1)
        elif enumid in self.enum_ids['authentication']:
            self.parse_authentication(enumid, nesting_level + 1)
        else:
            offset = self.infile.tell()
            self.dump_error(offset)
            raise ParseError('Unknown enumtype %d (0x%04X) at offset 0x%08X' % (enumid, enumid, offset))

    def dump_error(self, offset: int) -> None:
        self.outfile.write('\n\n************\n')
        self.outfile.write('Parse error occurred at offset 0x%08X. Next bunch of bytes were:\n' % offset)
        for l in range(20):
            value = read_bytearray(self.infile, 16)
            self.outfile.write('%08X: %s  %s\n' % (offset, bytearray2hex(value), bytearray2ascii(value)))
            offset += 16


def hexdump2indentandbytesperline(hexdumpfile):
    lastoffset = {
        False: -1,
        True: -1
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
                False: 0,
                True: 0
            }
            offsetlist = []
            data = {
                False: io.BytesIO(),
                True: io.BytesIO()
            }
            for indent, hexbytes in hexdump2indentandbytesperblock(infile):
                offsetlist.append((indent, offsets[indent], offsets[indent] + len(hexbytes)))
                offsets[indent] += len(hexbytes)
                data[indent].write(bytes(hexbytes))

            packetboundaries = {}
            payloaddata = {}
            parsedbyoffset = {}
            parser = Parser('known_field_data/enumfields.csv', 'known_field_data/fieldvalues.csv')
            for i in (False, True):
                data[i].seek(0)
                packetboundaries[i], payloaddata[i] = removepacketsizes(i, data[i])
                for payloadoffset, parsedoutput in parser.parse(payloaddata[i]):
                    rawoffset = payloadoffset2rawoffset(payloadoffset, packetboundaries[i])
                    globaloffset = indentandrawoffset2globaloffset(i, rawoffset, offsetlist)
                    parsedbyoffset[(globaloffset, rawoffset)] = (i, parsedoutput)

            for key in sorted(parsedbyoffset.keys()):
                indent, parsedoutput = parsedbyoffset[key]
                for line in parsedoutput.splitlines():
                    outfile.write(('    ' if indent else '') + line + '\n')



