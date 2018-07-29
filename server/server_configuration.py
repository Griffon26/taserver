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
import socket
from ipaddress import IPv4Address

from server_info import ServerInfo


class ServerConfiguration:
    def __init__(self, servers):
        self.servers = servers

    def __iter__(self):
        return self.servers.iter()

    @classmethod
    def from_configuration(cls, configuration: dict):
        servers = []
        for first_id, key in enumerate(configuration):
            server_config = configuration[key]
            second_id = 2 ** 31 + first_id
            description = server_config["description"]
            motd = server_config["motd"]
            ip = IPv4Address(socket.gethostbyname(server_config["ip"]))
            port = int(server_config["port"])

            server = ServerInfo(first_id, second_id, description, motd, ip, port)
            servers.append(server)
        return ServerConfiguration(servers)
