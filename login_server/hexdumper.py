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

dumpfilename = 'taserverdump.hexdump'


class HexDumper:
    def __init__(self, dump_queue):
        self.dump_queue = dump_queue
        self.client_offset = 0
        self.server_offset = 0

    def run(self):
        with open(dumpfilename, 'wt') as dump_file:
            while True:
                source, packet_bytes = self.dump_queue.get()
                indent = '    ' if source == 'tcpwriter' else ''
                byte_list = ['%02X' % b for b in packet_bytes]

                if source == 'tcpwriter':
                    overall_offset = self.server_offset
                else:
                    overall_offset = self.client_offset

                hex_block_offset = 0
                while len(byte_list) > hex_block_offset + 16:
                    dump_file.write('%s%08X  %-47s   .\n' % (indent,
                                                             overall_offset + hex_block_offset,
                                                             ' '.join(
                                                                 byte_list[hex_block_offset:hex_block_offset + 16])))
                    hex_block_offset += 16
                dump_file.write('%s%08X  %-47s   .\n' % (indent,
                                                         overall_offset + hex_block_offset,
                                                         ' '.join(byte_list[hex_block_offset:])))
                hex_block_offset += len(byte_list[hex_block_offset:])
                overall_offset += hex_block_offset

                if source == 'tcpwriter':
                    self.server_offset = overall_offset
                else:
                    self.client_offset = overall_offset

                dump_file.flush()
