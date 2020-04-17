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

from common.geventwrapper import gevent_spawn_later
from common import utils


class ExecuteCallbackMessage():
    def __init__(self, callback_id):
        self.callback_id = callback_id


class PendingCallbacks:
    def __init__(self, server_queue):
        self.server_queue = server_queue
        self.callbacks = {}

    def add(self, receiver, seconds_from_now, callback_func):
        callback_id = utils.first_unused_number_above(self.callbacks.keys(), 0)

        self.callbacks[callback_id] = {'receiver_id': id(receiver),
                                       'callback_func': callback_func }
        gevent_spawn_later('pending callback for %s' % receiver, seconds_from_now, self._post_callback, callback_id)

    def remove_receiver(self, receiver):
        for callback_id, callback in self.callbacks.items():
            if callback['receiver_id'] == id(receiver):
                # Only disable callbacks here, removal is done when the callback is fired
                callback['callback_func'] = None

    def _post_callback(self, callback_id):
        self.server_queue.put(ExecuteCallbackMessage(callback_id))

    def execute(self, callback_id):
        assert callback_id in self.callbacks, "Callback not found. A callback should only be removed by " \
                                              "its trigger to avoid problems with reused callback IDs."

        if self.callbacks[callback_id]['callback_func'] is not None:
            self.callbacks[callback_id]['callback_func']()
        del self.callbacks[callback_id]

