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
from player.state.handles_decorator import handles
from player.state.player_state import PlayerState

from datatypes import *


class LoggedInState(PlayerState):
    @handles(packet=a0033, inherited=False)
    def handle_a0033(self, request):
        self.player.send(a0033())

    @handles(packet=a00d5, inherited=False)
    def handle_a00d5(self, request):
        if request.findbytype(m0228).value == 1:
            self.player.send(originalfragment(0x1EEB3, 0x20A10))  # 00d5 (map list)
        else:
            self.player.send(a00d5().setservers(self.player.server.game_servers))  # 00d5 (server list)

    @handles(packet=a0014, inherited=False)
    def handle_a0014(self, request):
        self.player.send(originalfragment(0x20A18, 0x20B3F))  # 0014 (class list)

    @handles(packet=a018b, inherited=False)
    def handle_a018b(self, request):
        self.player.send(originalfragment(0x20B47, 0x20B4B))  # 018b

    @handles(packet=a01b5, inherited=False)
    def handle_a01b5(self, request):
        self.player.send(originalfragment(0x20B53, 0x218F7))  # 01b5 (watch now)

    @handles(packet=a0176, inherited=False)
    def handle_a0176(self, request):
        self.player.send(originalfragment(0x218FF, 0x219D1))  # 0176
        self.player.send(originalfragment(0x28AC9, 0x2F4D7))  # 0177 (store 0218)

    @handles(packet=a00b1, inherited=False)
    def handle_server_join_first_step(self, request):
        serverid1 = request.findbytype(m02c7).value
        game_server = self.player.server.find_server_by_id1(serverid1)
        serverid2 = game_server.serverid2
        self.player.send(a00b0().setlength(9).setserverid1(serverid1))
        self.player.send(a00b4().setserverid2(serverid2))

    @handles(packet=a00b2, inherited=False)
    def handle_server_join_second_step(self, request):
        serverid2 = request.findbytype(m02c4).value
        game_server = self.player.server.find_server_by_id2(serverid2)
        self.player.send(a00b0().setlength(10))
        self.player.send(a0035().setserverdata(game_server))

        modify_gameserver_whitelist('add', self.player, self.player.game_server)
        self.player.game_server = game_server

        # todo: add joined server state and enter it

    @handles(packet=a00b3, inherited=True)
    def handle_server_disconnect(self, request):  # server disconnect
        # TODO: check on the real server if there's a response to this msg
        # serverid2 = request.findbytype(m02c4).value
        modify_gameserver_whitelist('remove', self.player, self.player.game_server)
        self.player.game_server = None

    @handles(packet=a0070, inherited=True)
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
            addressed_player = self.player.server.find_player_by(display_name=addressed_player_name)
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
                self.player.server.send_all_on_server(request, self.player.game_server)

    @handles(packet=a0175, inherited=True)
    def handle_promotion_code_redemption(self, request):
        authcode = request.findbytype(m0669).value
        if (self.player.login_name in self.player.server.accounts and
                self.player.server.accounts[self.player.login_name].authcode == authcode):

            self.player.server.accounts[self.player.login_name].password_hash = self.player.password_hash
            self.player.server.accounts[self.player.login_name].authcode = None
            self.player.server.accounts.save()
            self.player.authenticated = True
        else:
            invalid_code_msg = a0175()
            invalid_code_msg.findbytype(m02fc).set(0x00019646)  # message type
            invalid_code_msg.findbytype(m0669).set(authcode)
            self.player.send(invalid_code_msg)

    @handles(packet=a018c, inherited=True)
    def handle_votekick(self, request):
        response = request.findbytype(m0592)

        if response is None:  # votekick initiation
            other_player = self.player.server.find_player_by(display_name=request.findbytype(m034a).value)

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
                self.player.server.send_all_on_server(reply, self.player.game_server)

                for player in self.player.server.players.values():
                    player.vote = None
                self.player.game_server.playerbeingkicked = other_player

        else:  # votekick response
            if (self.player.game_server and
                    self.player.game_server.playerbeingkicked is not None):
                current_server = self.player.game_server

                self.player.vote = (response.value == 1)

                votes = [p.vote for p in self.player.server.players.values() if p.vote is not None]
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

                        self.player.server.send_all_on_server(reply, current_server)

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
