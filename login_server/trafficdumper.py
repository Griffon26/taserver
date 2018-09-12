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

dumpfilename = 'taserverdump.carrays'


class TrafficDumper:
    def __init__(self, dump_queue):
        self.dump_queue = dump_queue
        self.overall_seqnr = 0
        self.client_seqnr = 0
        self.server_seqnr = 0

    def run(self):
        with open(dumpfilename, 'wt') as dump_file:
            while True:
                source, packet_bytes = self.dump_queue.get()
                peer_id = 1 if source == 'tcpwriter' else 0
                byte_list = ['0x%02X' % b for b in packet_bytes]

                if source == 'tcpwriter':
                    peer_seqnr = self.server_seqnr
                else:
                    peer_seqnr = self.client_seqnr

                dump_file.write('char peer%d_%d[] = { /* Packet %d */\n' % (peer_id, peer_seqnr, self.overall_seqnr))
                while len(byte_list) > 8:
                    dump_file.write(', '.join(byte_list[:8]) + ',\n')
                    byte_list = byte_list[8:]
                dump_file.write(', '.join(byte_list) + ' };\n')

                if source == 'tcpwriter':
                    self.server_seqnr += 1
                else:
                    self.client_seqnr += 1
                self.overall_seqnr += 1

                dump_file.flush()
