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
import gevent
import gevent.queue
from gevent.server import StreamServer
import gevent.subprocess as sp
import json
import re

from common.tcpmessage import TcpMessageReader

# Unused for now, but it'll need to move to the login server
'''
whitelistfilename = 'firewallwhitelist.txt'

def readiplist(filename):
    iplist = set()
    
    with open(filename, 'rt') as f:
        for line in f:
            line = line.strip()

            match = re.match('\d+\.\d+\.\d+\.\d+', line)
            if match:
                try:
                    ipparts = tuple(int(x) for x in line.split('.'))
                    if not all(0 <= p <= 255 for p in ipparts):
                        raise RuntimeError('Not a valid IP')

                    iplist.add(ipparts)
                
                except RuntimeError:
                    pass

    return iplist

def writeiplist(filename, iplist):
    with open(filename, 'wt') as f:
        for ip in sorted(iplist):
            f.write('%d.%d.%d.%d\n' % ip)
'''


def removeallrules():
    print('Removing any previous TAserverfirewall rules')
    for name in ('TAserverfirewall-blacklist',
                 'TAserverfirewall-whitelist',
                 'TAserverfirewall-general'):
        args = [
            'c:\\windows\\system32\\Netsh.exe',
            'advfirewall',
            'firewall',
            'delete',
            'rule',
            'name="%s"' % name
        ]
        # Don't check for failure here, because it is expected to
        # fail if there are no left-over rules from a previous run.
        sp.call(args, stdout=sp.DEVNULL)


def reset_whitelist():
    print('Resetting TAserverfirewall whitelist to initial state')
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'delete',
        'rule',
        'name="TAserverfirewall-whitelist"'
    ]
    # Don't check for failure here, because it is expected to
    # fail if there are no left-over rules from a previous run.
    sp.call(args, stdout=sp.DEVNULL)


def reset_blacklist():
    print('Resetting TAserverfirewall blacklist to initial state')
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'delete',
        'rule',
        'name="TAserverfirewall-blacklist"'
    ]
    # Don't check for failure here, because it is expected to
    # fail if there are no left-over rules from a previous run.
    sp.call(args, stdout=sp.DEVNULL)

    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'add',
        'rule',
        'name="TAserverfirewall-blacklist"',
        'protocol=tcp',
        'dir=in',
        'enable=yes',
        'profile=any',
        'localport=9000',
        'action=allow'
    ]
    try:
        sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to add initial rule to firewall during reset of blacklist:\n%s' % e.output)


def createinitialrules():
    print('Adding initial set of TAserverfirewall rules')

    # The only initial rules we need are a allow rules for
    # the login server for both clients and game servers
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'add',
        'rule',
        'name="TAserverfirewall-blacklist"',
        'protocol=tcp',
        'dir=in',
        'enable=yes',
        'profile=any',
        'localport=9000',
        'action=allow'
    ]
    try:
        sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to add initial rule to firewall:\n%s' % e.output)

    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'add',
        'rule',
        'name="TAserverfirewall-general"',
        'protocol=tcp',
        'dir=in',
        'enable=yes',
        'profile=any',
        'localport=9001',
        'action=allow'
    ]
    try:
        sp.check_output(args, text=True)
    except sp.CalledProcessError as e:
        print('Failed to add initial rule to firewall:\n%s' % e.output)


def removerule(name, ip, port, protocol):
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'delete',
        'rule',
        'name="%s"' % name,
        'protocol=%s' % protocol,
        'dir=in',
        'profile=any',
        'localport=%d' % port,
        'remoteip=%s' % ip
    ]
    try:
        sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to remove rule from firewall:\n%s' % e.output)


def addrule(name, ip, port, protocol, allow_or_block):
    if allow_or_block not in ('allow', 'block'):
        raise RuntimeError('Invalid argument provided: %s' % allow_or_block)
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'add',
        'rule',
        'name="%s"' % name,
        'protocol=%s' % protocol,
        'dir=in',
        'enable=yes',
        'profile=any',
        'localport=%d' % port,
        'action=%s' % allow_or_block,
        'remoteip=%s' % ip
    ]
    try:
        sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to add rule to firewall:\n%s' % e.output)


def findtribesascendrules():
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'show',
        'rule',
        'name=all',
        'dir=in',
        'status=enabled',
        'verbose'
    ]
    try:
        output = sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to request firewall rules.')
        output = ''

    tarules = []
    for line in output.splitlines():
        if line.startswith('Rule Name:'):
            newrule = {}
        elif ':' in line:
            key, value = line.split(':', maxsplit=1)
            key = key.strip()
            value = value.strip()
            
            newrule[key] = value

            if key == 'Program' and value.lower().endswith('tribesascend.exe'):
                tarules.append(newrule)

    return tarules


def disablerulesforprogramname(programname):
    args = [
        'c:\\windows\\system32\\Netsh.exe',
        'advfirewall',
        'firewall',
        'set',
        'rule',
        'name=all',
        'dir=in',
        'program="%s"' % programname,
        'new',
        'enable=no'
    ]
    
    try:
        print('Disabling rule for %s' % programname)
        sp.check_output(args, text = True)
    except sp.CalledProcessError as e:
        print('Failed to remove firewall rules for program %s. Output:\n%s' %
              (programname, e.output))


def handle_server(server_queue):
    lists = {
        'whitelist' : {
            'name' : 'TAserverfirewall-whitelist',
            'ruletype' : 'allow',
            'port' : 7777,
            'protocol' : 'udp',
            'IPs' : set(),
        },
        'blacklist' : {
            'name' : 'TAserverfirewall-blacklist',
            'ruletype' : 'block',
            'port' : 9000,
            'protocol' : 'tcp',
            'IPs' : set()
        }
    }

    # First disable the rules that are created by Windows itself when you run tribesascend.exe
    tribesascendprograms = set(rule['Program'] for rule in findtribesascendrules())
    for program in tribesascendprograms:
        disablerulesforprogramname(program)

    removeallrules()
    createinitialrules()
    
    while True:
        command = server_queue.get()
        thelist = lists[command['list']]

        if command['action'] == 'reset':
            if command['list'] == 'whitelist':
                reset_whitelist()
            else:
                reset_blacklist()
        elif command['action'] == 'add':
            ip = command['ip']
            if ip not in thelist['IPs']:
                print('add %sing firewall rule for %s to %s port %d' %
                      (thelist['ruletype'], ip, thelist['protocol'], thelist['port']))
                thelist['IPs'].add(ip)
                addrule(thelist['name'], ip, thelist['port'], thelist['protocol'], thelist['ruletype'])
        elif command['action'] == 'remove':
            ip = command['ip']
            if ip in thelist['IPs']:
                print('remove %sing firewall rule for %s to %s port %d' %
                      (thelist['ruletype'], ip, thelist['protocol'], thelist['port']))
                thelist['IPs'].remove(ip)
                removerule(thelist['name'], ip, thelist['port'], thelist['protocol'])


def main(args):
    server_queue = gevent.queue.Queue()
    
    gevent.spawn(handle_server, server_queue)

    def handle_client(socket, address):
        msg = TcpMessageReader(socket).receive()
        command = json.loads(msg.decode('utf8'))
        server_queue.put(command)

    server = StreamServer(('127.0.0.1', 9801), handle_client)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        removeallrules()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)

