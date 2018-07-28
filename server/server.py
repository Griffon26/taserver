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

from accounts import AccountInfo
from configuration import Configuration
from datatypes import *
import gevent.subprocess as sp
import random
import string

from player_info import PlayerInfo
from protocols.error import ProtocolViolationError


def modify_gameserver_whitelist(add_or_remove, player, server):
    if add_or_remove not in ('add', 'remove'):
        raise RuntimeError('Invalid argument provided')
    ipstring = '%d.%d.%d.%d' % player.ip
    sp.call('..\\scripts\\modifyfirewall.py whitelist %s %s' %
            (add_or_remove, ipstring), shell=True)


def modify_loginserver_blacklist(add_or_remove, player):
    if add_or_remove not in ('add', 'remove'):
        raise RuntimeError('Invalid argument provided')
    ipstring = '%d.%d.%d.%d' % player.ip
    sp.call('..\\scripts\\modifyfirewall.py blacklist %s %s' %
            (add_or_remove, ipstring), shell=True)


class Server:
    def __init__(self, server_queue, client_queues, authcode_queue, accounts, configuration: Configuration):
        self.server_queue = server_queue
        self.client_queues = client_queues
        self.authcode_queue = authcode_queue

        self.servers = configuration.server_config.servers

        self.players = {}
        self.accounts = accounts
        self.message_handlers = {
            AuthCodeRequestMessage: self.handle_authcode_request_message,
            ClientDisconnectedMessage: self.handle_client_disconnected_message,
            ClientConnectedMessage: self.handle_client_connected_message,
            ClientMessage: self.handle_client_message
        }

    def run(self):
        while True:
            for message in self.server_queue:
                handler = self.message_handlers[type(message)]
                handler(message)

    def find_server_by_id1(self, id1):
        for server in self.servers:
            if server.serverid1 == id1:
                return server
        raise ProtocolViolationError('No server found with specified serverid1')

    def find_server_by_id2(self, id2):
        for server in self.servers:
            if server.serverid2 == id2:
                return server
        raise ProtocolViolationError('No server found with specified serverid2')

    def find_player_by(self, **kwargs):
        matching_players = self.find_players_by(**kwargs)

        if len(matching_players) == 0:
            raise ValueError("No player matched query")

        if len(matching_players) > 1:
            raise ValueError("More than one player matched query")
        return matching_players[0]

    def find_players_by(self, **kwargs):
        matching_players = self.players

        for key, val in kwargs.items():
            matching_players = [player for player in matching_players if getattr(player, key) == val]

        return matching_players

    def handle_authcode_request_message(self, msg):
        availablechars = ''.join(c for c in (string.ascii_letters + string.digits) if c not in 'O0Il')
        authcode = ''.join([random.choice(availablechars) for i in range(8)])
        print('server: authcode requested for %s, returned %s' % (msg.login_name, authcode))
        self.accounts[msg.login_name] = AccountInfo(msg.login_name, authcode)
        self.accounts.save()
        self.authcode_queue.put((msg.login_name, authcode))

    def handle_client_disconnected_message(self, msg):
        print('server: client(%s)\'s reader quit; stopping writer' % msg.clientid)
        self.client_queues[msg.clientid].put((None, None))
        del (self.client_queues[msg.clientid])

        # Remove and don't complain if it wasn't there yet
        self.players.pop(msg.clientid, None)

    def handle_client_connected_message(self, msg):
        self.players[msg.clientid] = PlayerInfo(msg.clientid, msg.clientaddress, msg.clientport)

    def handle_client_message(self, msg):

        current_player = self.players[msg.clientid]
        current_player.lastreceivedseq = msg.clientseq

        def sendmsg(data, clientid=msg.clientid):
            self.client_queues[clientid].put((data, self.players[clientid].lastreceivedseq))

        def send_all_on_server(data, server):
            for player in self.find_players_by(server=server):
                sendmsg(data, player.id)

        print('server: client(%s, %s:%s, "%s") sent:\n%s' %
              (msg.clientid,
               current_player.ip,
               current_player.port,
               current_player.display_name,
               '\n'.join(['  %04X' % req.ident for req in msg.requests])))

        # TODO: implement a state machine in player such that we only
        # attempt to parse all kinds of messages after the player has
        # authenticated and his data is in the self.players dict
        for request in msg.requests:
            if isinstance(request, a01bc):
                sendmsg(a01bc())
                sendmsg(a0197())

            elif isinstance(request, a003a):
                if request.findbytype(m0056) is None:  # request for login
                    sendmsg(a003a())

                else:  # actual login
                    current_player.login_name = request.findbytype(m0494).value
                    current_player.password_hash = request.findbytype(m0056).content

                    if (current_player.login_name in self.accounts and
                            current_player.password_hash == self.accounts[current_player.login_name].password_hash):
                        current_player.authenticated = True

                    current_player.display_name = (
                                                    '' if current_player.authenticated else 'unverif-') + current_player.login_name
                    sendmsg([
                        a003d().setplayer(current_player.display_name, ''),
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
                sendmsg(a0033())

            elif isinstance(request, a00d5):
                if request.findbytype(m0228).value == 1:
                    sendmsg(originalfragment(0x1EEB3, 0x20A10))  # 00d5 (map list)
                else:
                    sendmsg(a00d5().setservers(self.servers))  # 00d5 (server list)

            elif isinstance(request, a0014):
                sendmsg(originalfragment(0x20A18, 0x20B3F))  # 0014 (class list)

            elif isinstance(request, a018b):
                sendmsg(originalfragment(0x20B47, 0x20B4B))  # 018b

            elif isinstance(request, a01b5):
                sendmsg(originalfragment(0x20B53, 0x218F7))  # 01b5 (watch now)

            elif isinstance(request, a0176):
                sendmsg(originalfragment(0x218FF, 0x219D1))  # 0176
                sendmsg(originalfragment(0x28AC9, 0x2F4D7))  # 0177 (store 0218)

            elif isinstance(request, a00b1):  # server join step 1
                serverid1 = request.findbytype(m02c7).value
                server = self.find_server_by_id1(serverid1)
                serverid2 = server.serverid2
                sendmsg(a00b0().setlength(9).setserverid1(serverid1))
                sendmsg(a00b4().setserverid2(serverid2))

            elif isinstance(request, a00b2):  # server join step 2
                serverid2 = request.findbytype(m02c4).value
                server = self.find_server_by_id2(serverid2)
                sendmsg(a00b0().setlength(10))
                sendmsg(a0035().setserverdata(server))

                modify_gameserver_whitelist('add', current_player, current_player.server)
                current_player.server = server

            elif isinstance(request, a00b3):  # server disconnect
                # TODO: check on the real server if there's a response to this msg
                # serverid2 = request.findbytype(m02c4).value
                modify_gameserver_whitelist('remove', current_player, current_player.server)
                current_player.server = None

            elif isinstance(request, a0070):  # chat
                messagetype = request.findbytype(m009e).value

                if messagetype == 3:  # team
                    reply = a0070()
                    reply.findbytype(m009e).set(3)
                    reply.findbytype(m02e6).set('Unfortunately team messages are not yet supported. Use VGS for now.')
                    reply.findbytype(m02fe).set('taserver')
                    sendmsg(reply)

                elif messagetype == 6:  # private
                    addressedplayername = request.findbytype(m034a).value
                    addressedplayer = self.find_player_by(display_name=addressedplayername)
                    if addressedplayer:
                        request.content.append(m02fe().set(current_player.display_name))
                        request.content.append(m06de().set(current_player.tag))

                        sendmsg(request, clientid=current_player.id)

                        if current_player.id != addressedplayer.id:
                            sendmsg(request, clientid=addressedplayer.id)

                else:  # public
                    request.content.append(m02fe().set(current_player.display_name))
                    request.content.append(m06de().set(current_player.tag))

                    if current_player.server:
                        send_all_on_server(request, current_player.server)

            elif isinstance(request, a0175):  # redeem promotion code
                authcode = request.findbytype(m0669).value
                if (current_player.login_name in self.accounts and
                        self.accounts[current_player.login_name].authcode == authcode):

                    self.accounts[current_player.login_name].password_hash = current_player.password_hash
                    self.accounts[current_player.login_name].authcode = None
                    self.accounts.save()
                    current_player.authenticated = True
                else:
                    invalidcodemsg = a0175()
                    invalidcodemsg.findbytype(m02fc).set(0x00019646)  # message type
                    invalidcodemsg.findbytype(m0669).set(authcode)
                    sendmsg(invalidcodemsg)

            elif isinstance(request, a018c):  # votekick
                response = request.findbytype(m0592)

                if response is None:  # votekick initiation
                    otherplayer = self.find_player_by(display_name=request.findbytype(m034a).value)

                    if (otherplayer and
                            current_player.server and
                            otherplayer.server and
                            current_player.server == otherplayer.server and
                            current_player.server.playerbeingkicked == None):

                        # Start a new vote
                        reply = a018c()
                        reply.content = [
                            m02c4().set(current_player.server.serverid2),
                            m034a().set(current_player.display_name),
                            m0348().set(current_player.id),
                            m02fc().set(0x0001942F),
                            m0442(),
                            m0704().set(otherplayer.id),
                            m0705().set(otherplayer.display_name)
                        ]
                        send_all_on_server(reply, current_player.server)

                        for player in self.players.values():
                            player.vote = None
                        current_player.server.playerbeingkicked = otherplayer

                else:  # votekick response
                    if (current_player.server and
                            current_player.server.playerbeingkicked != None):
                        currentserver = current_player.server

                        current_player.vote = (response.value == 1)

                        votes = [p.vote for p in self.players.values() if p.vote is not None]
                        yesvotes = [v for v in votes if v]

                        if len(votes) >= 1:
                            playertokick = currentserver.playerbeingkicked
                            kick = len(yesvotes) >= 1

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

                            send_all_on_server(reply, currentserver)

                            if kick:
                                # TODO: figure out if a real votekick also causes an
                                # inconsistency between the menu you see and the one
                                # you're really in
                                for msg in [a00b0(),
                                            a0035().setmainmenu(),
                                            a006f()]:
                                    sendmsg(msg, playertokick.id)
                                playertokick.server = None
                                modify_gameserver_whitelist('remove', playertokick, currentserver)
                                modify_loginserver_blacklist('add', playertokick)

                            currentserver.playerbeingkicked = None

                # TODO: implement removal of kickvote on timeout


            else:
                pass
