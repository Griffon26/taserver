#!/usr/bin/env python3

from gevent import socket
from datatypes import AuthCodeRequestMessage
import struct

authcodeaddress = ('127.0.0.1', 9800)

class AuthCodeHandler():
    def __init__(self, serverqueue, authcodequeue):
        self.serverqueue = serverqueue
        self.authcodequeue = authcodequeue

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(authcodeaddress)
        while True:
            data, addr = sock.recvfrom(4096)
            length = struct.unpack('<H', data[0:2])[0]
            namefromclient = data[2:2+length].decode('latin1')
            self.serverqueue.put(AuthCodeRequestMessage(namefromclient))
            
            namefromserver, authcode = self.authcodequeue.get()
            if namefromserver != namefromclient:
                raise RuntimeError('bug!')
            sock.sendto(struct.pack('<H', len(authcode)) + authcode.encode('latin1'), addr)
