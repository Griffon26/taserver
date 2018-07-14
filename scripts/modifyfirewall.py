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
from gevent import socket
import struct

serveraddress = ("127.0.0.1", 9801)

def main(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(serveraddress)

        listtype = b'w' if args.listtype == 'whitelist' else b'b'
        action = b'a' if args.action == 'add' else b'r'
        ipparts = bytes(int(ippart) for ippart in args.ip.split('.'))

        data = listtype + action + ipparts
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
    parser.add_argument('listtype',
                        type=str,
                        choices=['blacklist', 'whitelist'],
                        help='Which list to modify')
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
