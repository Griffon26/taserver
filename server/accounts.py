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

import base64
import json

class AccountInfo():
    def __init__(self, loginname, authcode=None, passwdhash=None):
        self.loginname = loginname
        self.authcode = authcode
        self.passwdhash = passwdhash

class Accounts():
    def __init__(self, filename):
        self.filename = filename
        self.accounts = {}
        self.load()

    def load(self):
        try:
            with open(self.filename, 'rt') as f:
                data = f.read()
            if data:
                accountlist = json.loads(data)
                for accountentry in accountlist:
                    loginname = accountentry['loginname']
                    authcode = accountentry['authcode']
                    passwdhash = accountentry['passwdhash']
                    if passwdhash is not None:
                        passwdhash = base64.b64decode(passwdhash)
                    self.accounts[loginname] = AccountInfo(loginname,
                                                           authcode,
                                                           passwdhash)
        except FileNotFoundError:
            pass

    def save(self):
        with open(self.filename, 'wt') as f:
            accountlist = []
            for accountinfo in self.accounts.values():
                passwdhash = accountinfo.passwdhash
                if passwdhash is not None:
                    passwdhash = base64.b64encode(passwdhash).decode('utf-8')
                accountlist.append({
                    'loginname' : accountinfo.loginname,
                    'authcode' : accountinfo.authcode,
                    'passwdhash' : passwdhash
                })
            json.dump(accountlist, f)

    def __getitem__(self, key):
        return self.accounts[key]

    def __setitem__(self, key, value):
        self.accounts[key] = value

    def __contains__(self, key):
        return key in self.accounts
    
