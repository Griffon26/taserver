#!/usr/bin/env python3

import bitarray
import socket
from udk import *

serverip = "62.251.94.140" # kfk4ever.com
serverport = 7777

class SeqnrGenerator():
    def __init__(self):
        self.seqnr = 0

    def get(self):
        temp = self.seqnr
        self.seqnr += 1
        return temp

class DumpingSocket():
    def __init__(self, sock):
        self.sock = sock
        self.serverdumpfile = open('serverpackets2.bindump', 'wt')
        self.clientdumpfile = open('clientpackets2.bindump', 'wt')

    def close(self):
        self.serverdumpfile.close()
        self.clientdumpfile.close()
        self.sock.close()

    def sendto(self, data, addr):
        bits = bitarray(endian = 'little')
        bits.frombytes(data)
        self.clientdumpfile.write('%d  %s\n' % (len(data), bits.to01()))
        return self.sock.sendto(data, addr)

    def recvfrom(self, size):
        data, addr = self.sock.recvfrom(size)
        bits = bitarray(endian = 'little')
        bits.frombytes(data)
        self.serverdumpfile.write('%d  %s\n' % (len(data), bits.to01()))
        return data, addr

def main():

    unacknowledged = []
    seqnrgen = SeqnrGenerator()

    parser = Parser()
    sock = DumpingSocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))

    packet = Packet()
    packet.seqnr = seqnrgen.get()
    packetdata = PacketData()
    packetdata.unknownbits11 = True
    packetdata.channel_data = ChannelData()
    packetdata.channel_data.channel = 0
    packetdata.channel_data.counter = 1
    packetdata.channel_data.unknownbits = bitarray('00000100')
    payload = PayloadData()
    payload.object_class = ObjectClass()
    payload.object_class.classid = 0x1B7E0110
    payload.instance = ObjectInstance()
    property_ = ObjectProperty()
    property_.propertyid = 0
    payload.instance.properties.append(property_)
    payload.bitsleft = bitarray('000000000000100010011110000000000000000000')
    packetdata.channel_data.payload = payload
    packet.parts.append(packetdata)

    print('Sent:')
    print(packet.tostring())
    sock.sendto(packet.tobitarray().tobytes(), (serverip, serverport))
    
    packet = Packet()
    packet.seqnr = seqnrgen.get()
    packetdata = PacketData()
    packetdata.channel_data = ChannelData()
    packetdata.channel_data.channel = 0
    packetdata.channel_data.counter = 2
    packetdata.channel_data.unknownbits = bitarray('00000100')
    payload = PayloadData()
    payload.instance = ObjectInstance()
    property_ = ObjectProperty()
    property_.propertyid = 18
    payload.instance.properties.append(property_)
    payload.bitsleft = bitarray('0000000000100000001001111000000000000000000000000001001100000011001110110010001100111011001100110000001100000011001100110000001100000011000000110001001100000011001110110010001100111011001100110000001100000011001100110000001100000011000000110001001100000011001110110010001100111011001100110000001100000011001100110000001100000011000000110001001100000011001110110010001100111011001100110000001100000011001100110000001100000011000000110000001100000011001110110010001100101011001100110010001100110011000010110000001100000011000000110000001100000011001110110010001100101011001100110010001100110011000010110000001100000011000000110000001100000011001110110010001100101011001100110010001100110011000010110000001100000011000000110000001100000011001110110010001100101011001100110010001100110011000010110000001100000011000000110010001100110011001100110010001100010011001110110001001100100011001000110000001100100111001010110010001100101011001100110000001100110011001010110000001100000011000000110000001100000011000000110000000000')
    packetdata.channel_data.payload = payload
    packet.parts.append(packetdata)

    print('Sent:')
    print(packet.tostring())
    sock.sendto(packet.tobitarray().tobytes(), (serverip, serverport))

    packet = Packet()
    packet.seqnr = seqnrgen.get()
    packetdata = PacketData()
    packetdata.channel_data = ChannelData()
    packetdata.channel_data.channel = 0
    packetdata.channel_data.counter = 3
    packetdata.channel_data.unknownbits = bitarray('00000100')
    payload = PayloadData()
    payload.instance = ObjectInstance()
    property_ = ObjectProperty()
    property_.propertyid = 0
    payload.instance.properties.append(property_)
    payload.bitsleft = bitarray('00100000000111111011011000000000000000000000100010011110000000000000000000')
    packetdata.channel_data.payload = payload
    packet.parts.append(packetdata)

    print('Sent:')
    print(packet.tostring())
    sock.sendto(packet.tobitarray().tobytes(), (serverip, serverport))

    data, addr = sock.recvfrom(4096)
    bits = bitarray(endian = 'little')
    bits.frombytes(data)
    serverpacket = parser.parsepacket(bits)
    print('Received from %s:%s:' % addr)
    print('%s\n' % packet.tostring())

    packet = Packet()
    packet.seqnr = seqnrgen.get()
    packetack = PacketAck()
    packetack.acknr = serverpacket.seqnr
    packet.parts.append(packetack)
    packetdata = PacketData()
    packetdata.channel_data = ChannelData()
    packetdata.channel_data.channel = 0
    packetdata.channel_data.counter = 4
    packetdata.channel_data.unknownbits = bitarray('00000100')
    payload = PayloadData()
    payload.instance = ObjectInstance()
    property_ = ObjectProperty()
    property_.propertyid = 4
    payload.instance.properties.append(property_)
    payload.bitsleft = bitarray('0000001000111001000000000000000000101000000100000000000000000000000000000000001100000000000001101000000000000000000000000001011100100111001000110010001100110011001111010000101010010011101001011001000110101001101100111010110010100001101001011001110110101000100111011000101110010011101001111011111100111000101000011010110110101001101100101000101110100001100010111010100110101111001111001011100010110010101111101001110010111101101100101010100110110011101100111010010110111101100111011011111100111000101000011010110110101001101011001011110110001001101010011010111100000011001111110001110010100001101011011010100110101111001101101000001110001101100001110010000100101110100000010011100010010011101001011001100110011001101111011001110110010011000110110011111100001010101010011010000110101101101011110001001100101011001010110000000000')
    packetdata.channel_data.payload = payload
    packet.parts.append(packetdata)

    print('Sent:')
    print(packet.tostring())
    sock.sendto(packet.tobitarray().tobytes(), (serverip, serverport))

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            bits = bitarray(endian = 'little')
            bits.frombytes(data)
            serverpacket = parser.parsepacket(bits)
            print('Received from %s:%s:' % addr)
            print('%s\n' % packet.tostring())
            unacknowledged.append(serverpacket.seqnr)

            clientpacket = Packet()
            clientpacket.seqnr = seqnrgen.get()
            for serverseqnr in unacknowledged:
                packetack = PacketAck()
                packetack.acknr = serverpacket.seqnr
                clientpacket.parts.append(packetack)
                unacknowledged = []
            print('Sending:')
            print('%s\n' % clientpacket.tostring())
            sock.sendto(packet.tobitarray().tobytes(), (serverip, serverport))
                
    except KeyboardInterrupt:
        print('Interrupted by CTRL-C')
        sock.close()

if __name__ == '__main__':
    main()
