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


class ConfigurationError(Exception):
    def __init__(self, message):
        super().__init__('Configuration error: %s' % message)


def wait_until_file_contains_string(filename, string):
    while True:
        try:
            with open(filename, 'rt') as f:
                if string in f.read():
                    break
                gevent.sleep(3)
        except FileNotFoundError:
            gevent.sleep(3)


def get_my_documents_folder():
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

def run_game_server(game_server_config):
    log_filename = os.path.join(get_my_documents_folder(),
                                'My Games', 'Tribes Ascend',
                                'TribesGame', 'Logs', 'tagameserver.log')

    logger = logging.getLogger(__name__)
    gevent.getcurrent().name = 'gameserver'

    try:
        working_dir = game_server_config['dir']
        dll_to_inject = game_server_config['controller_dll']
        dll_config_path = game_server_config['controller_config']
    except KeyError as e:
        raise ConfigurationError("%s is a required configuration item under [gameserver]" % str(e))

    exe_path = os.path.join(working_dir, 'TribesAscend.exe')

    if not os.path.exists(working_dir):
        raise ConfigurationError(
            "Invalid 'dir' specified under [gameserver]: the directory does not exist")
    if not os.path.exists(exe_path):
        raise ConfigurationError(
            "Invalid 'dir' specified under [gameserver]: the specified directory does not contain a TribesAscend.exe")

    if not os.path.isabs(dll_to_inject):
        dll_to_inject = os.path.abspath(dll_to_inject)
    if not os.path.isabs(dll_config_path):
        dll_config_path = os.path.abspath(dll_config_path)
    logger.info('gameserver: Path to controller DLL is %s' % dll_to_inject)
    logger.info('gameserver: Path to controller configuration is %s' % dll_config_path)

    if not os.path.exists(dll_to_inject):
        raise ConfigurationError(
            "Invalid 'controller_dll' specified under [gameserver]: the specified file does not exist.")

    try:
        logger.info('gameserver: Removing previous log file %s' % log_filename)
        os.remove(log_filename)
    except FileNotFoundError:
        pass

    logger.info('gameserver: Starting a new TribesAscend server...')
    args = [exe_path, 'server', '-Log=tagameserver.log']
    if dll_config_path is not None:
        args.extend(['-tamodsconfig', dll_config_path])
    process = sp.Popen(args, cwd=working_dir)
    try:
        logger.info('gameserver: Started process with pid: %s' % process.pid)

        # Check if it doesn't exit right away
        time.sleep(2)
        ret_code = process.poll()
        if ret_code:
            raise FatalError('The game server process terminated almost immediately with exit code %08X' %
                             ret_code)

        logger.info('gameserver: Waiting until game server has finished starting up...')
        wait_until_file_contains_string(log_filename, 'Log: Bringing up level for play took:')

        logger.info('gameserver: Injecting game controller DLL into game server...')
        inject(process.pid, dll_to_inject)
        logger.info('gameserver: Injection done.')

        process.wait()
    finally:
        process.terminate()
