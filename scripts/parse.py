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
import csv
import io
import os
import re
import struct
from typing import TypeVar, cast, Optional, List, Union, Set, Dict, Tuple, Generator, TextIO, BinaryIO, NamedTuple

K = TypeVar('K')
V = TypeVar('V')


def merge_value_dicts(dict_list: List[Dict[K, Set[V]]]) -> Dict[K, Set[V]]:
    result_dict = dict()
    for dictionary in dict_list:
        for key, value_set in dictionary.items():
            if key not in result_dict:
                result_dict[key] = set()
                result_dict[key].update(value_set)
    return result_dict


def indentlevel2string(i: int) -> str:
    """
    :param i: the indent level
    :returns: spaces representing the given level of indent
    """
    return '  ' * i


def peek_short(infile: BinaryIO) -> int:
    """
    Get the next short (two bytes) from a stream without advancing
    """
    values = infile.read(2)
    infile.seek(-2, 1)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<H', values)[0]


def read_byte(infile: BinaryIO) -> int:
    """
    Read the next byte from a stream
    """
    return infile.read(1)[0]


def read_short(infile: BinaryIO) -> int:
    """
    Read the next short (two bytes) from a stream
    """
    values = infile.read(2)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<H', values)[0]


def read_long(infile: BinaryIO) -> int:
    """
    Read the next long (four bytes) from a stream
    """
    values = infile.read(4)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<L', values)[0]


def read_bytearray(infile: BinaryIO, length: int) -> bytes:
    """
    Read a specified number of bytes from a stream
    """
    return infile.read(length)


def read_string(infile: BinaryIO, length) -> str:
    """
    Read a specified number from bytes from a stream, interpreting them as a utf-8 string
    """
    return infile.read(length).decode('utf-8')


def bytearray2ascii(ba: bytes) -> str:
    """
    Interpret raw bytes as an ASCII string
    """
    return ''.join([chr(b) if 0x20 <= b <= 0x7F else '.' for b in ba])


def bytearray2hex(ba: bytes) -> str:
    """
    Convert raw bytes into a hex string of space-separated bytes
    """
    return ' '.join(['%02X' % b for b in ba])


def index2prefix(i: int) -> str:
    """
    Convert an array index into the appropriate prefix string for printing
    """
    return '%-3d: ' % i


def offset2string(offset: int) -> str:
    """
    Print the offset, with a ` character for easier searching
    """
    return '%08X`  ' % offset


class ParserConfigError(Exception):
    """
    An exception arising from a failure to read or process Parser configuration
    """
    pass


class ParseError(Exception):
    """
    An exception arising from a failure during parsing
    """
    pass


