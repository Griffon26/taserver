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

class HexDumper():
    def __init__(self, dumpqueue):
        self.dumpqueue = dumpqueue
        self.clientoffset = 0
        self.serveroffset = 0

    def run(self):
        with open(dumpfilename, 'wt') as dumpfile:
            while True:
                source, packetbytes = self.dumpqueue.get()
                indent = '    ' if source == 'server' else ''
                bytelist = [ '%02X' % b for b in packetbytes ]

                if source == 'server':
                    overalloffset = self.serveroffset
                else:
                    overalloffset = self.clientoffset
                
                hexblockoffset = 0
                while len(bytelist) > hexblockoffset + 16:
                    dumpfile.write('%s%08X  %-47s   .\n' % (indent,
                                                            overalloffset + hexblockoffset,
                                                            ' '.join(bytelist[hexblockoffset:hexblockoffset + 16])))
                    hexblockoffset += 16
                dumpfile.write('%s%08X  %-47s   .\n' % (indent,
                                                        overalloffset + hexblockoffset,
                                                        ' '.join(bytelist[hexblockoffset:])))
                hexblockoffset += len(bytelist[hexblockoffset:])
                overalloffset += hexblockoffset
                
                if source == 'server':
                    self.serveroffset = overalloffset
                else:
                    self.clientoffset = overalloffset
                
                dumpfile.flush()
