#!/usr/bin/env python3
#
# Copyright (C) 2018  Joseph Spearritt <mcoot@tamods.org>
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

import copy

from .migration_mechanism import taserver_migration, upgrades_all_players

# Writing a migration function
#
# A migration function should be decorated with @taserver_migration(schema_version=n),
# where n = the version this migration will upgrade to
#
# If a migration fails, it should raise a ValueError (if it encounters a format error in existing data)
# or an OSError (if file system manipulation fails)
#
# The function it decorates is an arbitrary script that should perform whatever operations are needed for this migration
#
# A helper decoration, @upgrades_all_players, is provided to simplify migrations which upgrade
# the format of player datastores. See the docstring for that decorator for details of its contract
#
# Contract for the code running migrations:
# 1) If migrations succeed, then the code may rely on all datastores being at the schema version for which
#    there is the latest defined migration
# 2) Code must handle ValueErrors (format violations in the data) and OSErrors (assorted IO errors)
#