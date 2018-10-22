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

from ipaddress import IPv4Address
from typing import Optional


class IPAddressPair:
    def __init__(self, external_ip: Optional[IPv4Address], internal_ip: Optional[IPv4Address]):
        assert external_ip is not None or internal_ip is not None
        assert external_ip is None or external_ip.is_global
        assert internal_ip is None or internal_ip.is_private

        self._external_ip = external_ip
        self._internal_ip = internal_ip

    def validate_against_detected_address(self, detected_ip: IPv4Address):
        assert detected_ip == self._external_ip or detected_ip == self._internal_ip

    def get_preferred_destination(self, source_address_pair):
        if (self._external_ip is None or
                source_address_pair._external_ip is None or
                self._external_ip == source_address_pair._external_ip):
            return self._internal_ip
        else:
            return self._external_ip

    def __str__(self):
        return '%s/%s' % (self._external_ip, self._internal_ip)


def hexdump(data):
    bytelist = ['%02X' % b for b in data]
    offset = 0
    while len(bytelist) > offset + 16:
        print('%04X: %s' % (offset, ' '.join(bytelist[offset:offset + 16])))
        offset += 16
    print('%04X: %s' % (offset, ' '.join(bytelist[offset:])))


def first_unused_number_above(numbers, minimum):
    used_numbers = (n for n in numbers if n >= minimum)
    first_number_above = next(i for i, e in enumerate(sorted(used_numbers) + [None], start=minimum) if i != e)
    return first_number_above
