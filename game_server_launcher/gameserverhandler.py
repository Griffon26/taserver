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

import ctypes.wintypes
import gevent
import gevent.subprocess as sp
import logging
import os
import time

from .inject import inject
from common.errors import FatalError
from common.geventwrapper import gevent_spawn


class ConfigurationError(FatalError):
    def __init__(self, message):
        super().__init__('Configuration error: %s' % message)


class StartGameServerMessage:
    def __init__(self, server):
        self.server = server


class StopGameServerMessage:
    def __init__(self, server):
        self.server = server


class FreezeGameServerMessage:
    def __init__(self, server):
        self.server = server


class UnfreezeGameServerMessage:
    def __init__(self, server):
        self.server = server


class GameServerTerminatedMessage:
    def __init__(self, server):
        self.server = server


class GameServerHandler:

    def __init__(self, game_server_config, ports, server_handler_queue, launcher_queue, data_root):
        gevent.getcurrent().name = 'gameserver'

        self.servers = {}

        self.server_handler_queue = server_handler_queue
        self.launcher_queue = launcher_queue

        self.logger = logging.getLogger(__name__)
        self.ports = ports
        self.data_root = data_root

        try:
            self.working_dir = game_server_config['dir']
            self.dll_to_inject = game_server_config['controller_dll']
            self.dll_config_path = os.path.join(data_root, game_server_config['controller_config'])

            if game_server_config.get('use_external_port'):
                self.use_external_port = game_server_config.getboolean('use_external_port')
            else:
                self.use_external_port = False

        except KeyError as e:
            raise ConfigurationError("%s is a required configuration item under [gameserver]" % str(e))

        self.exe_path = os.path.join(self.working_dir, 'TribesAscend.exe')

        if not os.path.exists(self.working_dir):
            raise ConfigurationError(
                "Invalid 'dir' specified under [gameserver]: the directory does not exist")
        if not os.path.exists(self.exe_path):
            raise ConfigurationError(
                "Invalid 'dir' specified under [gameserver]: the specified directory does not contain a TribesAscend.exe")

        if not os.path.isabs(self.dll_to_inject):
            self.dll_to_inject = os.path.abspath(self.dll_to_inject)
        if not os.path.isabs(self.dll_config_path):
            self.dll_config_path = os.path.abspath(self.dll_config_path)
        self.logger.info(f'gameserver: path to controller DLL is {self.dll_to_inject}')
        self.logger.info(f'gameserver: path to controller configuration is {self.dll_config_path}')

        if not os.path.exists(self.dll_to_inject):
            raise ConfigurationError(
                "Invalid 'controller_dll' specified under [gameserver]: the specified file does not exist.")
        if not os.path.exists(self.dll_config_path):
            raise ConfigurationError(
                "Invalid 'controller_config' specified under [gameserver]: the specified file does not exist")


    def wait_until_file_contains_string(self, filename, string, timeout = 0):
        i = 0
        period = 3
        while not timeout or (i < timeout / period):
            try:
                with open(filename, 'rt') as f:
                    if string in f.read():
                        return True
                    gevent.sleep(period)
            except FileNotFoundError:
                gevent.sleep(period)
            i += 1
        return False

    def server_process_watcher(self, process, server):
        self.logger.info(f'{server}: starting server process watcher')
        process.wait()
        if server in self.servers:
            self.logger.info(f'{server}: server with pid {process.pid} terminated, notifying launcher')
            del self.servers[server]
            self.launcher_queue.put(GameServerTerminatedMessage(server))

    def start_server_process(self, server):
        external_port = self.ports[server]

        if self.use_external_port:
            # udpproxy is disabled, so listen directly on the port
            internal_port = external_port
        else:
            # Add 100 to the port, because it's the udpproxy that's actually listening on the port itself
            # and it forwards traffic to port + 100
            internal_port = self.ports[f'{server}proxy']

        log_filename = os.path.join(self.data_root, 'logs', 'tagameserver%d.log' % external_port)

        try:
            self.logger.info(f'{server}: removing previous log file {log_filename}')
            os.remove(log_filename)
        except FileNotFoundError:
            pass

        self.logger.info(f'{server}: starting a new TribesAscend server on port {external_port}...')
        args = [self.exe_path, 'server',
                '-abslog=%s' % os.path.abspath(log_filename),
                '-port=%d' % internal_port,
                '-controlport', str(self.ports['game2launcher'])]
        if self.dll_config_path is not None:
            args.extend(['-tamodsconfig', self.dll_config_path])
        # By default, TAMods-server will listen on port-100/tcp. If udpproxy is not running,
        # -noportoffset will allow TAMods server to still listen on the same port as the game server's udp.
        if self.use_external_port:
            args.extend(['-noportoffset'])
        process = sp.Popen(args, cwd=self.working_dir)
        self.servers[server] = process
        self.logger.info(f'{server}: started process with pid {process.pid}')

        # Check if it doesn't exit right away
        time.sleep(2)
        ret_code = process.poll()
        if ret_code:
            raise FatalError('The game server process terminated almost immediately with exit code %08X' %
                             ret_code)

        self.logger.info(f'{server}: waiting until game server has finished starting up...')
        if not self.wait_until_file_contains_string(log_filename, 'Log: Bringing up level for play took:', timeout = 30):
            self.logger.warning(f'{server}: timeout waiting for log entry, continuing with injection...')

        self.logger.info(f'{server}: injecting game controller DLL into game server...')
        inject(process.pid, self.dll_to_inject)
        self.logger.info(f'{server}: injection done.')

        self.watcher_task = gevent_spawn('gameserver process watcher for server %s' % server, self.server_process_watcher, process, server)

    def stop_server_process(self, server):
        if server in self.servers:
            process = self.servers[server]
            self.logger.info(f'{server}: terminating game server process {process.pid}')
            process.terminate()

    def freeze_server_process(self, server):
        pid = self.servers[server].pid
        if not ctypes.windll.kernel32.DebugActiveProcess(pid):
            self.logger.error(f'{server}: failed to freeze game server process {pid}')
        else:
            self.logger.info(f'{server}: game server process {pid} frozen')

    def unfreeze_server_process(self, server):
        pid = self.servers[server].pid
        if not ctypes.windll.kernel32.DebugActiveProcessStop(pid):
            self.logger.error(f'{server}: failed to unfreeze game server process {pid}')
        else:
            self.logger.info(f'{server}: game server process {pid} unfrozen')

    def terminate_all_servers(self):
        existing_servers = self.servers
        self.servers = {}
        for server, process in existing_servers.items():
            self.logger.info(f'{server}: terminating game server process {process.pid}')
            process.terminate()

    def run(self):
        try:
            for msg in self.server_handler_queue:
                if isinstance(msg, StartGameServerMessage):
                    self.start_server_process(msg.server)
                elif isinstance(msg, StopGameServerMessage):
                    self.stop_server_process(msg.server)
                elif isinstance(msg, FreezeGameServerMessage):
                    self.freeze_server_process(msg.server)
                else:
                    assert isinstance(msg, UnfreezeGameServerMessage)
                    self.unfreeze_server_process(msg.server)

        finally:
            self.terminate_all_servers()


def handle_game_server(game_server_config, ports, server_handler_queue, incoming_queue, data_root):
    game_server_handler = GameServerHandler(game_server_config,
                                            ports,
                                            server_handler_queue,
                                            incoming_queue,
                                            data_root)
    game_server_handler.run()
