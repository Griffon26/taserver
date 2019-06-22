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
import gevent.queue
import time
import urllib.error
import urllib.request
import urllib.parse


class WebhookHandler:
    def __init__(self, server_stats_queue, config):
        self.server_stats_queue = server_stats_queue
        self.webhook_url = config.get('webhook_url')

    def disconnect(self, e):
        self.server_stats_queue.put(None)

    def run(self):
        current_stats = []
        last_notification_time = 0
        last_reported_player_count = 0

        while True:
            try:
                current_stats = self.server_stats_queue.get_nowait()
                if not current_stats:
                    break

            except gevent.queue.Empty:
                pass

            current_time = time.time()
            player_count = sum(gs_stats['nplayers'] for gs_stats in current_stats)

            worth_notifying = (
                (player_count > last_reported_player_count and current_time > last_notification_time + 10) or
                (player_count < last_reported_player_count and current_time > last_notification_time + 60)
            )

            if self.webhook_url and worth_notifying:
                current_stats.sort(key=lambda gs: gs['description'].lower())
                current_stats.sort(key=lambda gs: gs['mode'], reverse=True)

                stat_msg = 'Server stats:\n'
                stat_msg += '```\n'
                stat_msg += '   mode   %-21.21s players\n' % 'name'
                stat_msg += ''.join(['%s %s | %-21.21s %2d/28\n' % ('\N{Lock}' if gs['locked'] else '  ',
                                                                    gs['mode'].upper(),
                                                                    gs['description'],
                                                                    gs['nplayers'])
                                        for gs in current_stats])
                stat_msg += '```\n'

                data = urllib.parse.urlencode({'content': stat_msg})
                data = data.encode('ascii')
                req = urllib.request.Request(self.webhook_url, headers={'User-Agent': 'Mozilla/5.0'})
                try:
                    urllib.request.urlopen(req, data)
                except urllib.error.URLError:
                    # TODO: do proper error logging
                    pass

                last_notification_time = current_time
                last_reported_player_count = player_count

            gevent.sleep(5)


def handle_webhook(server_stats_queue, config):
    webhook_handler = WebhookHandler(server_stats_queue, config)
    webhook_handler.run()
