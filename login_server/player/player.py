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

from .loadouts import Loadouts
from common.connectionhandler import Peer

TEAM_BLOODEAGLE = 0
TEAM_DIAMONDSWORD = 1
TEAM_SPEC = 255

class Player(Peer):
    def __init__(self, address):
        super().__init__()
        self.unique_id = None
        self.login_name = None
        self.display_name = None
        self.password_hash = None
        self.tag = ''
        self.ip = address[0]
        self.port = address[1]
        self.game_server = None
        self.registered = False
        self.last_received_seq = 0
        self.vote = None
        self.state = None
        self.login_server = None
        self.game_server = None
        self.loadouts = Loadouts()
        self.team = None

    def set_state(self, state_class, *args, **kwargs):
        assert(self.unique_id is not None)
        assert(self.login_server is not None)

        if self.state:
            self.state.on_exit()
        self.state = state_class(self, *args, **kwargs)
        self.state.on_enter()

    def handle_request(self, request):
        self.state.handle_request(request)

    def send(self, data):
        super().send((data, self.last_received_seq))

    def __repr__(self):
        return '%s(%s, %s:%s, 0x%08X:"%s")' % (self.task_name, self.task_id,
                                               self.ip, self.port, self.unique_id, self.display_name)
