#!/usr/bin/env python3

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
    
