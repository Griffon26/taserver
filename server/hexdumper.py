#!/usr/bin/env python3

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
