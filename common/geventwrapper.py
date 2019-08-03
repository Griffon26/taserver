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

import gevent
import logging


def gevent_spawn(task_name: str, func, *args, **kwargs):

    def wrapper_func(*args, **kwargs):
        logger = logging.getLogger('gevent_spawn')
        gevent.getcurrent().name = task_name

        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception('%s greenlet terminated with an unhandled exception:' % task_name, exc_info=e)
            raise

    return gevent.spawn(wrapper_func, *args, **kwargs)


def gevent_spawn_later(task_name: str, seconds, func, *args, **kwargs):

    def wrapper_func(*args, **kwargs):
        logger = logging.getLogger('gevent_spawn_later')
        gevent.getcurrent().name = task_name

        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception('%s greenlet terminated with an unhandled exception:' % task_name, exc_info=e)
            raise

    return gevent.spawn_later(seconds, wrapper_func, *args, **kwargs)