class Parser:
    """
    Stateful recursive-descent parser for a hexdump
    """

    def __init__(self, enumfields_files: List[str], fieldvalues_files: List[str],
                 do_annotate_fields: bool = True, do_annotate_values: bool = True) -> None:
        """
        :param enumfields_file: File containing descriptions of enum ids
        :param fieldvalues_file: File containing descriptions of enum values
        """
        def load_known_values_dict(fname: str, id_idx: int, value_idx: int) -> Dict[int, Set[str]]:
            """
            Load a mapping of value -> set of possible meanings from a file
            """
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
            """
            Load information about the enumfield types of enum ids
            """
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
                'password': set()
            }
            with open(fname, 'r') as f:
                for enumid, enumtype, _ in csv.reader(f):
                    if enumtype.lower() not in d:
                        raise ParserConfigError()
                    d[enumtype.lower()].add(int(enumid, 0))
            return d

        self.known_enum_fields = merge_value_dicts([load_known_values_dict(f, 0, 2) for f in enumfields_files])
        self.known_field_values = merge_value_dicts([load_known_values_dict(f, 0, 1) for f in fieldvalues_files])
        self.enum_ids = merge_value_dicts([load_enum_kinds_dict(f) for f in enumfields_files])

        self.do_annotate_fields = do_annotate_fields
        self.do_annotate_values = do_annotate_values

        self.infile: BinaryIO = None
        self.outfile: TextIO = None
        self.last_seen_seqnr = None

    def get_description(self, enumid: int, value: Optional[Union[str, int]]) -> str:
        """
        :param enumid: the enum id to get a description for
        :param value: the enum value to get a description for, or None to not interpret the value
        :returns: a description string about the enumfield
        """
        desc = ''
        if enumid in self.known_enum_fields:
            enum_str = '%04X' % enumid
            values_str = ', '.join(self.known_enum_fields[enumid])
            if self.do_annotate_fields:
                desc += f' (field 0x{enum_str}: {values_str})'
        if value is None:
            return desc
        try:
            possible_values = set()
            if type(value) is str:
                hex_val = int(cast(str, value), 16)
                if hex_val in self.known_field_values:
                    possible_values.update(self.known_field_values[hex_val])
                dec_val = int(cast(str, value), 10)
            else:
                dec_val = cast(int, value)
            if dec_val in self.known_field_values:
                possible_values.update(self.known_field_values[dec_val])
            if len(possible_values) > 0:
                values_str = ', '.join(possible_values)
                if self.do_annotate_values:
                    desc += f' (value {dec_val}: {values_str})'
        except ValueError:
            pass
        return desc

    def parse(self, infile: BinaryIO) -> Generator[Tuple[int, str], None, None]:
        """
        Runs the Parser on the given binary stream
        
        This is a generator, yielding the parsed data of each message in the stream

        :param infile: The binary stream to parse
        :yields: tuple of the initial offset in the stream of this message, and the parsed message contents
        """
        self.infile = infile
        try:
            packet_idx = 0
            while True:
                start_offset = self.infile.tell()
                self.outfile = io.StringIO()
                next_value = peek_short(self.infile)

                self.outfile.write('--------------------------------------------------------------------------\n')
                try:
                    enumfield = self.parse_enumfield(0, index2prefix(0))

                    # FIXME: That we have to look at the first short to see how
                    # many items are in this packet probably indicates that we
                    # interpret the packet structure incorrectly.
                    if enumfield['id'] == 0x01BC:
                        additional_items = 1
                    elif enumfield['id'] == 0x003D and any(subfield['id'] == 0x034a for subfield in enumfield['content']):
                        additional_items = 11
                    else:
                        additional_items = 0

                    for i in range(additional_items):
                        self.parse_enumfield(0, index2prefix(i + 1))
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
        """
        Parses a length-specified field from the stream as a string
        """
        length = read_short(self.infile)
        text = read_string(self.infile, length)
        self.outfile.write(f'"{text}"{self.get_description(enumid, text)}\n')

    def parse_onebyte(self, enumid: int, nesting_level: int) -> None:
        """
        Parses a one-byte field from the stream
        """
        value = read_byte(self.infile)
        self.outfile.write('%02X%s\n' % (value, self.get_description(enumid, value)))

    def parse_twobytes(self, enumid: int, nesting_level: int) -> None:
        """
        Parses a two-byte field from the stream
        """
        value = read_short(self.infile)
        self.outfile.write('%04X%s\n' % (value, self.get_description(enumid, value)))

    def parse_threebytes(self, enumid: int, nesting_level: int) -> None:
        """
        Parses a three-byte field from the stream
        """
        value = bytearray2hex(read_bytearray(self.infile, 3))
        self.outfile.write('%s%s\n' % (value, self.get_description(enumid, value)))

    def parse_fourbytes(self, enumid: int, nesting_level: int) -> None:
        """
        Parses a four-byte field from the stream
        """
        value = read_long(self.infile)
        self.outfile.write('%08X%s\n' % (value, self.get_description(enumid, value)))

    def parse_eightbytes(self, enumid: int, nesting_level: int) -> None:
        """
        Parses an eight-byte field from the stream, printing it as space-separated hex bytes
        """
        value = read_bytearray(self.infile, 8)
        self.outfile.write('%s%s\n' % (bytearray2hex(value), self.get_description(enumid, None)))

    def parse_authentication(self, enumid: int, nesting_level: int) -> None:
        """
        Parses an authentication value from the stream
        """
        size = read_long(self.infile)
        self.outfile.write(f'{size} bytes containing authentication data based on your password\n')
        read_bytearray(self.infile, size)

    def parse_salt(self, enumid: int, nesting_level: int) -> None:
        """
        Parses a salt value from the stream
        """
        salt = bytearray2hex(read_bytearray(self.infile, 16))
        self.outfile.write(f'{salt} (salt)\n')

    def parse_password(self, enumid: int, nesting_level: int) -> None:
        """
        Parses a value from the stream
        """
        length = read_short(self.infile) & 0x7FFF
        password = bytearray2hex(read_bytearray(self.infile, length * 2))
        self.outfile.write(f'{password} {self.get_description(enumid, None)}\n')

    def parse_seq_ack(self) -> None:
        """
        Parses a seq/ack from the stream
        """
        offset = self.infile.tell()
        seq = read_long(self.infile)
        if self.last_seen_seqnr and seq != self.last_seen_seqnr + 1:
            self.dump_error(offset)
            raise ParseError('Invalid sequence number %d (0x%08X) at offset 0x%08X (expected %d (0x%08X))'
                             % (seq, seq, offset, self.last_seen_seqnr, self.last_seen_seqnr))
        ack = read_long(self.infile)
        self.outfile.write(offset2string(offset) + 'seq %08X ack %08X\n' % (seq, ack))

    def parse_enumblockarray(self, enumid: int, nesting_level: int, newline: bool, prefix='') -> List:
        """
        Parses an enumfield containing an array of enumfields from the stream
        """
        offset = self.infile.tell()
        length = read_short(self.infile)
        if newline:
            self.outfile.write(offset2string(offset) + indentlevel2string(nesting_level))
        self.outfile.write(f'{prefix}enumblockarray length {length}{self.get_description(enumid, None)}\n')

        content = []
        for i in range(length):
            content.append(self.parse_enumfield(nesting_level + 1, index2prefix(i)))

        return content

    def parse_arrayofenumblockarrays(self, enumid: int, nesting_level: int) -> List:
        """
        Parses an array of enumfield arrays from the stream
        """
        size = read_short(self.infile)
        self.outfile.write(f'arrayofenumblockarrays size {size}\n')

        content = []
        for i in range(size):
            content.append(self.parse_enumblockarray(-1, nesting_level + 1, True, prefix=index2prefix(i)))
        return content

    def parse_enumfield(self, nesting_level: int, prefix='') -> Dict:
        """
        Parses any enumfield from the stream
        """
        offset = self.infile.tell()
        enumid = read_short(self.infile)
        self.outfile.write(offset2string(offset) + indentlevel2string(nesting_level) + prefix + 'enumfield %04X ' % enumid)

        enumfield = {'id': enumid, 'content': None}

        if enumid in self.enum_ids['enumblockarray'] and nesting_level == 0:
            enumfield['content'] = self.parse_enumblockarray(enumid, nesting_level + 1, False)
        elif enumid in self.enum_ids['salt']:
            self.parse_salt(enumid, nesting_level + 1)
        elif enumid in self.enum_ids['password']:
            self.parse_password(enumid, nesting_level + 1)
        elif enumid in self.enum_ids['sizedcontent'] or (nesting_level != 0 and enumid == 444):
            try:
                self.parse_sizedcontent(enumid, nesting_level + 1)
            except UnicodeDecodeError:
                offset = self.infile.tell()
                self.dump_error(offset)
                raise ParseError('Unable to decode some bytes as unicode')
        elif enumid in self.enum_ids['arrayofenumblockarrays']:
            enumfield['content'] = self.parse_arrayofenumblockarrays(enumid, nesting_level + 1)
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

        return enumfield

    def dump_error(self, offset: int) -> None:
        """
        Dump out error information from stream, listing the given offset
        """
        self.outfile.write('\n\n************\n')
        self.outfile.write('Parse error occurred at offset 0x%08X. Next bunch of bytes were:\n' % offset)
        for l in range(20):
            value = read_bytearray(self.infile, 16)
            self.outfile.write('%08X: %s  %s\n' % (offset, bytearray2hex(value), bytearray2ascii(value)))
            offset += 16


