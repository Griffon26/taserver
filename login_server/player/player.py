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

from .friends import Friends
from .loadouts import Loadouts
from common.connectionhandler import Peer


class Player(Peer):

    loadout_file_path = 'data/players/%s_loadouts.json'
    friends_file_path = 'data/players/%s_friends.json'

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
        self.friends = Friends()
        self.team = None
        self.pings = {}

    def set_state(self, state_class, *args, **kwargs):
        assert self.unique_id is not None
        assert self.login_server is not None

        if self.state:
            self.state.on_exit()

        if state_class:
            self.state = state_class(self, *args, **kwargs)
            self.state.on_enter()

    def load(self):
        if self.registered:
            self.loadouts.load(self.loadout_file_path % self.login_name)
            self.friends.load(self.friends_file_path % self.login_name)

    def save(self):
        if self.registered:
            self.loadouts.save(self.loadout_file_path % self.login_name)
            self.friends.save(self.friends_file_path % self.login_name)

    def handle_request(self, request):
        self.state.handle_request(request)

    def send(self, data):
        super().send((data, self.last_received_seq))

    def __repr__(self):
        return '%s(%s, %s:%s, 0x%08X:"%s")' % (self.task_name, self.task_id,
                                               self.ip, self.port, self.unique_id, self.display_name)
