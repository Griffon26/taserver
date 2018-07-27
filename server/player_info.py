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

class PlayerInfo:
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
