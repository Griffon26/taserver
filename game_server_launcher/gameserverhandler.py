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

import ctypes
import ctypes.wintypes
import gevent
import gevent.subprocess as sp
import logging
import os
import time

from .inject import inject
from common.errors import FatalError


class ConfigurationError(FatalError):
    def __init__(self, message):
        super().__init__('Configuration error: %s' % message)

class StartGameServerMessage:
    def __init__(self, port):
        self.port = port

class StopGameServerMessage:
    def __init__(self, port):
        self.port = port

class GameServerTerminatedMessage:
    def __init__(self, port):
        self.port = port


class GameServerHandler:

    def __init__(self, game_server_config, server_handler_queue, launcher_queue):
        gevent.getcurrent().name = 'gameserver'

        self.servers = {}

        self.server_handler_queue = server_handler_queue
        self.launcher_queue = launcher_queue

        self.logger = logging.getLogger(__name__)

        try:
            self.working_dir = game_server_config['dir']
            self.dll_to_inject = game_server_config['controller_dll']
            self.dll_config_path = game_server_config['controller_config']
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
        self.logger.info('gameserver: Path to controller DLL is %s' % self.dll_to_inject)
        self.logger.info('gameserver: Path to controller configuration is %s' % self.dll_config_path)

        if not os.path.exists(self.dll_to_inject):
            raise ConfigurationError(
                "Invalid 'controller_dll' specified under [gameserver]: the specified file does not exist.")

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


    def get_my_documents_folder(self):
        S_OK = 0
        CSIDL_MYDOCUMENTS = 5
        SHGFP_TYPE_CURRENT = 0

        _SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
        _SHGetFolderPath.argtypes = [
            ctypes.wintypes.HWND,
            ctypes.c_int,
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.LPWSTR
        ]

        buf = ctypes.create_unicode_buffer(1024)
        if _SHGetFolderPath(0, CSIDL_MYDOCUMENTS, 0, SHGFP_TYPE_CURRENT, buf) != S_OK:
            raise RuntimeError('For some reason requesting the location of the Documents folder failed')
        return buf.value

    def server_process_watcher(self, process, port):
        self.logger.info('gameserver: Starting server process watcher')
        process.wait()
        if port in self.servers:
            self.logger.info('gameserver: server terminated, notifying launcher')
            del self.servers[port]
            self.launcher_queue.put( GameServerTerminatedMessage(port) )

    def start_server_process(self, port):
        log_filename = os.path.join(self.get_my_documents_folder(),
                                    'My Games', 'Tribes Ascend',
                                    'TribesGame', 'Logs', 'tagameserver%d.log' % port)

        try:
            self.logger.info('gameserver: Removing previous log file %s' % log_filename)
            os.remove(log_filename)
        except FileNotFoundError:
            pass

        self.logger.info('gameserver: Starting a new TribesAscend server on port %d...' % port)
        # Add 100 to the port, because it's the udpproxy that's actually listening on the port itself
        # and it forwards traffic to port + 100
        args = [self.exe_path, 'server', '-Log=tagameserver%d.log' % port, '-port=%d' % (port + 100)]
        if self.dll_config_path is not None:
            args.extend(['-tamodsconfig', self.dll_config_path])
        process = sp.Popen(args, cwd=self.working_dir)
        self.servers[port] = process
        self.logger.info('gameserver: Started process with pid: %s' % process.pid)

        # Check if it doesn't exit right away
        time.sleep(2)
        ret_code = process.poll()
        if ret_code:
            raise FatalError('The game server process terminated almost immediately with exit code %08X' %
                             ret_code)

        self.logger.info('gameserver: Waiting until game server has finished starting up...')
        if not self.wait_until_file_contains_string(log_filename, 'Log: Bringing up level for play took:', timeout = 30):
            self.logger.warning('gameserver: timeout waiting for log entry, continuing with injection...')

        self.logger.info('gameserver: Injecting game controller DLL into game server...')
        inject(process.pid, self.dll_to_inject)
        self.logger.info('gameserver: Injection done.')

        self.watcher_task = gevent.spawn(self.server_process_watcher, process, port)

    def stop_server_process(self, port):
        if port in self.servers:
            process = self.servers[port]
            self.logger.info('gameserver: Terminating game server on port %u, process %u' % (port, process.pid))
            process.terminate()

    def terminate_all_servers(self):
        processes = self.servers.values()
        self.servers = {}
        for process in processes:
            self.logger.info('gameserver: Terminating game server process %u' % process.pid)
            process.terminate()

    def run(self):
        try:
            for msg in self.server_handler_queue:
                if isinstance(msg, StartGameServerMessage):
                    self.start_server_process(msg.port)
                else:
                    assert(isinstance(msg, StopGameServerMessage))
                    self.stop_server_process(msg.port)
        finally:
            self.terminate_all_servers()


def handle_game_server(game_server_config, server_handler_queue, incoming_queue):
    game_server_handler = GameServerHandler(game_server_config, server_handler_queue, incoming_queue)
    game_server_handler.run()
