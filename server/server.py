#!/usr/bin/env python3

from datatypes import *
import random
import socket
import string

class ProtocolViolation(Exception):
    pass

class AccountInfo():
    def __init__(self, loginname, authcode):
        self.loginname = loginname
        self.authcode = authcode
        self.passwdhash = None

class PlayerInfo():
    def __init__(self):
        self.loginname = None
        self.displayname = None
        self.passwdhash = None
        self.tag = ''
        self.server = None
        self.authenticated = False

class Server():
    def __init__(self, serverqueue, clientqueues, authcodequeue):
        self.serverqueue = serverqueue
        self.clientqueues = clientqueues
        self.authcodequeue = authcodequeue
        taserveripstr = socket.gethostbyname('ta.kfk4ever.com')
        taserverip = [int(part) for part in taserveripstr.split('.')]
        
        self.servers = [
            { 'serverid1' : 0x00000001,
              'serverid2' : 0x80000001,
              'description' : 'server on 127.0.0.1',
              'motd' : 'Join this server to connect to a dedicated server running on the same machine as your client',
              'ip' : (127, 0, 0, 1),
              'port' : 7777,
            },
            { 'serverid1' : 0x00000002,
              'serverid2' : 0x80000002,
              'description' : 'server on ta.kfk4ever.com',
              'motd' : 'Join this server to connect to a dedicated server hosted by Griffon26',
              'ip' : taserverip,
              'port' : 7777,
            }
        ]
        self.players = {
        }
        self.accounts = {
        }

    def findserverbyid1(self, id1):
        for serverdata in self.servers:
            if serverdata['serverid1'] == id1:
                return serverdata
        raise ProtocolViolation('No server found with specified serverid1')

    def findserverbyid2(self, id2):
        for serverdata in self.servers:
            if serverdata['serverid2'] == id2:
                return serverdata
        raise ProtocolViolation('No server found with specified serverid2')

    def run(self):
        while True:
            for msg in self.serverqueue:
                if isinstance(msg, AuthCodeRequestMessage):
                    availablechars = ''.join(c for c in (string.ascii_letters + string.digits) if c not in 'iI')
                    authcode = ''.join([random.choice(availablechars) for i in range(8)])
                    print('server: authcode requested for %s, returned %s' % (msg.loginname, authcode))
                    self.accounts[msg.loginname] = AccountInfo(msg.loginname, authcode)
                    self.authcodequeue.put((msg.loginname, authcode))
                    
                elif isinstance(msg, ClientDisconnectedMessage):
                    print('server: client(%s)\'s reader quit; stopping writer' % msg.clientid)
                    self.clientqueues[msg.clientid].put((None, None))
                    del(self.clientqueues[msg.clientid])
                    del(self.players[msg.clientid])

                elif isinstance(msg, ClientMessage):
                    if not msg.clientid in self.players:
                        self.players[msg.clientid] = PlayerInfo()
                    currentplayer = self.players[msg.clientid]

                    def sendmsg(data, clientid=msg.clientid):
                        self.clientqueues[clientid].put((data, msg.clientseq))

                    print('server: received from client(%s) (seq = %s):\n%s' %
                            (msg.clientid, msg.clientseq, '\n'.join(['  %04X' % req.ident for req in msg.requests])))
                    for request in msg.requests:
                        if request.ident == 0x01bc:
                            sendmsg(a01bc())
                            sendmsg(a0197())
                            
                        elif request.ident == 0x003a:
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
                        elif request.ident == 0x0033:
                            sendmsg(a0033())
                            
                        elif request.ident == 0x00d5:
                            if request.findbytype(m0228).value == 1:
                                sendmsg(originalfragment(0x1EEB3, 0x20A10)) # 00d5 (map list)
                            else:
                                sendmsg(a00d5().setservers(self.servers))   # 00d5 (server list)
                                
                        elif request.ident == 0x0014:
                            sendmsg(originalfragment(0x20A18, 0x20B3F)) # 0014 (class list)
                            
                        elif request.ident == 0x018b:
                            sendmsg(originalfragment(0x20B47, 0x20B4B)) # 018b
                            
                        elif request.ident == 0x01b5:
                            sendmsg(originalfragment(0x20B53, 0x218F7)) # 01b5 (watch now)
                            
                        elif request.ident == 0x0176:
                            sendmsg(originalfragment(0x218FF, 0x219D1)) # 0176
                            sendmsg(originalfragment(0x28AC9, 0x2F4D7)) # 0177 (store 0218)
                            
                        elif request.ident == 0x00b1: # server join step 1
                            serverid1 = request.findbytype(m02c7).value
                            serverdata = self.findserverbyid1(serverid1)
                            serverid2 = serverdata['serverid2']
                            sendmsg(a00b0(9).setserverid1(serverid1))
                            sendmsg(a00b4().setserverid2(serverid2))
                            
                        elif request.ident == 0x00b2: # server join step 2
                            serverid2 = request.findbytype(m02c4).value
                            serverdata = self.findserverbyid2(serverid2)
                            sendmsg(a00b0(10))
                            sendmsg(a0035().setserverdata(serverdata))
                            
                        elif request.ident == 0x0070: # chat
                            request.content.append(m02fe().set(currentplayer.displayname))
                            request.content.append(m06de().set(currentplayer.tag))
                            
                            for otherclientid in self.players.keys():
                                sendmsg(request, otherclientid)

                        elif request.ident == 0x0175: # redeem promotion code
                            authcode = request.findbytype(m0669).value
                            if (currentplayer.loginname in self.accounts and
                                self.accounts[currentplayer.loginname].authcode == authcode):
                                
                                self.accounts[currentplayer.loginname].passwdhash = currentplayer.passwdhash
                                self.accounts[currentplayer.loginname].authcode = None
                                currentplayer.authenticated = True
                            else:
                                invalidcodemsg = a0175()
                                invalidcodemsg.findbytype(m02fc).set(0x00019646)
                                invalidcodemsg.findbytype(m0669).set(authcode)
                                sendmsg(invalidcodemsg)
                            
                        else:
                            pass

