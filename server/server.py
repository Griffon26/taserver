#!/usr/bin/env python3

from datatypes import *

class Server():
    def __init__(self, serverqueue, clientqueues):
        self.serverqueue = serverqueue
        self.clientqueues = clientqueues

    def run(self):
        authenticated = False
        while True:
            for clientid, clientseq, requests in self.serverqueue:
                if requests == None:
                    self.clientqueues[clientid].put((None, None))
                    del(self.clientqueues[clientid])
                else:

                    def sendmsg(msg):
                        self.clientqueues[clientid].put((msg, clientseq))

                    print('server: received from client(%s) (seq = %s):\n%s' %
                            (clientid, clientseq, '\n'.join(['  %04X' % req.ident for req in requests])))
                    for request in requests:
                        if request.ident == 0x01bc:
                            sendmsg(a01bc())
                            sendmsg(a0197())
                        elif request.ident == 0x003a:
                            if not authenticated:
                                authenticated = True
                                sendmsg(a003a())
                            else:
                                sendmsg([
                                    a003d(),
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
                            if request.content[0].ident != 0x0228:
                                raise RuntimeError('oh shit')
                            if request.content[0].value == 1:
                                sendmsg(originalfragment(0x1EEB3, 0x20A18)) # 00d5 (map list)
                            else:
                                sendmsg(a00d5())
                        elif request.ident == 0x0014:
                            sendmsg(originalfragment(0x20A18, 0x20B47)) # 0014 (class list)
                        elif request.ident == 0x018b:
                            sendmsg(originalfragment(0x20B47, 0x20B53)) # 018b
                        elif request.ident == 0x01b5:
                            sendmsg(originalfragment(0x20B53, 0x218FF)) # 01b5 (watch now)
                        elif request.ident == 0x0176:
                            sendmsg(originalfragment(0x218FF, 0x219D9)) # 0176
                            sendmsg(originalfragment(0x28AC9, 0x2F4DF)) # 0177 (store 0218)
                        elif request.ident == 0x00b1:
                            sendmsg(a00b0(9))
                            sendmsg(a00b4())
                        elif request.ident == 0x00b2:
                            sendmsg(a00b0(10))
                            sendmsg(a0035())
                        elif request.ident == 0x0070:
                            request.content.append(m02fe().set('Griffon28'))
                            request.content.append(m06de().set('tag'))
                            sendmsg(request)
                        else:
                            pass

