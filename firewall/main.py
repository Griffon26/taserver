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

import gevent
import gevent.queue
from gevent.server import StreamServer
import gevent.subprocess as sp
import json
import logging
import sys

from common.logging import set_up_logging
from common.tcpmessage import TcpMessageReader

GAME_PORT1 = 7777
GAME_PORT2 = 7778


class Firewall():
    def __init__(self):
        set_up_logging('taserver_firewall.log')
        self.logger = logging.getLogger('firewall')

    def removeallrules(self):
        self.logger.info('Removing any previous TAserverfirewall rules')
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


    def reset_whitelist(self):
        self.logger.info('Resetting TAserverfirewall whitelist to initial state')
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

    def reset_tcp_whitelist(self):
        self.logger.info('Resetting TAserverfirewall TCP whitelist to initial state')
        args = [
            'c:\\windows\\system32\\Netsh.exe',
            'advfirewall',
            'firewall',
            'delete',
            'rule',
            'name="TAserverfirewall-whitelist-tcp"'
        ]
        # Don't check for failure here, because it is expected to
        # fail if there are no left-over rules from a previous run.
        sp.call(args, stdout=sp.DEVNULL)

    def reset_blacklist(self):
        self.logger.info('Resetting TAserverfirewall blacklist to initial state')
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
            self.logger.error('Failed to add initial rule to firewall during reset of blacklist:\n%s' % e.output)


    def createinitialrules(self):
        self.logger.info('Adding initial set of TAserverfirewall rules')

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
            self.logger.error('Failed to add initial rule to firewall:\n%s' % e.output)

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
            self.logger.error('Failed to add initial rule to firewall:\n%s' % e.output)

    def removerule(self, name, ip, port, protocol):
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
            'localport=%s' % port,
            'remoteip=%s' % ip
        ]
        try:
            sp.check_output(args, text = True)
        except sp.CalledProcessError as e:
            self.logger.error('Failed to remove rule from firewall:\n%s' % e.output)

    def addrule(self, name, ip, port, protocol, allow_or_block):
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
            'localport=%s' % port,
            'action=%s' % allow_or_block,
            'remoteip=%s' % ip
        ]
        try:
            sp.check_output(args, text = True)
        except sp.CalledProcessError as e:
            self.logger.error('Failed to add rule to firewall:\n%s' % e.output)


    def findtribesascendrules(self):
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
            self.logger.error('Failed to request firewall rules.')
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


    def disablerulesforprogramname(self, programname):
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
            self.logger.info('Disabling rule for %s' % programname)
            sp.check_output(args, text = True)
        except sp.CalledProcessError as e:
            self.logger.error('Failed to remove firewall rules for program %s. Output:\n%s' %
                              (programname, e.output))


    def run(self, server_queue):
        lists = {
            'whitelist' : {
                'name' : 'TAserverfirewall-whitelist',
                'ruletype' : 'allow',
                'port' : '%d,%d' % (GAME_PORT1, GAME_PORT2),
                'protocol' : 'udp',
                'IPs' : list(),
            },
            'blacklist' : {
                'name' : 'TAserverfirewall-blacklist',
                'ruletype' : 'block',
                'port' : 9000,
                'protocol' : 'tcp',
                'IPs' : list()
            },
            'whitelist-tcp' : {
                'name': 'TAserverfirewall-whitelist-tcp',
                'ruletype': 'allow',
                'port': '%d,%d' % (GAME_PORT1, GAME_PORT2),
                'protocol': 'tcp',
                'IPs': list(),
            }
        }

        # First disable the rules that are created by Windows itself when you run tribesascend.exe
        tribesascendprograms = set(rule['Program'] for rule in self.findtribesascendrules())
        for program in tribesascendprograms:
            self.disablerulesforprogramname(program)

        self.removeallrules()
        self.createinitialrules()

        while True:
            command = server_queue.get()
            thelist = lists[command['list']]

            if command['action'] == 'reset':
                if command['list'] == 'whitelist':
                    self.reset_whitelist()
                elif command['list'] == 'whitelist-tcp':
                    self.reset_tcp_whitelist()
                else:
                    self.reset_blacklist()
                thelist['IPs'] = list()
            elif command['action'] == 'add':
                ip = command['ip']
                if ip not in thelist['IPs']:
                    ip_is_new = ip not in thelist['IPs']
                    thelist['IPs'].append(ip)
                    if ip_is_new:
                        self.logger.info('add %sing firewall rule for %s to %s port %s' %
                                         (thelist['ruletype'], ip, thelist['protocol'],
                                          thelist['port']))
                        self.addrule(thelist['name'], ip, thelist['port'], thelist['protocol'], thelist['ruletype'])
            elif command['action'] == 'remove':
                ip = command['ip']
                if ip in thelist['IPs']:
                    thelist['IPs'].remove(ip)
                    if ip not in thelist['IPs']:
                        self.logger.info('remove %sing firewall rule for %s to %s port %s' %
                                         (thelist['ruletype'], ip, thelist['protocol'],
                                          thelist['port']))
                        self.removerule(thelist['name'], ip, thelist['port'], thelist['protocol'])
            elif command['action'] == 'removeall':
                ip = command['ip']
                if ip in thelist['IPs']:
                    thelist['IPs'] = [x for x in thelist['IPs'] if x != ip]
                    self.logger.info('remove %sing firewall rule for %s to %s port %s' %
                                     (thelist['ruletype'], ip, thelist['protocol'],
                                      thelist['port']))
                    self.removerule(thelist['name'], ip, thelist['port'], thelist['protocol'])


def main():
    try:
        udp_proxy_proc1 = sp.Popen('udpproxy.exe %d' % GAME_PORT1)
        udp_proxy_proc2 = sp.Popen('udpproxy.exe %d' % GAME_PORT2)

    except OSError as e:
        print('Failed to run udpproxy.exe. Run download_udpproxy.py to download it\n'
              'or build it yourself using the Visual Studio solution in the udpproxy\n'
              'subdirectory and place it in the taserver directory.\n',
              file=sys.stderr)
        return

    server_queue = gevent.queue.Queue()
    firewall = Firewall()
    gevent.spawn(firewall.run, server_queue)

    def handle_client(socket, address):
        msg = TcpMessageReader(socket).receive()
        command = json.loads(msg.decode('utf8'))
        server_queue.put(command)

    server = StreamServer(('127.0.0.1', 9801), handle_client)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        firewall.removeallrules()

    udp_proxy_proc1.terminate()
    udp_proxy_proc2.terminate()
