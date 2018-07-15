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
from datatypes import *
import gevent.subprocess as sp
import random
import socket
import string

def tuple2ipstring(iptuple):
    return '%d.%d.%d.%d' % iptuple

def modifygameserverwhitelist(add_or_remove, player, server):
    if add_or_remove not in ('add', 'remove'):
        raise RuntimeError('Invalid argument provided')
    ipstring = '%d.%d.%d.%d' % player.ip
    sp.call('..\\scripts\\modifyfirewall.py whitelist %s %s' %
             (add_or_remove, ipstring), shell=True)

def modifyloginserverblacklist(add_or_remove, player):
    if add_or_remove not in ('add', 'remove'):
        raise RuntimeError('Invalid argument provided')
    ipstring = '%d.%d.%d.%d' % player.ip
    sp.call('..\\scripts\\modifyfirewall.py blacklist %s %s' %
             (add_or_remove, ipstring), shell=True)

class ProtocolViolation(Exception):
    pass

class ServerInfo():
    def __init__(self, serverid1, serverid2, description, motd, ip, port):
        self.serverid1 = serverid1
        self.serverid2 = serverid2
        self.description = description
        self.motd = motd
        self.ip = ip
        self.port = port
        self.playerbeingkicked = None

class PlayerInfo():
    def __init__(self, playerid, playerip, playerport):
        self.id = playerid
        self.loginname = None
        self.displayname = None
        self.passwdhash = None
        self.tag = ''
        self.ip = playerip
        self.port = playerport
        self.server = None
        self.authenticated = False
        self.lastreceivedseq = 0
        self.vote = None

