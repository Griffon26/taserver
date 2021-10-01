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
from distutils.version import StrictVersion
import os
import re
import xml.etree.ElementTree as XML
from urllib.error import HTTPError
import urllib.request as urlreq

from common.versions import launcher2controller_protocol_version

compatibility_csv = 'https://raw.githubusercontent.com/Griffon26/taserver/master/data/tamods_compatibility.csv'
base_controller_url = 'https://tamods-server-update.s3-ap-southeast-2.amazonaws.com'
target_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'TAMods-Server.dll')


class UserError(Exception):
    pass


def get_available_tamods_versions():
    tamods_server_files = []
    with urlreq.urlopen(f'{base_controller_url}?list-type=2', cafile=certifi.where()) as resp:
        # S3 list responds with XML
        root = XML.parse(resp).getroot()
        ns_prefix = '{http://s3.amazonaws.com/doc/2006-03-01/}'
        for item in root.findall(f'./{ns_prefix}Contents'):
            key = item.find(f'./{ns_prefix}Key').text
            if key.startswith('TAMods-Server') and key.endswith('.dll'):
                tamods_server_files.append(key)

    available_tamods_versions = []
    version_to_filename_map = {}
    for filename in tamods_server_files:
        match = re.match(r'TAMods-Server-(.*).dll', filename)
        if match:
            try:
                version = StrictVersion(match.group(1))
                available_tamods_versions.append(version)
                version_to_filename_map[str(version)] = filename
            except ValueError:
                # Ignore versions that cannot be parsed
                pass

    return sorted(available_tamods_versions), version_to_filename_map


def load_version_map():
    response = urlreq.urlopen(compatibility_csv, cafile=certifi.where())
    encoding = response.info().get_content_charset()
    content = response.read().decode(encoding)

    version_map = {}
    for line in content.splitlines():
        if not line.strip() or line.strip().startswith('#'):
            continue

        fields = (field.strip() for field in line.split(','))
        protocol_version, tamods_version = fields
        version_map[str(StrictVersion(tamods_version))] = StrictVersion(protocol_version)

    return version_map


def get_protocol_version(tamods_version, compatibility_map):
    sorted_tamods_versions = sorted(StrictVersion(version) for version in compatibility_map.keys())
    versions_not_newer = [version for version in sorted_tamods_versions if version <= tamods_version]
    latest_version_not_newer = versions_not_newer[-1]
    protocol_version = compatibility_map[str(latest_version_not_newer)]
    return protocol_version


def is_compatible(version1, version2):
    return version1.version[0] == version2.version[0]


def download_tamods_server_version(download_filename):
    with urlreq.urlopen(f'{base_controller_url}/{download_filename}', cafile=certifi.where()) as result:
        with open(target_filename, 'wb') as outfile:
            outfile.write(result.read())


def main():
    try:
        version_map = load_version_map()
    except HTTPError as e:
        raise UserError('unable to download %s: %s' % (compatibility_csv, e))

    available_tamods_versions, version_to_filename_map = get_available_tamods_versions()
    if not available_tamods_versions:
        raise UserError('no TAMods-Server versions were found in the release branch of github.com/mcoot/tamodsupdate')

    print('Available TAMods-server versions:')
    print('\n'.join('  %s (supports protocol version %s)' %
                    (version, get_protocol_version(version, version_map)) for version in available_tamods_versions))

    print('Protocol version supported by this taserver version: %s' % launcher2controller_protocol_version)

    latest_compatible_version = None
    for tamods_version in reversed(available_tamods_versions):
        if is_compatible(get_protocol_version(tamods_version, version_map), launcher2controller_protocol_version):
            latest_compatible_version = tamods_version
            break

    if latest_compatible_version is None:
        raise UserError('no compatible version of TAMods-Server is available')

    print('Latest compatible TAMods-Server version is %s' % latest_compatible_version)
    download_filename = version_to_filename_map[str(latest_compatible_version)]
    print('Downloading %s to %s' % (download_filename, target_filename))
    try:
        download_tamods_server_version(download_filename)
    except HTTPError as e:
        raise UserError('download failed: %s' % e)

    print('Done.')


if __name__ == '__main__':
    try:
        main()
    except UserError as e:
        print('\nError: %s' % e)
        exit(-1)
