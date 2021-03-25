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

import os

MIN_UNVERIFIED_ID = 1000000
MAX_UNVERIFIED_ID = 2000000

AUTHBOT_ID = MIN_UNVERIFIED_ID - 1

MIN_VERIFIED_ID = 1
MAX_VERIFIED_ID = AUTHBOT_ID - 1

def get_shared_ini_path(data_root):
    return os.path.join(data_root, 'shared.ini')


def first_unused_number_above(numbers, minimum, maximum=None):
    used_numbers = (n for n in numbers if n >= minimum)
    first_number_above = next(i for i, e in enumerate(sorted(used_numbers) + [None], start=minimum) if i != e)
    if maximum is not None and first_number_above > maximum:
        raise RuntimeError('Unable to allocate an unused number between {minimum} and {maximum}. All are in use.')
    return first_number_above


def is_valid_ascii_for_name(ascii_bytes):
    return all((33 <= c <= 126 and chr(c) not in r'#/:?\`~') for c in ascii_bytes)
