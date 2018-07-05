#!/usr/bin/env python3

from accounts import AccountInfo
from datatypes import *
import random
import socket
import string

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
    def __init__(self, playerid):
        self.id = playerid
        self.loginname = None
        self.displayname = None
        self.passwdhash = None
        self.tag = ''
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
        
        self.servers = [
            ServerInfo(
                0x00000001,
                0x80000001,
                'server on 127.0.0.1',
                'Join this server to connect to a dedicated server running on the same machine as your client',
                (127, 0, 0, 1),
                7777
            ),
            ServerInfo(
                0x00000002,
                0x80000002,
                'server on ta.kfk4ever.com',
                'Join this server to connect to a dedicated server hosted by Griffon26',
                taserverip,
                7777
            )
        ]
        self.players = {
        }
        self.accounts = accounts

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

    def run(self):
        while True:
            for msg in self.serverqueue:
                if isinstance(msg, AuthCodeRequestMessage):
                    availablechars = ''.join(c for c in (string.ascii_letters + string.digits) if c not in 'O0Il')
                    authcode = ''.join([random.choice(availablechars) for i in range(8)])
                    print('server: authcode requested for %s, returned %s' % (msg.loginname, authcode))
                    self.accounts[msg.loginname] = AccountInfo(msg.loginname, authcode)
                    self.accounts.save()
                    self.authcodequeue.put((msg.loginname, authcode))
                    
                elif isinstance(msg, ClientDisconnectedMessage):
                    print('server: client(%s)\'s reader quit; stopping writer' % msg.clientid)
                    self.clientqueues[msg.clientid].put((None, None))
                    del(self.clientqueues[msg.clientid])

                    # Remove and don't complain if it wasn't there yet
                    self.players.pop(msg.clientid, None)

                elif isinstance(msg, ClientMessage):
                    if not msg.clientid in self.players:
                        self.players[msg.clientid] = PlayerInfo(msg.clientid)
                    currentplayer = self.players[msg.clientid]
                    currentplayer.lastreceivedseq = msg.clientseq

                    def sendmsg(data, clientid=msg.clientid):
                        self.clientqueues[clientid].put((data, self.players[clientid].lastreceivedseq))

                    def sendallonserver(data, server):
                        for player in self.allplayersonserver(server):
                            sendmsg(data, player.id)

                    print('server: received from client(%s) (seq = %s):\n%s' %
                            (msg.clientid, msg.clientseq, '\n'.join(['  %04X' % req.ident for req in msg.requests])))

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
                                
                                currentplayer.displayname = ('' if currentplayer.authenticated else 'unverif.') + currentplayer.loginname
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
                            currentplayer.server = server

                        # TODO: reset currentplayer.server when the player exits the match
                            
                        elif isinstance(request, a0070): # chat
                            if request.findbytype(m009e).value == 3:
                                reply = a0070()
                                reply.findbytype(m009e).set(3)
                                reply.findbytype(m02e6).set('Unfortunately team messages are not yet supported. Use VGS for now.')
                                reply.findbytype(m02fe).set('taserver')
                                sendmsg(reply)
                            else:
                                request.content.append(m02fe().set(currentplayer.displayname))
                                request.content.append(m06de().set(currentplayer.tag))

                                if currentplayer.server:
                                    sendallonserver(request, server)

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
                                        
                                        currentserver.playerbeingkicked = None
                                        

                            # TODO: implement removal of kickvote on timeout
                                
                                    
                        else:
                            pass

