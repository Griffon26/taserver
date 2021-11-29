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
import sys

from common.geventwrapper import gevent_spawn
from common.ports import Ports
from common.tcpmessage import TcpMessageReader
from common.utils import get_shared_ini_path

from .windows_firewall import Firewall
from .iptables_firewall import IPTablesFirewall


def main():
    print('Running on Python %s' % sys.version)
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', action='store', default='data',
                        help='Location of the data dir containing all config files and logs.')
    parser.add_argument('--port-offset', action='store', default=None,
                        help='Override port offset in the config')
    args = parser.parse_args()
    data_root = args.data_root

    config = configparser.ConfigParser()
    with open(get_shared_ini_path(data_root)) as f:
        config.read_file(f)

    if args.port_offset is not None:
        print(f"Using port offset flag: {int(args.port_offset)}")
        ports = Ports(int(args.port_offset))
    else:
        ports = Ports(int(config['shared']['port_offset']))
    use_iptables = config['shared'].getboolean('use_iptables', False)
    udpproxy_enabled = not use_iptables

    if udpproxy_enabled:
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
    
    if use_iptables:
        firewall = IPTablesFirewall(ports, data_root)
    else:
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

    if udpproxy_enabled:
        udp_proxy_proc1.terminate()
        udp_proxy_proc2.terminate()
