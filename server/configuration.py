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
import configparser
from os import path

from server_configuration import ServerConfiguration

SERVERS_INI_PATH = path.join("configurations", "servers.ini")


class Configuration:
    def __init__(self):
        self.server_config = ServerConfiguration.from_configuration(self.read_config(file_name=SERVERS_INI_PATH))

    @classmethod
    def read_config(cls, file_name: str):
        parser = configparser.ConfigParser()
        parser.read(file_name)
        return parser._sections
