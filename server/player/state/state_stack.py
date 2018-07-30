#!/usr/bin/env python3
#
# Copyright (C) 2018  Maurice van der Pot <griffon26@kfk4ever.com>,
# Copyright (C) 2018 Timo Pomer <timopomer@gmail.com>
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
from player.player import Player
from player.state.player_state import PlayerState

from typing import List


class StateStack:
    def __init__(self, player: Player):
        self.stack = List[PlayerState]
        self.player = player

    def enter_state(self, state_constructor, **kwargs):
        state = state_constructor(self.player, **kwargs)
        state.on_enter()
        self.stack.append(state)

    def exit_state(self):
        state = self.stack.pop()
        state.on_exit()

    def handle_request(self, request, server):
        for state in self.stack:
            state.handle_request(request, server, inherited=True)
        self.stack[-1].handle_request(request, server, inherited=False)
