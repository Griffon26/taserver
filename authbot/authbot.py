#!/usr/bin/env python3
#
# Copyright (C) 2019  Maurice van der Pot <griffon26@kfk4ever.com>
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

import base64
from common.ipaddresspair import IPAddressPair
from email.message import EmailMessage
from functools import wraps
import gevent
import inspect
import itertools
import json
import logging
import re
import smtplib
import time
import urllib.request as urlreq

from common.datatypes import *
from common.errors import FatalError, MajorError
from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage
from common.loginprotocol import LoginProtocolMessage
from common.messages import *
from common.statetracer import statetracer

from .communityloginserverhandler import CommunityLoginServer
from .hirezloginserverhandler import HirezLoginServer

SOURCE_HIREZ = 'hirez'
SOURCE_COMMUNITY = 'community'


class LoginFailedError(MajorError):
    def __init__(self):
        super().__init__('Failed to login with the specified credentials. This can happen if the Hirez server has been down. If that is not the case, check the credentials in authbot.ini')


class NoPublicIpAddressError(FatalError):
    def __init__(self, error):
        super().__init__(f'Failed to detect the public IP address: {error}. Authbot refuses to start up without it, because it needs this IP address when sending verification mail.')


def handles(packet):
    """
    A decorator that defines a function as a handler for a certain packet
    :param packet: the packet being handled by the function
    """

    def real_decorator(func):
        func.handles_packet = packet

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return real_decorator


def xor_password_hash(password_hash, salt):
    salt_nibbles = []
    for value in salt:
        salt_nibbles.append(value >> 4)
        salt_nibbles.append(value & 0x0F)

    xor_values = [(value if value <= 9 else 0x47 + value) for value in salt_nibbles]

    xor_pattern = [
        xor_values[6], 0,
        xor_values[7], 0,
        xor_values[4], 0,
        xor_values[5], 0,
        xor_values[2], 0,
        xor_values[3], 0,
        xor_values[0], 0,
        xor_values[1], 0,
        0, 0,
        xor_values[10], 0,
        xor_values[11], 0,
        xor_values[8], 0,
        xor_values[9], 0,
        0, 0,
        xor_values[14], 0,
        xor_values[15], 0,
        xor_values[12], 0,
        xor_values[13], 0,
        0, 0,
        xor_values[16], 0,
        xor_values[17], 0,
        xor_values[18], 0,
        xor_values[19], 0,
        0, 0,
        xor_values[20], 0,
        xor_values[21], 0,
        xor_values[22], 0,
        xor_values[23], 0,
        xor_values[24], 0,
        xor_values[25], 0,
        xor_values[26], 0,
        xor_values[27], 0,
        xor_values[28], 0,
        xor_values[29], 0,
        xor_values[30], 0,
        xor_values[31], 0,
    ]

    xored_password_hash = [
        p ^ x for p, x in itertools.zip_longest(password_hash, xor_pattern, fillvalue = 0)
    ]

    return bytes(xored_password_hash)


