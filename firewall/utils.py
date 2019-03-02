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

import gevent.subprocess as sp


class FirewallUtils:
    def __init__(self, logger):
        self.logger = logger

    def remove_rules_by_name(self, name):
        args = [
            'c:\\windows\\system32\\Netsh.exe',
            'advfirewall',
            'firewall',
            'delete',
            'rule',
            'name=%s' % name
        ]
        # Don't check for failure here, because it is expected to
        # fail if there are no left-over rules from a previous run.
        sp.call(args, stdout=sp.DEVNULL)

    def remove_rule(self, name, ip, port, protocol, allow_or_block):
        self.logger.info('remove %sing firewall rule for %s to %s port %s' %
                         (allow_or_block, ip, protocol, port))

        args = [
            'c:\\windows\\system32\\Netsh.exe',
            'advfirewall',
            'firewall',
            'delete',
            'rule',
            'name=%s' % name,
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

    def add_rule(self, name, ip, port, protocol, allow_or_block):
        self.logger.info('add %sing firewall rule for %s to %s port %s' %
                         (allow_or_block, ip, protocol, port))

        if allow_or_block not in ('allow', 'block'):
            raise RuntimeError('Invalid argument provided: %s' % allow_or_block)


        args = [
            'c:\\windows\\system32\\Netsh.exe',
            'advfirewall',
            'firewall',
            'add',
            'rule',
            'name=%s' % name,
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

    def find_tribes_ascend_rules(self):
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

        ta_rules = []
        for line in output.splitlines():
            if line.startswith('Rule Name:'):
                newrule = {}
            elif ':' in line:
                key, value = line.split(':', maxsplit=1)
                key = key.strip()
                value = value.strip()

                newrule[key] = value

                if key == 'Program' and value.lower().endswith('tribesascend.exe'):
                    ta_rules.append(newrule)

        return ta_rules

    def disable_rules_for_program_name(self, programname):
        args = [
            'c:\\windows\\system32\\Netsh.exe',
            'advfirewall',
            'firewall',
            'set',
            'rule',
            'name=all',
            'dir=in',
            'program=%s' % programname,
            'new',
            'enable=no'
        ]

        try:
            self.logger.info('Disabling rule for %s' % programname)
            sp.check_output(args, text = True)
        except sp.CalledProcessError as e:
            self.logger.error('Failed to remove firewall rules for program %s. Output:\n%s' %
                              (programname, e.output))

