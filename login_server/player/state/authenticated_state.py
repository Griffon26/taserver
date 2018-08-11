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

from ...datatypes import *
from ...firewall import modify_gameserver_whitelist, modify_loginserver_blacklist
from .player_state import PlayerState, handles


class AuthenticatedState(PlayerState):
    @handles(packet=a0033)
    def handle_a0033(self, request):
        self.player.send(a0033())

    @handles(packet=a00d5)
    def handle_a00d5(self, request):
        if request.findbytype(m0228).value == 1:
            self.player.send(originalfragment(0x1EEB3, 0x20A10))  # 00d5 (map list)
        else:
            self.player.send(a00d5().setservers(self.player.login_server.game_servers))  # 00d5 (server list)

    @handles(packet=a0014)
    def handle_a0014(self, request):
        self.player.send(originalfragment(0x20A18, 0x20B3F))  # 0014 (class list)

    @handles(packet=a018b)
    def handle_a018b(self, request):
        self.player.send(originalfragment(0x20B47, 0x20B4B))  # 018b

    @handles(packet=a01b5)
    def handle_a01b5(self, request):
        self.player.send(originalfragment(0x20B53, 0x218F7))  # 01b5 (watch now)

    @handles(packet=a0176)
    def handle_a0176(self, request):
        self.player.send(originalfragment(0x218FF, 0x219D1))  # 0176

    @handles(packet=a0177)
    def handle_menu(self, request):
        menu_part = request.findbytype(m02ab).value
        menu_fragments = {
            0x01de: originalfragment(0x38d17, 0x3d0fe),
            0x01ed: originalfragment(0x219d9, 0x2219e),
            0x01f0: originalfragment(0x4758e, 0x54bbe),
            0x01f1: originalfragment(0x54bc6, 0x54db0),
            0x01f2: originalfragment(0x55a2e, 0x57375),
            0x01f3: originalfragment(0x54db8, 0x55a26),
            0x01f4: originalfragment(0x5a776, 0x6fde3),
            0x01f6: originalfragment(0x5965a, 0x5a72b),
            0x01f7: originalfragment(0x5a733, 0x5a76e),
            0x01f8: originalfragment(0x5737d, 0x579af),
            0x01f9: originalfragment(0x579b7, 0x586a7),
            0x01fa: originalfragment(0x221a6, 0x22723),
            0x01fb: originalfragment(0x2272b, 0x235b8),
            0x01fc: originalfragment(0x235c0, 0x239dd),
            0x0200: originalfragment(0x239e5, 0x23acf),
            0x0206: originalfragment(0x2620e, 0x28ac1),
            0x0214: originalfragment(0x23ad7, 0x26206),
            0x0218: originalfragment(0x28ac9, 0x2f4d7),
            0x021b: originalfragment(0x3d106, 0x47586),
            0x021c: originalfragment(0x6fdeb, 0x6fecf),
            0x0220: originalfragment(0x586af, 0x59652),
            0x0221: originalfragment(0x2f4df, 0x2f69f),
            0x0227: originalfragment(0x2f6a7, 0x38d0f),
        }
        if menu_part in menu_fragments:
            self.player.send(menu_fragments[menu_part])

    @handles(packet=a00b1)
    def handle_server_join_first_step(self, request):
        serverid1 = request.findbytype(m02c7).value
        game_server = self.player.login_server.find_server_by_id1(serverid1)
        serverid2 = game_server.serverid2
        self.player.send(a00b0().setlength(9).setserverid1(serverid1))
        self.player.send(a00b4().setserverid2(serverid2))

    @handles(packet=a00b2)
    def handle_server_join_second_step(self, request):
        serverid2 = request.findbytype(m02c4).value
        game_server = self.player.login_server.find_server_by_id2(serverid2)
        self.player.send(a00b0().setlength(10))
        self.player.send(a0035().setserverdata(game_server))

        modify_gameserver_whitelist('add', self.player, self.player.game_server)
        self.player.game_server = game_server

        # todo: add joined server state and enter it

    @handles(packet=a00b3)
    def handle_server_disconnect(self, request):  # server disconnect
        # TODO: check on the real server if there's a response to this msg
        # serverid2 = request.findbytype(m02c4).value
        modify_gameserver_whitelist('remove', self.player, self.player.game_server)
        self.player.game_server = None

    @handles(packet=a0070)
    def handle_chat(self, request):
        message_type = request.findbytype(m009e).value

        if message_type == 3:  # team
            reply = a0070()
            reply.findbytype(m009e).set(3)
            reply.findbytype(m02e6).set('Unfortunately team messages are not yet supported. Use VGS for now.')
            reply.findbytype(m02fe).set('taserver')
            self.player.send(reply)

        elif message_type == 6:  # private
            addressed_player_name = request.findbytype(m034a).value
            addressed_player = self.player.login_server.find_player_by(display_name=addressed_player_name)
            if addressed_player:
                request.content.append(m02fe().set(self.player.display_name))
                request.content.append(m06de().set(self.player.tag))

                self.player.send(request)

                if self.player.id != addressed_player.id:
                    addressed_player.send(request)

        else:  # public
            request.content.append(m02fe().set(self.player.display_name))
            request.content.append(m06de().set(self.player.tag))

            if self.player.game_server:
                self.player.login_server.send_all_on_server(request, self.player.game_server)

    @handles(packet=a0175)
    def handle_promotion_code_redemption(self, request):
        authcode = request.findbytype(m0669).value
        if (self.player.login_name in self.player.login_server.accounts and
                self.player.login_server.accounts[self.player.login_name].authcode == authcode):

            self.player.login_server.accounts[self.player.login_name].password_hash = self.player.password_hash
            self.player.login_server.accounts[self.player.login_name].authcode = None
            self.player.login_server.accounts.save()
            self.player.authenticated = True
        else:
            invalid_code_msg = a0175()
            invalid_code_msg.findbytype(m02fc).set(0x00019646)  # message type
            invalid_code_msg.findbytype(m0669).set(authcode)
            self.player.send(invalid_code_msg)

    @handles(packet=a018c)
    def handle_votekick(self, request):
        response = request.findbytype(m0592)

        if response is None:  # votekick initiation
            other_player = self.player.login_server.find_player_by(display_name=request.findbytype(m034a).value)

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
                self.player.login_server.send_all_on_server(reply, self.player.game_server)

                for player in self.player.login_server.players.values():
                    player.vote = None
                self.player.game_server.playerbeingkicked = other_player

        else:  # votekick response
            if (self.player.game_server and
                    self.player.game_server.playerbeingkicked is not None):
                current_server = self.player.game_server

                self.player.vote = (response.value == 1)

                votes = [p.vote for p in self.player.login_server.players.values() if p.vote is not None]
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

                        self.player.login_server.send_all_on_server(reply, current_server)

                    if kick:
                        # TODO: figure out if a real votekick also causes an
                        # inconsistency between the menu you see and the one
                        # you're really in
                        for msg in [a00b0(), a0035().setmainmenu(), a006f()]:
                            playertokick.send(msg)
                        playertokick.game_server = None
                        modify_gameserver_whitelist('remove', playertokick, current_server)
                        modify_loginserver_blacklist('add', playertokick)

                    current_server.playerbeingkicked = None

        # TODO: implement removal of kickvote on timeout
