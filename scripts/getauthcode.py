#!/usr/bin/env python3

import argparse
from gevent import socket
import struct

serveraddress = ("127.0.0.1", 9800)

def main(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    data = struct.pack('<H', len(args.username)) + \
            args.username.encode('latin1')
    sock.sendto(data, serveraddress)
    
    addr = None
    while addr != serveraddress:
        data, addr = sock.recvfrom(4096)
    authcodelen = struct.unpack('<H', data[0:2])[0]
    authcode = data[2:2+authcodelen].decode('latin1')

    print('Received authcode %s for username %s' % (authcode, args.username))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username',
                        type=str,
                        help='username for which to request an authentication code')
    args = parser.parse_args()
    main(args)
