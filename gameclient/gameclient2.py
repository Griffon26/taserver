#!/usr/bin/env python3

import bitarray
import socket
from udk import *

serverip = "62.251.94.140" # kfk4ever.com
serverport = 7777

def main():

    seqnr = 0

    parser = Parser()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    packet = Packet(seqnr)
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


            clientpacket = Packet(seqnr)
            packetack = PacketAck()
            packetack.acknr = serverpacket.seqnr
            clientpacket.parts.append(packetack)

            seqnr += 1
            print('Sending:')
            print('%s\n' % clientpacket.tostring())
            sock.sendto(packet.tobitarray().tobytes(), (serverip, serverport))
                
    except KeyboardInterrupt:
        print('Interrupted by CTRL-C')
        sock.close()

if __name__ == '__main__':
    main()
