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

import argparse
from gevent import socket
import struct

serveraddress = ("127.0.0.1", 9800)

def main(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    data = struct.pack('<H', len(args.username)) + \
            args.username.encode('latin1')
    sock.sendto(data, serveraddress)
    
    addr = None
    while addr != serveraddress:
        data, addr = sock.recvfrom(4096)
    authcodelen = struct.unpack('<H', data[0:2])[0]
    authcode = data[2:2+authcodelen].decode('latin1')

    print('Received authcode %s for username %s' % (authcode, args.username))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username',
                        type=str,
                        help='username for which to request an authentication code')
    args = parser.parse_args()
    main(args)
