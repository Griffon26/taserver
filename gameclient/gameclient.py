#!/usr/bin/env python3

from bitarray import bitarray
import os
import socket
import string
import struct
import sys

serverip = "62.251.94.140" # kfk4ever.com
serverport = 7777

def hexdump(data):
    offset = 0
    while True:
        rowdata = data[offset:offset + 16]
        printables = set(string.printable) - set('\n\r\t')

        if not rowdata:
            break
        
        print('%08X  %-48s  %s' % (offset,
                                 ' '.join(['%02X' % b for b in rowdata]),
                                 ''.join([chr(b) if chr(b) in printables else '.' for b in rowdata ])
                                 ))
        offset += 16

def datatohex(data):
    return ''.join(['%02X' % b for b in data])

def datatoascii(data):
    printables = string.digits + string.ascii_letters + string.punctuation + ' '
    return ''.join([chr(b) if chr(b) in printables else '.' for b in data ])

def bindump(data):
    bytesonrow = 16
    offset = 0
    while True:
        rowdata = data[offset:offset + bytesonrow]

        if not rowdata:
            break

        bits = bitarray(endian='little')
        bits.frombytes(rowdata)
        print('%08X  %-*s ' % (offset, bytesonrow * 8, bits.to01()), end = '')
        extendedbits = bitarray(bits)
        extendedbits.extend('00000000')
        for i in range(8):
            shiftedbytes = extendedbits[i:bytesonrow * 8 + i].tobytes()
            print('%-*s ' % (bytesonrow * 2, datatohex(shiftedbytes)), end = '')
            print('%-*s ' % (bytesonrow, datatoascii(shiftedbytes)), end = '')
        print()
        
        offset += bytesonrow

def bindump2(data):
    bindump_binaryonly(data)
    for i in range(8):
        print()
        bindump_hex_withshift(data, i)

def bindump_binaryonly(data):
    bytesonrow = 16
    offset = 0
    while True:
        rowdata = data[offset:offset + bytesonrow]

        if not rowdata:
            break

        bits = bitarray(endian='little')
        bits.frombytes(rowdata)
        print('%08X  %-*s ' % (offset, bytesonrow * 8, bits.to01()), end = '')
        print()
        
        offset += bytesonrow

def bindump_hex_withshift(data, shift):
    bytesonrow = 16
    offset = 0
    while True:
        rowdata = data[offset:offset + bytesonrow]

        if not rowdata:
            break

        bits = bitarray(endian='little')
        bits.frombytes(rowdata)
        extendedbits = bitarray(bits)
        extendedbits.extend('00000000')
        i = shift
        shiftedbytes = extendedbits[i:bytesonrow * 8 + i].tobytes()
        print('%-*s ' % (bytesonrow * 2, datatohex(shiftedbytes)), end = '')
        print('%-*s ' % (bytesonrow, datatoascii(shiftedbytes)), end = '')
        print()
        
        offset += bytesonrow


def hexparse(hexstring):
    return bytes([int('0x' + hexbyte, base = 16) for hexbyte in hexstring.split()])

def parsehexdump(hexdumptext):
    hexbytes = bytes()
    
    for line in hexdumptext.splitlines():
        line = line.strip()

        if not line:
            continue

        offsettext, rest = line.split('  ', maxsplit=1)
        hexpart, asciipart = rest.split('   ', maxsplit=1)

        hexbytes += bytes(int(hextext, 16) for hextext in hexpart.split())
        
    return hexbytes        

def bindumptofile(data, f):
    bits = bitarray(endian='little')
    bits.frombytes(data)
    f.write('%05d  %s\n' % (len(data), bits.to01()))
    f.flush()

def main():
    packets = []
    packetindex = 0
    try:
        while True:
            with open('data/packet%d.hexdump' % packetindex, 'rt') as f:
                content = parsehexdump(f.read())
                packets.append(content)
                packetindex += 1
    except FileNotFoundError:
        # No more packet files to read
        pass

    with open('data/packetack.hexdump', 'rt') as f:
        packetack = parsehexdump(f.read())

    try:
        with open('clientpackets.bindump', 'wt') as clientoutfile:
            with open('serverpackets.bindump', 'wt') as serveroutfile:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                protocol = [
                    ('send', 0),
                    ('send', 1),
                        ('wait', 0),
                    ('send', 2),
                    ('send', 3),
                    ('send', 4),
                    ('send', 5),
                    ('send', 6),
                    ('send', 7),
                    ('send', 8),
                        ('wait', 1),
                    ('send', 9),
                    # The next packets are optional. The server
                    # will already start sending game updates.
                    ('send', 10),
                    ('send', 11),
                        ('wait', 30),
                    ('send', 12),
                    ('send', 13),
                    ('send', 14)
                ]

                print('Starting initial packet exchange...')
                for action, seq in protocol:
                    if action == 'send':
                        print('  Sending recorded packet %d...' % seq)
                        sock.sendto(packets[seq], (serverip, serverport))
                        bindumptofile(packets[seq], clientoutfile)
                    else:
                        print('  Waiting for at least seqnr %d...' % seq)
                        while True:
                            data, addr = sock.recvfrom(4096)
                            # cut off seqnr
                            bindumptofile(data, serveroutfile)
                            receivedseq = struct.unpack('<H', data[0:2])[0] & 0x3FFF
                            print('    received %d bytes with seqnr %d' % (len(data), receivedseq))
                            if receivedseq >= seq:
                                break

                print('Initial packet exchange finished; keeping the server talking...')
                while True:
                    data, addr = sock.recvfrom(4096)
                    bindumptofile(data, serveroutfile)
                    receivedseq = struct.unpack('<H', data[0:2])[0] & 0x3FFF
                    print("  received %d bytes with seqnr %d" % (len(data), receivedseq))

                    seq += 1
                    newvalue = (seq | (1 << 14) | (receivedseq << 15))
                    oldvalue = struct.unpack('<L', data[0:4])[0] & 0xE000000
                    newseqack = struct.pack('<L', newvalue | oldvalue)

                    packettosend = newseqack + packetack[4:]
                    sock.sendto(packettosend, (serverip, serverport))
                    bindumptofile(packettosend, clientoutfile)
                
    except KeyboardInterrupt:
        print('Interrupted by CTRL-C')
        sock.close()

if __name__ == '__main__':
    main()
