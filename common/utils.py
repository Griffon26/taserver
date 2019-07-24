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


def first_unused_number_above(numbers, minimum):
    used_numbers = (n for n in numbers if n >= minimum)
    first_number_above = next(i for i, e in enumerate(sorted(used_numbers) + [None], start=minimum) if i != e)
    return first_number_above


def is_valid_ascii_for_name(ascii_bytes):
    return all((33 <= c <= 126 and chr(c) not in r'#/:?\`~') for c in ascii_bytes)
