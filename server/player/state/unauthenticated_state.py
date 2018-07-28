#!/usr/bin/env python3
#
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
    def handle_request(self, request, server):
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

                self.player.display_name = (
                                               '' if self.player.authenticated else 'unverif-') + self.player.login_name
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

        elif isinstance(request, a00d5):
            if request.findbytype(m0228).value == 1:
                send(originalfragment(0x1EEB3, 0x20A10))  # 00d5 (map list)
            else:
                send(a00d5().setservers(server.game_servers))  # 00d5 (server list)

        elif isinstance(request, a0014):
            send(originalfragment(0x20A18, 0x20B3F))  # 0014 (class list)

        elif isinstance(request, a018b):
            send(originalfragment(0x20B47, 0x20B4B))  # 018b

        elif isinstance(request, a01b5):
            send(originalfragment(0x20B53, 0x218F7))  # 01b5 (watch now)

        elif isinstance(request, a0176):
            send(originalfragment(0x218FF, 0x219D1))  # 0176
            send(originalfragment(0x28AC9, 0x2F4D7))  # 0177 (store 0218)

        elif isinstance(request, a00b1):  # server join step 1
            serverid1 = request.findbytype(m02c7).value
            game_server = server.find_server_by_id1(serverid1)
            serverid2 = game_server.serverid2
            send(a00b0().setlength(9).setserverid1(serverid1))
            send(a00b4().setserverid2(serverid2))

        elif isinstance(request, a00b2):  # server join step 2
            serverid2 = request.findbytype(m02c4).value
            game_server = server.find_server_by_id2(serverid2)
            send(a00b0().setlength(10))
            send(a0035().setserverdata(game_server))

            modify_gameserver_whitelist('add', self.player, self.player.game_server)
            self.player.game_server = game_server

        elif isinstance(request, a00b3):  # server disconnect
            # TODO: check on the real server if there's a response to this msg
            # serverid2 = request.findbytype(m02c4).value
            modify_gameserver_whitelist('remove', self.player, self.player.game_server)
            self.player.game_server = None

        elif isinstance(request, a0070):  # chat
            message_type = request.findbytype(m009e).value

            if message_type == 3:  # team
                reply = a0070()
                reply.findbytype(m009e).set(3)
                reply.findbytype(m02e6).set('Unfortunately team messages are not yet supported. Use VGS for now.')
                reply.findbytype(m02fe).set('taserver')
                send(reply)

            elif message_type == 6:  # private
                addressed_player_name = request.findbytype(m034a).value
                addressed_player = server.find_player_by(display_name=addressed_player_name)
                if addressed_player:
                    request.content.append(m02fe().set(self.player.display_name))
                    request.content.append(m06de().set(self.player.tag))

                    send(request, client_id=self.player.id)

                    if self.player.id != addressed_player.id:
                        send(request, client_id=addressed_player.id)

            else:  # public
                request.content.append(m02fe().set(self.player.display_name))
                request.content.append(m06de().set(self.player.tag))

                if self.player.game_server:
                    server.send_all_on_server(request, self.player.game_server)

        elif isinstance(request, a0175):  # redeem promotion code
            authcode = request.findbytype(m0669).value
            if (self.player.login_name in server.accounts and
                    server.accounts[self.player.login_name].authcode == authcode):

                server.accounts[self.player.login_name].password_hash = self.player.password_hash
                server.accounts[self.player.login_name].authcode = None
                server.accounts.save()
                self.player.authenticated = True
            else:
                invalid_code_msg = a0175()
                invalid_code_msg.findbytype(m02fc).set(0x00019646)  # message type
                invalid_code_msg.findbytype(m0669).set(authcode)
                send(invalid_code_msg)

        elif isinstance(request, a018c):  # votekick
            response = request.findbytype(m0592)

            if response is None:  # votekick initiation
                other_player = server.find_player_by(display_name=request.findbytype(m034a).value)

                if (other_player and
                        self.player.game_server and
                        other_player.game_server and
                        self.player.game_server == other_player.game_server and
                        self.player.game_server.playerbeingkicked is None):

                    # Start a new vote
                    reply = a018c()
                    reply.content = [
                        m02c4().set(self.player.game_server.serverid2),
                        m034a().set(self.player.display_name),
                        m0348().set(self.player.id),
                        m02fc().set(0x0001942F),
                        m0442(),
                        m0704().set(other_player.id),
                        m0705().set(other_player.display_name)
                    ]
                    server.send_all_on_server(reply, self.player.game_server)

                    for player in server.players.values():
                        player.vote = None
                    self.player.game_server.playerbeingkicked = other_player

            else:  # votekick response
                if (self.player.game_server and
                        self.player.game_server.playerbeingkicked is not None):
                    current_server = self.player.game_server

                    self.player.vote = (response.value == 1)

                    votes = [p.vote for p in server.players.values() if p.vote is not None]
                    yes_votes = [v for v in votes if v]

                    if len(votes) >= 1:
                        playertokick = current_server.playerbeingkicked
                        kick = len(yes_votes) >= 1

                        reply = a018c()
                        reply.content = [
                            m0348().set(playertokick.id),
                            m034a().set(playertokick.display_name)
                        ]

                        if kick:
                            reply.content.extend([
                                m02fc().set(0x00019430),
                                m0442().set(1)
                            ])

                        else:
                            reply.content.extend([
                                m02fc().set(0x00019431),
                                m0442().set(0)
                            ])

                        server.send_all_on_server(reply, current_server)

                        if kick:
                            # TODO: figure out if a real votekick also causes an
                            # inconsistency between the menu you see and the one
                            # you're really in
                            for msg in [a00b0(),
                                        a0035().setmainmenu(),
                                        a006f()]:
                                send(msg, playertokick.id)
                            playertokick.game_server = None
                            modify_gameserver_whitelist('remove', playertokick, current_server)
                            modify_loginserver_blacklist('add', playertokick)

                        current_server.playerbeingkicked = None

            # TODO: implement removal of kickvote on timeout
