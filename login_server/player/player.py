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

import logging
from typing import Dict
import os

from ipaddress import IPv4Address

from .friends import Friends
from .loadouts import Loadouts
from .settings import PlayerSettings
from common.connectionhandler import Peer
from common.ipaddresspair import IPAddressPair
from common.statetracer import statetracer, RefOnly
from common.game_items import get_game_setting_modes, UNMODDED_GAME_SETTING_MODE


@statetracer('unique_id', 'login_name', 'display_name', 'address_pair', 'player_settings', 'port', 'verified',
             RefOnly('game_server'), 'vote', 'team')
class Player(Peer):

    min_name_length = 2
    max_name_length = 15
    idle_timeout = 60

    def __init__(self, address, data_root):
        super().__init__()

        self.logger = logging.getLogger(__name__)
        self.unique_id: int = None
        self.login_name: str = None
        self.display_name: str = None
        self.password_hash: str = None
        self.port = address[1]
        self.verified = False
        self.last_received_seq = 0
        self.vote = None
        self.state = None
        self.is_modded: bool = False
        self.login_server = None
        self.game_server = None
        self.loadouts: Dict[Loadouts] = {mode: Loadouts(mode) for mode in get_game_setting_modes()}
        self.friends = Friends(self)
        self.player_settings = PlayerSettings()
        self.team = None
        self.pings = {}
        self.activity_since_last_check = True

        self.loadout_file_path = os.path.join(data_root, 'players', '%s_%s_loadouts.json' )
        self.friends_file_path = os.path.join(data_root, 'players', '%s_friends.json' )
        self.settings_file_path = os.path.join(data_root, 'players', '%s_settings.json' )

        detected_ip = IPv4Address(address[0])
        if detected_ip.is_global:
            self.address_pair = IPAddressPair(detected_ip, None)
        else:
            assert detected_ip.is_private
            self.address_pair = IPAddressPair(None, detected_ip)

    def start_idle_timeout(self):
        if not self.activity_since_last_check:
            self.logger.info('Disconnecting %s after a period of %s seconds without network activity' %
                             (self, self.idle_timeout))
            self.disconnect()
        else:
            self.activity_since_last_check = False
            self.login_server.pending_callbacks.add(self, self.idle_timeout, self.start_idle_timeout)

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

        self.state = state_class(self, *args, **kwargs)
        self.state.on_enter()

    def get_unmodded_loadouts(self) -> Loadouts:
        return self.loadouts[UNMODDED_GAME_SETTING_MODE]

    def get_current_loadouts(self) -> Loadouts:
        effective_mode = self.player_settings.game_setting_mode if self.is_modded else UNMODDED_GAME_SETTING_MODE
        return self.loadouts[effective_mode]

    def get_loadout_modded_defs(self):
        return self.get_current_loadouts().get_loadout_modded_defs()

    def load(self):
        if self.verified:
            for mode in get_game_setting_modes():
                self.loadouts[mode].load(self.loadout_file_path % (self.login_name, mode))
            self.friends.load(self.friends_file_path % self.login_name)
            self.player_settings.load(self.settings_file_path % self.login_name)

    def save(self):
        if self.verified:
            for mode in get_game_setting_modes():
                self.loadouts[mode].save(self.loadout_file_path % (self.login_name, mode))
            self.friends.save(self.friends_file_path % self.login_name)
            self.player_settings.save(self.settings_file_path % self.login_name)

    def handle_request(self, request):
        return self.state.handle_request(request)

    def send(self, data):
        super().send((data, self.last_received_seq))

    def __repr__(self):
        return '%s(%s, %s:%s, %d:"%s")' % (self.task_name, self.task_id,
                                           self.address_pair, self.port,
                                           self.unique_id, self.display_name)
