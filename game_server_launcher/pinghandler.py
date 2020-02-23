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

import gevent
from gevent.server import DatagramServer

from common.errors import PortInUseError


class EchoServer(DatagramServer):
    def handle(self, data, address):
        self.socket.sendto(data, address)


def handle_ping(ports):
    gevent.getcurrent().name = 'pinghandler'
    address = '0.0.0.0'
    port = ports['launcherping']
    try:
        EchoServer('%s:%d' % (address, port)).serve_forever()
    except OSError as e:
        if e.errno == 10048:
            raise PortInUseError('udp', address, port)
        else:
            raise