def carrays2indentandbytesperblock(hexdumpfile: TextIO) -> Generator[Tuple[bool, bytearray], None, None]:
    lastpacketnumber = {}
    collectedbytes: bytearray = []
    lastlineofpacket = False
    peer = None

    for linenum, line in enumerate(infile):
        line = line.strip()

        if not line:
            continue

        match = re.match('char peer(\d)_(\d+).* Packet .*', line)

        if match:
            peer = int(match.group(1))
            packetnumber = int(match.group(2))
            if packetnumber < lastpacketnumber.get(peer, -1):
                print('Warning: found non-increasing packet number on line %d: %s\n' % (linenum + 1, packetnumber) +
                      '\n' +
                      'This is probably caused by a known bug in Wireshark,\n' +
                      'so we\'ll just ignore this and stop reading here.\n'
                      'Everything up to this point has been converted successfully.')
                break
            lastpacketnumber[peer] = packetnumber
            continue

        lastlineofpacket = line.endswith('};')
        line = line.replace('};', '')
        line = line.rstrip(',')

        hexthisline = [int('%s' % hextext, 16) for hextext in line.split(',')]
        collectedbytes.extend(hexthisline)

        if lastlineofpacket:
            assert peer is not None
            yield (peer == 1), collectedbytes
            collectedbytes = []

