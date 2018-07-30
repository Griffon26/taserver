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
from player.state.state_stack import StateStack


class Player:
    def __init__(self, id, ip, port):
        self.id = id
        self.login_name = None
        self.display_name = None
        self.password_hash = None
        self.tag = ''
        self.ip = ip
        self.port = port
        self.game_server = None
        self.authenticated = False
        self.last_received_seq = 0
        self.vote = None
        self.state = StateStack(self)

    def enter_state(self, state_constructor, **kwargs):
        self.state.enter_state(state_constructor, **kwargs)

    def exit_state(self):
        self.state.exit_state()

    def send(self, data, server):
        server.client_queues[self.id].put((data, self.last_received_seq))

    def __repr__(self):
        return '%s, %s:%s, "%s"' % (self.id, self.ip, self.port, self.display_name)