@statetracer()
class AuthBot:
    def __init__(self, config, incoming_queue):
        gevent.getcurrent().name = 'authbot'

        self.logger = logging.getLogger(__name__)
        self.incoming_queue = incoming_queue
        self.community_login_server = None
        self.hirez_login_server = None
        self.login_name = config['login_name']
        self.display_name = None
        self.password_hash = base64.b64decode(config['password_hash'])
        self.last_requests = {}

        self.smtp_server = config['smtp_server']
        self.smtp_port = int(config['smtp_port'])
        self.smtp_user = config['smtp_user']
        self.smtp_password = config['smtp_password']
        self.smtp_sender = config['smtp_sender']
        self.smtp_usetls = config.getboolean('smtp_usetls')

        self.message_handlers = {
            PeerConnectedMessage: self.handle_peer_connected,
            PeerDisconnectedMessage: self.handle_peer_disconnected,
            Login2AuthAuthCodeResultMessage: self.handle_authcode_result_message,
            Login2AuthChatMessage: self.handle_auth_channel_chat_message,
            LoginProtocolMessage: self.handle_login_protocol_message,
        }

        address_pair, errormsg = IPAddressPair.detect()
        if not address_pair.external_ip:
            raise NoPublicIpAddressError(errormsg)
        else:
            self.logger.info('authbot: detected external IP: %s' % address_pair.external_ip)
        self.login_server_address = address_pair.external_ip

    def run(self):
        self.send_and_schedule_keepalive_message()
        while True:
            for message in self.incoming_queue:
                handler = self.message_handlers[type(message)]
                handler(message)

    def send_and_schedule_keepalive_message(self):
        if self.hirez_login_server and self.display_name:
            self.hirez_login_server.send(
                a01c8().set([
                    m068b().set([])
                ])
            )
        gevent.spawn_later(30, self.send_and_schedule_keepalive_message)

    def send_reply_message_via_hirez_server(self, who, what):
        self.hirez_login_server.send(
            a0070().set([
                m009e().set(MESSAGE_PRIVATE),
                m02e6().set(what),
                m034a().set(who),
                m0574()
            ])
        )

    def send_reply_message_via_auth_channel(self, who, what):
        self.community_login_server.send(Auth2LoginChatMessage(who, what))

    def send_reply_message(self, source, who, what):
        if source == SOURCE_HIREZ:
            self.send_reply_message_via_hirez_server(who, what)
        else:
            self.send_reply_message_via_auth_channel(who, what)

    def handle_peer_connected(self, msg):
        if isinstance(msg.peer, HirezLoginServer):
            assert self.hirez_login_server is None
            self.logger.info('authbot: connected to hirez login server')
            self.hirez_login_server = msg.peer
            self.hirez_login_server.send(
                a01bc().set([
                    m049e(),
                    m0489()
                ])
            )
        elif isinstance(msg.peer, CommunityLoginServer):
            assert self.community_login_server is None
            self.logger.info('authbot: connected to community login server')
            self.community_login_server = msg.peer
            self.community_login_server.send(Auth2LoginRegisterAsBotMessage())
        else:
            pass

    def handle_peer_disconnected(self, msg):
        if isinstance(msg.peer, HirezLoginServer):
            assert self.hirez_login_server is msg.peer
            msg.peer.disconnect()
            self.logger.info('authbot: hirez login server disconnected')
            self.hirez_login_server = None
        elif isinstance(msg.peer, CommunityLoginServer):
            assert self.community_login_server is msg.peer
            msg.peer.disconnect()
            self.logger.info('authbot: community login server disconnected')
            self.community_login_server = None
        else:
            pass

    def send_authcode_email(self, recipient, login_name, authcode):
        masked_recipient = ''.join([c if (i == 0 or c in '@.' or recipient[i - 1] in '@.') else '*' for i, c in enumerate(recipient)])
        msg = EmailMessage()
        msg['Subject'] = 'taserver verification mail'
        msg['From'] = self.smtp_sender
        msg['To'] = recipient
        msg.set_content(f"We have received a request to send an authentication code to this email address for \n"
                        f"user '{login_name}' on the taserver installation running at {self.login_server_address}.\n"
                        f"\n"
                        f"If you requested this code, please connect to the login server mentioned above \n"
                        f"and login as '{login_name}' with a password of your choosing. After logging in \n"
                        f"go to the 'Store' menu, select 'Redeem promotion' and type in the following code:\n"
                        f"\n"
                        f"  {authcode}\n"
                        f"\n"
                        f"Your account will be verified once you have restarted and logged in again with the \n"
                        f"same name and password.\n"
                        f"\n"
                        f"If you did NOT request an authentication code then you can safely ignore this message.\n"
                        f"\n")

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.smtp_usetls:
                server.ehlo()
                server.starttls()
                server.ehlo()
            if self.smtp_user != '':
                server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.close()
        except Exception as e:
            self.logger.error(f'authbot: failed to send verification mail to {masked_recipient} for user {login_name}: {str(e)}')
        else:
            self.logger.info(f'authbot: successfully sent verification mail to {masked_recipient} for user {login_name}')

    def handle_authcode_result_message(self, msg):
        if msg.authcode:
            self.send_authcode_email(msg.email_address, msg.login_name, msg.authcode)
        else:
            self.logger.error(f'authbot: failed to acquire authcode from login server for {msg.login_name}: {msg.error_message}')

    def looks_like_email_address(self, text):
        return re.match(r'.*@.*\..*', text)

    def handle_chat_helper(self, source, login_name, verified, message_text):

        self.last_requests = {k: v for k, v in self.last_requests.items() if time.time() - v < 5}

        message_words = message_text.split()
        if len(message_words) == 2 and message_words[0] == 'authcode':
            email_address = message_words[1]
            if self.looks_like_email_address(email_address):

                if login_name in self.last_requests:
                    self.send_reply_message(source, login_name, 'Jeez.. I just gave you an authcode five seconds ago! Stop being so pushy!')
                else:
                    self.last_requests[login_name] = time.time()
                    self.community_login_server.send(Auth2LoginAuthCodeRequestMessage(source, login_name, email_address))
                    self.send_reply_message(source, login_name,
                                            'Your authcode request has been processed. If the specified email address '
                                            'was valid for the account, an email has been sent with an authcode.')
            else:
                self.send_reply_message(source, login_name, f'{email_address} does not look like an email address.')

        elif len(message_words) == 1 and message_words[0] == 'status':
            server_info = json.loads(urlreq.urlopen('http://localhost:9080/status').read())

            try:
                self.send_reply_message(source, login_name, 'There are %s players and %s servers online' %
                                                            (server_info['online_players'],
                                                             server_info['online_servers']))
            except KeyError as e:
                self.logger.error('authbot: invalid status received from server: %s' % e)
                self.send_reply_message(source, login_name, 'Something went wrong. Please contact the administrator '
                                                            'of this bot or try again later.')

        elif source == SOURCE_COMMUNITY and len(message_words) == 2 and message_words[0] == 'setemail':
            email_address = message_words[1]
            if not verified:
                self.send_reply_message(source, login_name,
                                        'You cannot change your email address unless you are verified.')
            elif self.looks_like_email_address(email_address):
                self.community_login_server.send(Auth2LoginSetEmailMessage(login_name, email_address))
                self.send_reply_message(source, login_name,
                                        f'The email address for user {login_name} has been updated to {email_address}.')
            else:
                self.send_reply_message(source, login_name, f'{email_address} does not look like an email address.')

        else:
            setemail_command =  ', "setemail <email>"' if source == SOURCE_COMMUNITY else ''
            self.send_reply_message(source, login_name, f'Hi {login_name}. Valid commands are "authcode <email>"{setemail_command} and "status".')

    def handle_auth_channel_chat_message(self, msg):
        self.handle_chat_helper(SOURCE_COMMUNITY, msg.login_name, msg.verified, msg.text)

    def handle_login_protocol_message(self, msg):
        msg.peer.last_received_seq = msg.clientseq

        requests = ' '.join(['%04X' % req.ident for req in msg.requests])

        for request in msg.requests:
            methods = [
                func for name, func in inspect.getmembers(self) if
                getattr(func, 'handles_packet', None) == type(request)
            ]
            if not methods:
                self.logger.warning("No handler found for request %s" % request)
                return

            if len(methods) > 1:
                raise ValueError("Duplicate handlers found for request")

            methods[0](request)

    @handles(packet=a01bc)
    def handle_a01bc(self, request):
        pass

    @handles(packet=a0197)
    def handle_a0197(self, request):
        self.hirez_login_server.send(a003a())

    @handles(packet=a003a)
    def handle_a003a(self, request):
        salt = request.findbytype(m03e3).value
        self.hirez_login_server.send(
            a003a().set([
                m0056().set(xor_password_hash(self.password_hash, salt)),
                m0494().set(self.login_name),
                m0671(),
                m0671(),
                m0672(),
                m0673(),
                m0677(),
                m0676(),
                m0674(),
                m0675(),
                m0434(),
                m049e()
            ])
        )

    @handles(packet=a003d)
    def handle_a003d(self, request):
        display_name_field = request.findbytype(m034a)
        if display_name_field:
            self.display_name = display_name_field.value
        else:
            self.logger.info('authbot: login to HiRez server failed.')
            raise LoginFailedError()

    @handles(packet=a0070)
    def handle_hirez_server_chat_message(self, request):
        assert self.display_name is not None

        message_type = request.findbytype(m009e).value
        message_text = request.findbytype(m02e6).value
        sender_name = request.findbytype(m02fe).value

        if message_type == MESSAGE_PRIVATE and sender_name != self.display_name:
            self.handle_chat_helper(SOURCE_HIREZ, sender_name, False, message_text)

    @handles(packet=a011b)
    def handle_edit_friend_list(self, request):
        # Ignore any friend activity to minimize logging of unhandled messages
        pass

    @handles(packet=a0145)
    def handle_player_server_update(self, request):
        # Ignore any update from friends about which server/map they are playing
        pass


def handle_authbot(config, incoming_queue):
    authbot = AuthBot(config, incoming_queue)
    # launcher.trace_as('authbot')
    authbot.run()
