#!/usr/bin/env python3
#
# Copyright (C) 2018-2019  Maurice van der Pot <griffon26@kfk4ever.com>
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

import json

FRIEND_STATE_VISIBLE = 0x00000001
FRIEND_STATE_ONLINE = 0x00001000
FRIEND_STATE_IN_GAME = 0x00002000


class Friends:
    def __init__(self, this_player):
        self.this_player = this_player
        self.friends_dict = {}
        self.social_network = None

    def connect_to_social_network(self, social_network):
        self.social_network = social_network

    def add(self, unique_id, login_name):
        if unique_id not in self.friends_dict:
            self.friends_dict[unique_id] = {'login_name': login_name}
            self.social_network.add_friend(self.this_player.unique_id, unique_id)
            return True
        else:
            return False

    def remove(self, unique_id):
        if unique_id in self.friends_dict:
            self.friends_dict.pop(unique_id, None)
            self.social_network.remove_friend(self.this_player.unique_id, unique_id)
            return True
        else:
            return False

    def load(self, filename):
        try:
            with open(filename, 'rt') as infile:
                friend_dict_with_string_keys = json.load(infile)
                self.friends_dict = {int(k): v for k, v in friend_dict_with_string_keys.items()}
        except OSError:
            self.friends_dict = {}

    def save(self, filename):
        with open(filename, 'wt') as outfile:
            json.dump(self.friends_dict, outfile, indent=4, sort_keys=True)

    def notify_online(self):
        if self.this_player.verified:
            self.social_network.notify_online(self.this_player,
                                              {k: v['login_name'] for k, v in self.friends_dict.items()})

    def notify_on_game_server(self):
        if self.this_player.verified:
            self.social_network.notify_on_game_server(self.this_player)

    def notify_offline(self):
        if self.this_player.verified:
            self.social_network.notify_offline(self.this_player)
