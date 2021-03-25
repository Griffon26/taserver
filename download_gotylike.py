#!/usr/bin/env python3
#
# Copyright (C) 2019  Maurice van der Pot <griffon26@kfk4ever.com>
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

import os
import shutil
import tempfile
from urllib.error import HTTPError
import urllib.request as urlreq
import zipfile

default_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
download_url = 'https://github.com/Griffon26/tamods-server-gotylike/archive/master.zip'


class UserError(Exception):
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', action='store', default=default_data_dir,
                        help='Location of the data dir containing all config files and logs.')
    args = parser.parse_args()
    data_root = args.data_root
    destination_dir = os.path.join(data_root, 'gamesettings', 'gotylike')

    if os.path.exists(destination_dir):
        raise UserError('%s already exists. Please remove it before running this script again.' % destination_dir)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        print('Downloading %s...' % download_url)
        target_filename = os.path.join(temp_dir_name, 'gotylike.zip')
        try:
            result = urlreq.urlopen(download_url)
            with open(target_filename, 'wb') as outfile:
                outfile.write(result.read())
        except HTTPError as e:
            raise UserError('download failed: %s' % e)

        print('Extracting to %s' % destination_dir)
        with zipfile.ZipFile(target_filename, 'r') as my_zip:
            my_zip.extractall(temp_dir_name)

        shutil.move(os.path.join(temp_dir_name, 'tamods-server-gotylike-master'),
                    destination_dir)

    print('Done.')


if __name__ == '__main__':
    try:
        main()
    except UserError as e:
        print('\nError: %s' % e)
        exit(-1)
