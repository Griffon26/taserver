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

from .authenticated_state import AuthenticatedState
from ..state.player_state import PlayerState, handles
from ...datatypes import *


class UnauthenticatedState(PlayerState):
    @handles(packet=a01bc)
    def handle_a01bc(self, request):
        self.player.send(a01bc())
        self.player.send(a0197())

    @handles(packet=a0033)
    def handle_a0033(self, request):
        self.player.send(a0033())

    @handles(packet=a003a)
    def handle_login_request(self, request):
        if request.findbytype(m0056) is None:  # request for login
            self.player.send(a003a())

        else:  # actual login
            self.player.login_name = request.findbytype(m0494).value
            self.player.password_hash = request.findbytype(m0056).content
            if (self.player.login_name in self.player.login_server.accounts and
                self.player.password_hash == self.player.login_server.accounts[self.player.login_name].password_hash):

                self.player.authenticated = True

            name_prefix = '' if self.player.authenticated else 'unverif-'
            self.player.display_name = name_prefix + self.player.login_name
            self.player.send([
                a003d().setplayer(self.player.display_name, ''),
                m0662(0x8898, 0xdaff),
                m0633(),
                m063e(),
                m067e(),
                m0442(),
                m02fc(),
                m0219(),
                m0019(),
                m0623(),
                m05d6(),
                m00ba()
            ])
            self.player.set_state(AuthenticatedState)
