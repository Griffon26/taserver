#!/usr/bin/env python3
#
# Copyright (C) 2018-2019  Maurice van der Pot <griffon26@kfk4ever.com>
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

import certifi
from gevent import socket
from ipaddress import IPv4Address
from typing import Optional
import urllib.request as urlreq


def _get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return IPv4Address(ip)


class IPAddressPair:
    def __init__(self, external_ip: Optional[IPv4Address], internal_ip: Optional[IPv4Address]):
        assert external_ip is not None or internal_ip is not None
        assert external_ip is None or external_ip.is_global
        assert internal_ip is None or internal_ip.is_private

        self.external_ip = external_ip
        self.internal_ip = internal_ip

    def validate_against_detected_address(self, detected_ip: IPv4Address):
        assert detected_ip == self.external_ip or detected_ip == self.internal_ip

    def get_address_seen_from(self, source_address_pair):
        if self.internal_ip is None:
            return self.external_ip
        elif (self.external_ip is None or
                source_address_pair.external_ip is None or
                self.external_ip == source_address_pair.external_ip):
            return self.internal_ip
        else:
            return self.external_ip

    def __str__(self):
        return '%s/%s' % (self.external_ip, self.internal_ip)

    @staticmethod
    def detect():
        detection_error = None

        req = urlreq.Request('https://ipv4.icanhazip.com/', headers={'User-Agent': 'Mozilla/5.0'})
        try:
            external_ip = IPv4Address(urlreq.urlopen(req, cafile=certifi.where()).read().decode('utf8').strip())
        except Exception as e:
            external_ip = None
            detection_error = str(e)
        if external_ip:
            assert external_ip.is_global

        internal_ip = _get_local_ip()
        if internal_ip == external_ip:
            internal_ip = None
        else:
            assert internal_ip.is_private

        return IPAddressPair(external_ip, internal_ip), detection_error
