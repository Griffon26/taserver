#!/usr/bin/env python3

import argparse
from gevent import socket
import struct

serveraddress = ("127.0.0.1", 9801)

def main(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(serveraddress)

        action = b'a' if args.action == 'add' else b'r'
        ipparts = bytes(int(ippart) for ippart in args.ip.split('.'))

        data = action + ipparts
        sock.send(data)
        sock.close()

        print('Sent data', data)
        return 0
    
    except ConnectionRefusedError:
        print('-------------------------------------------------------------\n'
              'Warning: Failed to connect to taserverfirewall for modifying \n'
              'the firewall rules on the game server.\n'
              'Did you forget to start taserverfirewall.py there?\n'
              '-------------------------------------------------------------')
        return -1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',
                        type=str,
                        choices=['add', 'remove'],
                        help='Whether to add or remove the IP address to/from the list')
    parser.add_argument('ip',
                        type=str,
                        help='an IP address')
    args = parser.parse_args()

    retcode = main(args)

    exit(retcode)
