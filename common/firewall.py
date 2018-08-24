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

from gevent import socket

server_address = ("127.0.0.1", 9801)


def modify_firewall(list_type, action, ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(server_address)

        list_type = b'w' if list_type == 'whitelist' else b'b'
        action = b'a' if action == 'add' else b'r'
        ip_parts = bytes(int(ip_part) for ip_part in ip.split('.'))

        data = list_type + action + ip_parts
        sock.sendall(data)
        sock.close()

    except ConnectionRefusedError:
        print('-------------------------------------------------------------\n'
              'Warning: Failed to connect to taserverfirewall for modifying \n'
              'the firewall rules.\n'
              'Did you forget to start taserverfirewall.py?\n'
              '-------------------------------------------------------------')
