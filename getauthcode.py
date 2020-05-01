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

from common.tcpmessage import TcpMessageReader, TcpMessageWriter
from common.connectionhandler import *
from common.messages import *

server_address = ("127.0.0.1", 9800)




def main(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    writer = TcpMessageWriter(sock)
    reader = TcpMessageReader(sock)

    writer.send(Auth2LoginAuthCodeRequestMessage('getauthcode', args.username, args.email).to_bytes())
    result = parse_message_from_bytes(reader.receive())

    if not isinstance(result, Login2AuthAuthCodeResultMessage) or result.authcode is None:
        print(result.error_message)
    else:
        print(f'Received authcode {result.authcode} for username {result.login_name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username',
                        type=str,
                        help='username for which to request an authentication code')
    parser.add_argument('email',
                        type=str,
                        help='email address belonging to this user')
    args = parser.parse_args()
    main(args)