class Server():
    def __init__(self, serverqueue, clientqueues, authcodequeue, accounts):
        self.serverqueue = serverqueue
        self.clientqueues = clientqueues
        self.authcodequeue = authcodequeue
        
        taserveripstr = socket.gethostbyname('ta.kfk4ever.com')
        taserverip = [int(part) for part in taserveripstr.split('.')]

        samserveripstr = socket.gethostbyname('sam.kfk4ever.com')
        samserverip = [int(part) for part in samserveripstr.split('.')]
        
        self.servers = [
            ServerInfo(
                0x00000001,
                0x80000001,
                '127.0.0.1',
                'Join this server to connect to a game server running on the same machine as your client',
                (127, 0, 0, 1),
                7777
            ),
            ServerInfo(
                0x00000002,
                0x80000002,
                'ta.kfk4ever.com (AWS t2.micro)',
                'Join this server to connect to a game server hosted by Griffon26',
                taserverip,
                7777
            ),
            ServerInfo(
                0x00000003,
                0x80000003,
                "sam.kfk4ever.com (AWS t2.medium)",
                'Join this server to connect to a game server hosted by Sam',
                samserverip,
                7777
            )
        ]
        self.players = {
        }
        self.accounts = accounts

    def run(self):
        while True:
            for msg in self.serverqueue:
                messagehandlers = {
                    AuthCodeRequestMessage : self.handleauthcoderequestmessage,
                    ClientDisconnectedMessage: self.handleclientdisconnectedmessage,
                    ClientConnectedMessage: self.handleclientconnectedmessage,
                    ClientMessage: self.handleclientmessage
                }
                messagehandlers[type(msg)](msg)

    def findserverbyid1(self, id1):
        for server in self.servers:
            if server.serverid1 == id1:
                return server
        raise ProtocolViolation('No server found with specified serverid1')

    def findserverbyid2(self, id2):
        for server in self.servers:
            if server.serverid2 == id2:
                return server
        raise ProtocolViolation('No server found with specified serverid2')

    def findplayerbyid(self, playerid):
        return self.players[playerid] if playerid in self.players else None

    def findplayerbydisplayname(self, displayname):
        for player in self.players.values():
            if player.displayname == displayname:
                return player
        return None

    def allplayersonserver(self, server):
        return (p for p in self.players.values() if p.server is server)

    def handleauthcoderequestmessage(self, msg):
        availablechars = ''.join(c for c in (string.ascii_letters + string.digits) if c not in 'O0Il')
        authcode = ''.join([random.choice(availablechars) for i in range(8)])
        print('server: authcode requested for %s, returned %s' % (msg.loginname, authcode))
        self.accounts[msg.loginname] = AccountInfo(msg.loginname, authcode)
        self.accounts.save()
        self.authcodequeue.put((msg.loginname, authcode))

    def handleclientdisconnectedmessage(self, msg):
        print('server: client(%s)\'s reader quit; stopping writer' % msg.clientid)
        self.clientqueues[msg.clientid].put((None, None))
        del(self.clientqueues[msg.clientid])

        # Remove and don't complain if it wasn't there yet
        self.players.pop(msg.clientid, None)

    def handleclientconnectedmessage(self, msg):
        self.players[msg.clientid] = PlayerInfo(msg.clientid, msg.clientaddress, msg.clientport)

    def handleclientmessage(self, msg):

        currentplayer = self.players[msg.clientid]
        currentplayer.lastreceivedseq = msg.clientseq

        def sendmsg(data, clientid=msg.clientid):
            self.clientqueues[clientid].put((data, self.players[clientid].lastreceivedseq))

        def sendallonserver(data, server):
            for player in self.allplayersonserver(server):
                sendmsg(data, player.id)

        print('server: client(%s, %s:%s, "%s") sent:\n%s' %
                (msg.clientid,
                 tuple2ipstring(currentplayer.ip),
                 currentplayer.port,
                 currentplayer.displayname,
                 '\n'.join(['  %04X' % req.ident for req in msg.requests])))

        # TODO: implement a state machine in player such that we only
        # attempt to parse all kinds of messages after the player has
        # authenticated and his data is in the self.players dict
        for request in msg.requests:
            if isinstance(request, a01bc):
                sendmsg(a01bc())
                sendmsg(a0197())
                
            elif isinstance(request, a003a):
                if request.findbytype(m0056) is None: # request for login
                    sendmsg(a003a())
                    
                else: # actual login
                    currentplayer.loginname = request.findbytype(m0494).value
                    currentplayer.passwdhash = request.findbytype(m0056).content

                    if (currentplayer.loginname in self.accounts and
                        currentplayer.passwdhash == self.accounts[currentplayer.loginname].passwdhash):
                        currentplayer.authenticated = True
                    
                    currentplayer.displayname = ('' if currentplayer.authenticated else 'unverif-') + currentplayer.loginname
                    sendmsg([
                        a003d().setplayer(currentplayer.displayname, ''),
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
                    sendmsg(originalfragment(0x1EEB3, 0x20A10)) # 00d5 (map list)
                else:
                    sendmsg(a00d5().setservers(self.servers))   # 00d5 (server list)
                    
            elif isinstance(request, a0014):
                sendmsg(originalfragment(0x20A18, 0x20B3F)) # 0014 (class list)
                
            elif isinstance(request, a018b):
                sendmsg(originalfragment(0x20B47, 0x20B4B)) # 018b
                
            elif isinstance(request, a01b5):
                sendmsg(originalfragment(0x20B53, 0x218F7)) # 01b5 (watch now)
                
            elif isinstance(request, a0176):
                sendmsg(originalfragment(0x218FF, 0x219D1)) # 0176
                sendmsg(originalfragment(0x28AC9, 0x2F4D7)) # 0177 (store 0218)
                
            elif isinstance(request, a00b1): # server join step 1
                serverid1 = request.findbytype(m02c7).value
                server = self.findserverbyid1(serverid1)
                serverid2 = server.serverid2
                sendmsg(a00b0().setlength(9).setserverid1(serverid1))
                sendmsg(a00b4().setserverid2(serverid2))
                
            elif isinstance(request, a00b2): # server join step 2
                serverid2 = request.findbytype(m02c4).value
                server = self.findserverbyid2(serverid2)
                sendmsg(a00b0().setlength(10))
                sendmsg(a0035().setserverdata(server))
                
                modifygameserverwhitelist('add', currentplayer, currentplayer.server)
                currentplayer.server = server

            elif isinstance(request, a00b3): # server disconnect
                # TODO: check on the real server if there's a response to this msg
                #serverid2 = request.findbytype(m02c4).value
                modifygameserverwhitelist('remove', currentplayer, currentplayer.server)
                currentplayer.server = None
                
            elif isinstance(request, a0070): # chat
                messagetype = request.findbytype(m009e).value
                
                if messagetype == 3: # team
                    reply = a0070()
                    reply.findbytype(m009e).set(3)
                    reply.findbytype(m02e6).set('Unfortunately team messages are not yet supported. Use VGS for now.')
                    reply.findbytype(m02fe).set('taserver')
                    sendmsg(reply)
                    
                elif messagetype == 6: # private
                    addressedplayername = request.findbytype(m034a).value;
                    addressedplayer = self.findplayerbydisplayname(addressedplayername)
                    if addressedplayer:
                        request.content.append(m02fe().set(currentplayer.displayname))
                        request.content.append(m06de().set(currentplayer.tag))
                        
                        sendmsg(request, clientid=currentplayer.id)
                        
                        if currentplayer.id != addressedplayer.id:
                            sendmsg(request, clientid=addressedplayer.id)
                    
                else: # public
                    request.content.append(m02fe().set(currentplayer.displayname))
                    request.content.append(m06de().set(currentplayer.tag))

                    if currentplayer.server:
                        sendallonserver(request, currentplayer.server)

            elif isinstance(request, a0175): # redeem promotion code
                authcode = request.findbytype(m0669).value
                if (currentplayer.loginname in self.accounts and
                    self.accounts[currentplayer.loginname].authcode == authcode):
                    
                    self.accounts[currentplayer.loginname].passwdhash = currentplayer.passwdhash
                    self.accounts[currentplayer.loginname].authcode = None
                    self.accounts.save()
                    currentplayer.authenticated = True
                else:
                    invalidcodemsg = a0175()
                    invalidcodemsg.findbytype(m02fc).set(0x00019646) # message type
                    invalidcodemsg.findbytype(m0669).set(authcode)
                    sendmsg(invalidcodemsg)

            elif isinstance(request, a018c): # votekick
                response = request.findbytype(m0592)
                
                if response is None: # votekick initiation
                    otherplayer = self.findplayerbydisplayname(request.findbytype(m034a).value)
                    
                    if ( otherplayer and
                         currentplayer.server and
                         otherplayer.server and
                         currentplayer.server == otherplayer.server and
                         currentplayer.server.playerbeingkicked == None ):

                        # Start a new vote
                        reply = a018c()
                        reply.content = [
                            m02c4().set(currentplayer.server.serverid2),
                            m034a().set(currentplayer.displayname),
                            m0348().set(currentplayer.id),
                            m02fc().set(0x0001942F),
                            m0442(),
                            m0704().set(otherplayer.id),
                            m0705().set(otherplayer.displayname)
                        ]
                        sendallonserver(reply, currentplayer.server)

                        for player in self.players.values():
                            player.vote = None
                        currentplayer.server.playerbeingkicked = otherplayer
                        
                else: # votekick response
                    if ( currentplayer.server and
                         currentplayer.server.playerbeingkicked != None ):
                        currentserver = currentplayer.server
                        
                        currentplayer.vote = (response.value == 1)

                        votes = [p.vote for p in self.players.values() if p.vote is not None]
                        yesvotes = [v for v in votes if v]

                        if len(votes) >= 1:
                            playertokick = currentserver.playerbeingkicked
                            kick = len(yesvotes) >= 1

                            reply = a018c()
                            reply.content = [
                                m0348().set(playertokick.id),
                                m034a().set(playertokick.displayname)
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

                            sendallonserver(reply, currentserver)

                            if kick:
                                # TODO: figure out if a real votekick also causes an
                                # inconsistency between the menu you see and the one
                                # you're really in
                                for msg in [a00b0(),
                                            a0035().setmainmenu(),
                                            a006f()]:
                                    sendmsg(msg, playertokick.id)
                                playertokick.server = None
                                modifygameserverwhitelist('remove', playertokick, currentserver)
                                modifyloginserverblacklist('add', playertokick)
                            
                            currentserver.playerbeingkicked = None

                # TODO: implement removal of kickvote on timeout


            else:
                pass

