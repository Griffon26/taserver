#!/usr/bin/env python3
#
# Copyright (C) 2021  Maurice van der Pot <griffon26@kfk4ever.com>
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
import unittest
import unittest.mock as mock

from login_server.gameserver import GameServer


class TestGameServer(GameServer):
    def __init__(self):
        super().__init__(IPv4Address('127.0.0.1'), ports=None, shared_config=None)

    def send(self, msg):
        self.msg = msg

    def __repr__(self):
        return str(__class__)


class GameServerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.gameserver = TestGameServer()
        self.gameserver.next_map_idx = 3
        self.gameserver.votable_maps = [1, 2, 3, 4, 5]

    def test_process_map_votes__map_with_most_votes_is_selected(self):
        self.gameserver.map_votes = {'person1': 1, 'person2': 2, 'person3': 3, 'person4': 2}
        self.gameserver.process_map_votes()
        self.assertEqual(self.gameserver.msg.map_id, 2)

    def test_process_map_votes__outcome_with_equal_votes_is_determined_randomly(self):
        self.gameserver.map_votes = {'person1': 1, 'person2': 2, 'person3': 3}

        with mock.patch('random.choice', lambda options: options[0]) as m:
            self.gameserver.process_map_votes()
            map_with_most_votes1 = self.gameserver.msg.map_id

        with mock.patch('random.choice', lambda options: options[1]) as m:
            self.gameserver.process_map_votes()
            map_with_most_votes2 = self.gameserver.msg.map_id

        self.assertNotEqual(map_with_most_votes1, map_with_most_votes2)

    def test_process_map_votes__with_no_votes_map_is_next_one(self):
        self.gameserver.next_map_idx = 2
        self.gameserver.map_votes = {}
        self.gameserver.process_map_votes()
        self.assertEqual(self.gameserver.msg.map_id, 2)
