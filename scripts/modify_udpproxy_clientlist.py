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
from ipaddress import ip_address
import socket
import struct

proxy_address = ("127.0.0.1", 9802)


def main(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(proxy_address)
        action = b'a' if args.action == 'add' else b'r'
        message = action + struct.pack('<L', args.playerID) + args.IPaddress.packed
        sock.sendall(struct.pack('<L', len(message)))
        sock.sendall(message)
        sock.shutdown(socket.SHUT_RDWR)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Helper utility for testing the udpproxy')
    arg_parser.add_argument('action', choices = ['add', 'remove'],
                            help='the action to perform')
    arg_parser.add_argument('playerID', type=int,
                            help='the ID of the player that is being added/removed')
    arg_parser.add_argument('IPaddress', type=ip_address,
                            help='the address to add to or remove from the list of allowed clients')

    main(arg_parser.parse_args())
