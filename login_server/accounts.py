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
    def __init__(self, unique_id, login_name, authcode=None, password_hash=None):
        self.unique_id = unique_id
        self.login_name = login_name
        self.authcode = authcode
        self.password_hash = password_hash

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
                    unique_id = accountentry['unique_id']
                    login_name = accountentry['login_name']
                    authcode = accountentry['authcode']
                    password_hash = accountentry['password_hash']
                    if password_hash is not None:
                        password_hash = base64.b64decode(password_hash)
                    self.accounts[login_name] = AccountInfo(unique_id,
                                                            login_name,
                                                            authcode,
                                                            password_hash)
        except FileNotFoundError:
            pass

    def save(self):
        with open(self.filename, 'wt') as f:
            accountlist = []
            for accountinfo in self.accounts.values():
                password_hash = accountinfo.password_hash
                if password_hash is not None:
                    password_hash = base64.b64encode(password_hash).decode('utf-8')
                accountlist.append({
                    'unique_id' : accountinfo.unique_id,
                    'login_name' : accountinfo.login_name,
                    'authcode' : accountinfo.authcode,
                    'password_hash' : password_hash
                })
            json.dump(accountlist, f, indent = 4)

    def __getitem__(self, key):
        return self.accounts[key]

    def __contains__(self, key):
        return key in self.accounts
    
    def add_account(self, login_name, authcode):
        used_ids = {account.unique_id for account in self.accounts}
        unique_id = next(i for i, e in enumerate(sorted(used_ids) + [None], start=1) if i != e)
        self.accounts[login_name] = AccountInfo(unique_id, login_name, authcode)
