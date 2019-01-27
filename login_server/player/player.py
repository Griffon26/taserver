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

from ipaddress import IPv4Address

from .friends import Friends
from .loadouts import Loadouts
from common.connectionhandler import Peer
from common.ipaddresspair import IPAddressPair
from common.statetracer import statetracer, RefOnly


@statetracer('unique_id', 'login_name', 'display_name', 'tag', 'address_pair', 'port', 'registered',
             RefOnly('game_server'), 'vote', 'team')
class Player(Peer):

    max_name_length = 15

    loadout_file_path = 'data/players/%s_loadouts.json'
    friends_file_path = 'data/players/%s_friends.json'

    def __init__(self, address, use_goty_mode: bool):
        super().__init__()

        self.use_goty_mode = use_goty_mode

        self.unique_id = None
        self.login_name = None
        self.display_name = None
        self.password_hash = None
        self.tag = ''
        self.port = address[1]
        self.registered = False
        self.last_received_seq = 0
        self.vote = None
        self.state = None
        self.is_modded = False
        self.login_server = None
        self.game_server = None
        self.loadouts = Loadouts(use_goty_mode)
        self.friends = Friends()
        self.team = None
        self.pings = {}

        detected_ip = IPv4Address(address[0])
        if detected_ip.is_global:
            self.address_pair = IPAddressPair(detected_ip, None)
        else:
            assert detected_ip.is_private
            self.address_pair = IPAddressPair(None, detected_ip)

    def complement_address_pair(self, login_server_address_pair):
        # Take over login server external address in case login server and player
        # are on the same LAN
        if not self.address_pair.external_ip and login_server_address_pair.external_ip:
            assert(self.address_pair.internal_ip)
            self.address_pair.external_ip = login_server_address_pair.external_ip

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
        return '%s(%s, %s:%s, %d:"%s")' % (self.task_name, self.task_id,
                                           self.address_pair, self.port,
                                           self.unique_id, self.display_name)
