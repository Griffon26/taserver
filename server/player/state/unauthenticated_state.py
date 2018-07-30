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
from firewall import modify_gameserver_whitelist, modify_loginserver_blacklist
from player.state.player_state import PlayerState

from datatypes import *


class UnauthenticatedState(PlayerState):
    def handle_request(self, request, server, inherited):
        def send(data, client_id=None):
            player = server.players[client_id] if client_id is not None else self.player
            player.send(data, server)

        if isinstance(request, a01bc):
            send(a01bc())
            send(a0197())

        elif isinstance(request, a003a):
            if request.findbytype(m0056) is None:  # request for login
                send(a003a())

            else:  # actual login
                self.player.login_name = request.findbytype(m0494).value
                self.player.password_hash = request.findbytype(m0056).content

                if (self.player.login_name in server.accounts and
                        self.player.password_hash == server.accounts[self.player.login_name].password_hash):
                    self.player.authenticated = True

                name_prefix = '' if self.player.authenticated else 'unverif-'
                self.player.display_name = name_prefix + self.player.login_name
                send([
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
        elif isinstance(request, a0033):
            send(a0033())
