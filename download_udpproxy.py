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

import certifi
import os
import ssl
from urllib.error import HTTPError
import urllib.request as urlreq


target_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'udpproxy.exe')
download_url = 'https://github.com/Griffon26/taserver/releases/download/v2.1.0/udpproxy.exe'


class UserError(Exception):
    pass


def main():
    print('Downloading %s\nto %s' % (download_url, target_filename))
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        result = urlreq.urlopen(download_url, context=ssl_context)
        with open(target_filename, 'wb') as outfile:
            outfile.write(result.read())
    except HTTPError as e:
        raise UserError('download failed: %s' % e)

    print('Done.')


if __name__ == '__main__':
    try:
        main()
    except UserError as e:
        print('\nError: %s' % e)
        exit(-1)
