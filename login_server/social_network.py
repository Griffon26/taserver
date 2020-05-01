#!/usr/bin/env python3
#
# Copyright (C) 2019  Maurice van der Pot <griffon26@kfk4ever.com>
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

SOCIAL_BITMASK_NOBODY    = 0x00000000
SOCIAL_BITMASK_FRIEND    = 0x00000001
SOCIAL_BITMASK_FOLLOWER  = 0x00010000

SOCIAL_BITMASK_OFFLINE   = 0x00000000
SOCIAL_BITMASK_IN_LOBBY  = 0x00001000
SOCIAL_BITMASK_IN_GAME   = 0x00003000

import collections

from common.datatypes import *


class SocialNetwork:

    def __init__(self):
        self.players = {}
        self.player_names = {}
        self.player_states = collections.defaultdict(lambda: SOCIAL_BITMASK_OFFLINE)
        self.player_friends = collections.defaultdict(set)

    def add_friend(self, player_id, friend_id):
        self.player_friends[player_id].add(friend_id)
        self._notify_specific_player(friend_id, player_id)
        self._notify_specific_player(player_id, friend_id)

    def remove_friend(self, player_id, friend_id):
        self.player_friends[player_id].remove(friend_id)
        self._notify_specific_player(friend_id, player_id)
        self._notify_specific_player(player_id, friend_id)

    def notify_online(self, player, friends):
        assert player.verified

        self.players[player.unique_id] = player
        self.player_states[player.unique_id] = SOCIAL_BITMASK_IN_LOBBY
        self.player_names[player.unique_id] = player.login_name
        self.player_names.update(friends)
        self.player_friends[player.unique_id] = set(friends.keys())

        self._notify_followers_and_friends(player.unique_id, vice_versa=True)

    def notify_on_game_server(self, player):
        self.player_states[player.unique_id] = SOCIAL_BITMASK_IN_GAME
        self._notify_followers_and_friends(player.unique_id)

    def notify_offline(self, player):
        self.player_states[player.unique_id] = SOCIAL_BITMASK_OFFLINE
        self._notify_followers_and_friends(player.unique_id)
        del self.players[player.unique_id]

    def _get_friends(self, player_id):
        return self.player_friends[player_id]

    def _get_followers(self, selected_player_id):
        return {player_id for player_id, friends in
                self.player_friends.items() if selected_player_id in friends}

    def _get_notification_type(self, sender_id, receiver_id):
        notification_type = self.player_states[sender_id]
        if receiver_id in self.player_friends[sender_id]:
            notification_type |= SOCIAL_BITMASK_FOLLOWER
        if sender_id in self.player_friends[receiver_id]:
            notification_type |= SOCIAL_BITMASK_FRIEND
        return notification_type

    def _notify_followers_and_friends(self, selected_player_id, vice_versa=False):
        followers = self._get_followers(selected_player_id)
        friends = self._get_friends(selected_player_id)

        for other_player_id in followers | friends:
            self._notify_specific_player(selected_player_id, other_player_id)
            if vice_versa:
                self._notify_specific_player(other_player_id, selected_player_id)

    def _notify_specific_player(self, sender_id, receiver_id):
        if receiver_id in self.players:
            notification_type = self._get_notification_type(sender_id, receiver_id)

            msg = a011b().set([
                m034a().set(self.player_names[sender_id]),
                m020d().set(sender_id),
                m0296(),
                m0591().set(notification_type)
            ])
            self.players[receiver_id].send(msg)

    def send_friend_list(self, player_id):
        followers = self._get_followers(player_id)
        friends = self._get_friends(player_id)

        friend_list = []
        for other_player_id in followers | friends:
            friend_list.append([
                m034a().set(self.player_names[other_player_id]),
                m020d().set(other_player_id),
                m0296(),
                m0591().set(self._get_notification_type(other_player_id, player_id)),
                m0307()])

        msg = a011c().set([
            m0348().set(player_id),
            m0116().set(friend_list)
        ])

        self.players[player_id].send(msg)
