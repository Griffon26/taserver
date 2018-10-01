#!/usr/bin/env python3
#
# Copyright (C) 2018  mcoot
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

from contextlib import contextmanager
from ctypes import *

PROCESS_CREATE_THREAD = 0x0002
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400

MEM_COMMIT = 0x00001000
MEM_RESERVE = 0x00002000

PAGE_READWRITE = 0x04

kernel32 = windll.kernel32


class InjectionFailedError(Exception):
    pass


@contextmanager
def closing_handle(handle):
    try:
        yield handle
    finally:
        if handle:
            kernel32.CloseHandle(handle)


def inject(pid, path_to_dll):

    required_access = (PROCESS_CREATE_THREAD |
                       PROCESS_VM_OPERATION |
                       PROCESS_VM_READ |
                       PROCESS_VM_WRITE |
                       PROCESS_QUERY_INFORMATION)

    with closing_handle(kernel32.OpenProcess(required_access, False, pid)) as process_handle:
        if not process_handle:
            raise InjectionFailedError('Unable to get process handle')

        # Allocate memory in the process for the DLL path, and then write it there
        path_to_dll_bytes = path_to_dll.encode('ascii') + b'\0'
        remote_path_space = kernel32.VirtualAllocEx(process_handle,
                                                    None,
                                                    len(path_to_dll_bytes),
                                                    MEM_RESERVE | MEM_COMMIT,
                                                    PAGE_READWRITE)
        if not remote_path_space:
            raise InjectionFailedError('Unable to allocate space in remote process')

        if not kernel32.WriteProcessMemory(process_handle,
                                           remote_path_space,
                                           path_to_dll_bytes,
                                           len(path_to_dll_bytes),
                                           None):
            raise InjectionFailedError('Failed to write to memory')

        # Add some obfuscation to get Windows Defender off our backs
        CreateRemoteThreadFunc = getattr(kernel32, 'HonestlyNotCreateRemoteThread'[11:])

        # Load the DLL with CreateRemoteThread + LoadLibraryA
        remote_thread = CreateRemoteThreadFunc(process_handle,
                                               None,
                                               None,
                                               c_void_p.from_buffer(kernel32.LoadLibraryA),
                                               remote_path_space,
                                               None,
                                               None)

        if not remote_thread:
            raise InjectionFailedError('Failed to create remote thread to load the DLL')
