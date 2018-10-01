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
import json
import logging

from .tcpmessage import TcpMessageWriter

server_address = ("127.0.0.1", 9801)


def _send_command(command):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(server_address)
            TcpMessageWriter(sock).send(json.dumps(command).encode('utf8'))

    except ConnectionRefusedError:
        logger = logging.getLogger(__name__)
        logger.warning('\n'
                       '--------------------------------------------------------------\n'
                       'Warning: Failed to connect to taserver firewall for modifying \n'
                       'the firewall rules.\n'
                       'Did you forget to run start_taserver_firewall.py (as admin)?\n'
                       '--------------------------------------------------------------')


def reset_firewall(list_type):
    command = {
        'list' : list_type,
        'action' : 'reset'
    }
    _send_command(command)


def modify_firewall(list_type, action, ip):
    command = {
        'list' : list_type,
        'action' : action,
        'ip' : ip
    }
    _send_command(command)

