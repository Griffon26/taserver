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

from .migration_mechanism import taserver_migration

# Contract for a migration function:
#
# 1) Function has the taserver_migration decorator, with appropriate schema_version it upgrades to
# 2) Function takes the data as a dict where the keys are each existing schemas, under which is data from that schema
# 3) Function returns the data as a dict with keys being the new schemas, under which data is in the new schema format
# 4) If the format of the original data is invalid, function raises a ValueError
# 5) Function must be a pure function, except that it may mutate its argument for convenience
#    (but in that case, it must also return its now-mutated argument)
#
# Contract for the code running migrations:
# 1) If migrations succeed, then the code may rely on all datastores being at the schema version for which
#    there is the latest defined migration
# 2) Code must handle ValueErrors (format violations in the data) and OSErrors (assorted IO errors)
#
