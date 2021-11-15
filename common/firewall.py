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
from ipaddress import IPv4Address
import json
import logging
import struct

from .tcpmessage import TcpMessageWriter


class FirewallClient:
    def __init__(self, ports, shared_config):
        self.ports = ports
        # don't try to send commands to udpproxy if its not running
        self.use_udpproxy = not shared_config.getboolean('use_iptables', False)

    def _send_command(self, command):
        server_address = ("127.0.0.1", self.ports['firewall'])
        proxy_addresses = (("127.0.0.1", self.ports['gameserver1firewall']),
                           ("127.0.0.1", self.ports['gameserver2firewall']))
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(server_address)
                TcpMessageWriter(sock).send(json.dumps(command).encode('utf8'))

            if self.use_udpproxy:
                if command['list'] == 'whitelist':
                    for proxy_address in proxy_addresses:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                            sock.connect(proxy_address)
                            if command['action'] == 'reset':
                                message = b'reset'
                            else:
                                address = IPv4Address(command['ip'])
                                action = b'a' if command['action'] == 'add' else b'r'
                                message = action + struct.pack('<L', command['player_id']) + address.packed
                            sock.sendall(struct.pack('<L', len(message)))
                            sock.sendall(message)
                            sock.shutdown(socket.SHUT_RDWR)

        except ConnectionRefusedError:
            logger = logging.getLogger(__name__)
            logger.warning('\n'
                        '--------------------------------------------------------------\n'
                        'Warning: Failed to connect to taserver firewall for modifying \n'
                        'the firewall rules.\n'
                        'Did you forget to run start_taserver_firewall.py (as admin)?\n'
                        'If you want to run without the firewall and udpproxy you will need\n'
                        'to change the gameserver port to 7777 in gameserverlauncher.ini.\n'
                        '--------------------------------------------------------------')

    def reset_firewall(self, list_type):
        command = {
            'list' : list_type,
            'action' : 'reset'
        }
        self._send_command(command)

    def modify_firewall(self, list_type, action, player_id, ip):
        command = {
            'list' : list_type,
            'action' : action,
            'player_id' : player_id,
            'ip' : str(ip)
        }
        self._send_command(command)
