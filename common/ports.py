#!/usr/bin/env python3
#
# Copyright (C) 2020  Maurice van der Pot <griffon26@kfk4ever.com>
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


class Ports:

    fixed_ports = {
        'client2login': 9000,  # TCP
        'launcher2login': 9001,  # TCP
        'restapi': 9080,  # TCP
        'authchannel': 9800 # TCP
    }

    variable_ports = {
        'gameserver1': 7777,     # UDP
        'gameserver2': 7778,     # UDP
        # gameserverNproxy    = gameserverN + 100   # UDP
        # gameserverNfirewall = gameserverN + 200   # TCP
        'game2launcher': 9002,   # TCP
        'launcherping': 9002,    # UDP
        'firewall': 9801,        # TCP
    }

    def __init__(self, portOffset):
        assert isinstance(portOffset, int), f'portOffset must be int, not {portOffset.__class__.__name__}'
        self.portOffset = portOffset

    def __getitem__(self, key):
        if key in self.fixed_ports:
            return self.fixed_ports[key]
        elif key in self.variable_ports:
            return self.variable_ports[key] + self.portOffset
        elif key.endswith('proxy') and key[:-5] in self.variable_ports:
            return self.variable_ports[key[:-5]] + 100 + self.portOffset
        elif key.endswith('firewall') and key[:-8] in self.variable_ports:
            return self.variable_ports[key[:-8]] + 200 + self.portOffset
        else:
            raise KeyError(f'{key} is not a valid port descriptor.')
