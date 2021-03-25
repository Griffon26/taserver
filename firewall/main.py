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
import configparser
import gevent
import gevent.queue
from gevent.server import StreamServer
import gevent.subprocess as sp
import json
import logging
import os
import sys

from common.geventwrapper import gevent_spawn
from common.logging import set_up_logging
from common.ports import Ports
from common.tcpmessage import TcpMessageReader
from common.utils import get_shared_ini_path

from .utils import FirewallUtils


class Rulelist:
    def __init__(self, ports):
        self.IPs = set()
        self.ports = ports

    def has_ip(self, ip):
        return ip in self.IPs

    def add(self, ip):
        if ip not in self.IPs:
            self.IPs.add(ip)
            return True
        else:
            return False

    def remove(self, ip):
        if ip in self.IPs:
            self.IPs.remove(ip)
            return True
        else:
            return False


class Blacklist(Rulelist):

    def __init__(self, utils, logger, ports):
        super().__init__(ports)
        self.utils = utils
        self.logger = logger
        self.name = 'TAserverfirewall-blacklist'
        if self.ports.portOffset:
            self.name += f'_offset{self.ports.portOffset}'

    def remove_all(self):
        self.utils.remove_rules_by_name(self.name)

    def reset(self):
        self.logger.info('Resetting blacklist to initial state')
        self.remove_all()

        args = [
            'c:\\windows\\system32\\Netsh.exe',
            'advfirewall',
            'firewall',
            'add',
            'rule',
            'name="%s"' % self.name,
            'protocol=tcp',
            'dir=in',
            'enable=yes',
            'profile=any',
            'localport=%d' % self.ports['client2login'],
            'action=allow'
        ]
        try:
            sp.check_output(args, text = True)
        except sp.CalledProcessError as e:
            self.logger.error('Failed to add initial rule to firewall during reset of blacklist:\n'
                              '%s' % e.output)

    def add(self, ip):
        if super().add(ip):
            self.utils.add_rule(self.name, ip, self.ports['client2login'], 'tcp', 'block')

    def remove(self, ip):
        if super().remove(ip):
            self.utils.remove_rule(self.name, ip, self.ports['client2login'], 'tcp', 'block')


class Whitelist(Rulelist):

    def __init__(self, utils, logger, ports):
        super().__init__(ports)
        self.utils = utils
        self.logger = logger
        self.name = 'TAserverfirewall-whitelist'
        if self.ports.portOffset:
            self.name += f'_offset{self.ports.portOffset}'

    def remove_all(self):
        self.utils.remove_rules_by_name(self.name)

    def reset(self):
        self.logger.info('Resetting whitelist to initial state')
        self.remove_all()

    def add(self, ip):
        if super().add(ip):
            for protocol in ('udp', 'tcp'):
                self.utils.add_rule(self.name, ip, '%d,%d' % (self.ports['gameserver1'], self.ports['gameserver2']), protocol, 'allow')

    def remove(self, ip):
        if super().remove(ip):
            for protocol in ('udp', 'tcp'):
                self.utils.remove_rule(self.name, ip, '%d,%d' % (self.ports['gameserver1'], self.ports['gameserver2']), protocol, 'allow')


class Firewall:
    def __init__(self, ports, data_root):
        set_up_logging(data_root, 'taserver_firewall.log')
        self.logger = logging.getLogger('firewall')
        self.ports = ports
        self.utils = FirewallUtils(self.logger)
        self.blacklist = Blacklist(self.utils, self.logger, ports)
        self.whitelist = Whitelist(self.utils, self.logger, ports)
        self.name = 'TAserverfirewall-general'
        if self.ports.portOffset:
            self.name += f'_offset{self.ports.portOffset}'

    def remove_all_rules(self):
        self.logger.info('Removing any previous TAserverfirewall rules')
        self.utils.remove_rules_by_name(self.name)
        self.blacklist.remove_all()
        self.whitelist.remove_all()

    def run(self, server_queue):
        lists = {
            'whitelist': self.whitelist,
            'blacklist': self.blacklist
        }

        # First disable the rules that are created by Windows itself when you run tribesascend.exe
        tribes_ascend_programs = set(rule['Program'] for rule in self.utils.find_tribes_ascend_rules())
        for program in tribes_ascend_programs:
            self.utils.disable_rules_for_program_name(program)

        self.utils.add_rule(self.name, 'any', self.ports['launcher2login'], 'tcp', 'allow') # for game servers
        self.utils.add_rule(self.name, 'any', self.ports['restapi'], 'tcp', 'allow') # for REST
        self.utils.add_rule(self.name, 'any', self.ports['launcherping'], 'udp', 'allow') # for in-game pings
        self.whitelist.reset()
        self.blacklist.reset()

        while True:
            command = server_queue.get()
            thelist = lists[command['list']]

            if command['action'] == 'reset':
                thelist.reset()
            elif command['action'] == 'add':
                ip = command['ip']
                thelist.add(ip)
            elif command['action'] == 'remove':
                ip = command['ip']
                thelist.remove(ip)
            else:
                self.logger.error('Invalid action received: %s' % command['action'])


def main():
    print('Running on Python %s' % sys.version)
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', action='store', default='data',
                        help='Location of the data dir containing all config files and logs.')
    args = parser.parse_args()
    data_root = args.data_root

    config = configparser.ConfigParser()
    with open(get_shared_ini_path(data_root)) as f:
        config.read_file(f)

    ports = Ports(int(config['shared']['port_offset']))

    try:
        udp_proxy_proc1 = sp.Popen('udpproxy.exe %d' % ports['gameserver1'])
        udp_proxy_proc2 = sp.Popen('udpproxy.exe %d' % ports['gameserver2'])

    except OSError as e:
        print('Failed to run udpproxy.exe. Run download_udpproxy.py to download it\n'
              'or build it yourself using the Visual Studio solution in the udpproxy\n'
              'subdirectory and place it in the taserver directory.\n',
              file=sys.stderr)
        return

    server_queue = gevent.queue.Queue()
    firewall = Firewall(ports, data_root)
    gevent_spawn('firewall.run', firewall.run, server_queue)

    def handle_client(socket, address):
        msg = TcpMessageReader(socket).receive()
        command = json.loads(msg.decode('utf8'))
        server_queue.put(command)

    server = StreamServer(('127.0.0.1', ports['firewall']), handle_client)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        firewall.remove_all_rules()

    udp_proxy_proc1.terminate()
    udp_proxy_proc2.terminate()
