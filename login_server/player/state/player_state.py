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

import inspect
import logging
from functools import wraps

from common.datatypes import *
from common.messages import Message
from ..player import Player


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


def handles_control_message(messageType):
    """
    A decorator that defines a function as a handler for a certain control message
    sent by the player to the login server
    :param messageType: the type of control message this function handles
    """

    def real_decorator(func):
        func.handles_message = messageType

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    return real_decorator


class PlayerState:
    def __init__(self, player: Player):
        self.logger = logging.getLogger(__name__)
        self.player = player

    def handle_request(self, request):
        methods = [
            func for name, func in inspect.getmembers(self) if
            getattr(func, 'handles_packet', None) == type(request)
        ]
        if not methods:
            self.logger.warning("No handler found for request %s" % request)
            return False

        if len(methods) > 1:
            raise ValueError("Duplicate handlers found for request")

        return methods[0](request)

    def handle_control_message(self, message: Message):
        methods = [
            func for name, func in inspect.getmembers(self) if
            getattr(func, 'handles_message', None) == type(message)
        ]
        if not methods:
            self.logger.warning("No handler found for control message %s" % str(message))
            return

        if len(methods) > 1:
            raise ValueError("Duplicate handlers found for control message")

        methods[0](message)

    @handles(packet=a01c8)
    def handle_ping(self, request):
        self.player.activity_since_last_check = True
        for arr in request.findbytype(m068b).arrays:
            region = findbytype(arr, m0448).value
            ping = findbytype(arr, m053d).value
            self.player.pings[region] = ping
        return True

    def on_enter(self):
        self.logger.info("%s is entering state %s" % (self.player, type(self).__name__))

    def on_exit(self):
        self.logger.info("%s is exiting state %s" % (self.player, type(self).__name__))


