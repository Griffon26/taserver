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


class PlayerState:
    def __init__(self, player):
        self.player = player

    def handle_request(self, request):
        methods = [
            func for name, func in inspect.getmembers(self) if
            not name.startswith("__")
            and hasattr(func, "handler")
            and isinstance(request, func.packet)
        ]
        for method in methods:
            method(request)

    def on_enter(self):
        print("%s is entering state %s" % (self.player, self))

    def on_exit(self):
        print("%s is exiting state %s" % (self.player, self))