def removepacketsizes(indent: bool, bytestreamin: BinaryIO) -> Tuple[List[int], BinaryIO]:
    """
    Remove the packet size information from the given bytestream

    :returns: tuple of a list of packet boundary positions in the stream, and the stream with packet sizes removed
    """
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


def payloadoffset2rawoffset(payloadoffset: int, packetboundaries: List[int]) -> int:
    """
    Convert a payload offset to the raw offset in the original stream
    """
    rawoffset = payloadoffset
    for boundary in packetboundaries:
        if payloadoffset > boundary:
            rawoffset += 2

    return rawoffset


def indentandrawoffset2globaloffset(indent: bool, rawoffset: int, offsetlist: List[Tuple[bool, int, int]]) -> int:
    """
    Get the global offset associated with the given raw offset
    """
    for i, (ind, start, end) in enumerate(offsetlist):
        if indent == ind and start <= rawoffset < end:
            return i
    raise RuntimeError('There\'s a bug in this code. This statement should not have been reached.')


class CliArguments(NamedTuple):
    file: str
    disable_id_annotations: bool
    disable_value_annotations: bool
    id_annotation_sources: List[str]
    value_annotation_sources: List[str]


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Client-Login Server Capture Parser')
    arg_parser.add_argument('file', metavar='FILE', type=str,
                            help='a wireshark capture in C-arrays format')
    arg_parser.add_argument('--disable-id-annotations', action='store_true',
                            help='disable printing annotations for enumfield ids')
    arg_parser.add_argument('--disable-value-annotations', action='store_true',
                            help='disable printing annotations for enumfield values')
    arg_parser.add_argument('--id-annotation-sources', type=str, nargs='+',
                            help='list of additional CSVs to source enumfield id annotations from')
    arg_parser.add_argument('--value-annotation-sources', type=str, nargs='+',
                            help='list of additional CSVs to source enumfield value annotations from')

    args: CliArguments = arg_parser.parse_args()

    infile_name = args.file

    with open(infile_name, 'rt') as infile:
        with open(infile_name + '_parsed.txt', 'wt') as outfile:
            offsets = {
                False: 0,
                True: 0
            }
            offset_list = []
            data = {
                False: io.BytesIO(),
                True: io.BytesIO()
            }
            for indent, hex_bytes in carrays2indentandbytesperblock(infile):
                offset_list.append((indent, offsets[indent], offsets[indent] + len(hex_bytes)))
                offsets[indent] += len(hex_bytes)
                data[indent].write(bytes(hex_bytes))

            packet_boundaries = {}
            payload_data = {}
            parsed_by_offset = {}

            id_sources_list = [os.path.join(os.path.dirname(__file__), 'known_field_data/enumfields.csv')]
            if args.id_annotation_sources:
                id_sources_list.extend(args.id_annotation_sources)
            value_sources_list = [os.path.join(os.path.dirname(__file__), 'known_field_data/fieldvalues.csv')]
            if args.value_annotation_sources:
                value_sources_list.extend(args.value_annotation_sources)
            parser = Parser(id_sources_list, value_sources_list,
                            not args.disable_id_annotations, not args.disable_value_annotations)
            for i in (False, True):
                data[i].seek(0)
                packet_boundaries[i], payload_data[i] = removepacketsizes(i, data[i])
                for payload_offset, parsed_output in parser.parse(payload_data[i]):
                    raw_offset = payloadoffset2rawoffset(payload_offset, packet_boundaries[i])
                    global_offset = indentandrawoffset2globaloffset(i, raw_offset, offset_list)
                    parsed_by_offset[(global_offset, raw_offset)] = (i, parsed_output)

            for key in sorted(parsed_by_offset.keys()):
                indent, parsed_output = parsed_by_offset[key]
                for line in parsed_output.splitlines():
                    outfile.write(('    ' if indent else '') + line + '\n')
