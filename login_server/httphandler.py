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

import gevent.queue
from gevent import pywsgi
import logging

from common.datatypes import HttpRequestMessage


class HttpHandler:
    def __init__(self, incoming_queue, ports):
        self.ports = ports
        self.incoming_queue = incoming_queue
        self.response_queue = gevent.queue.Queue()

    def handle_http_request(self, env, start_response):
        self.incoming_queue.put(HttpRequestMessage(self, env))
        response = self.response_queue.get()

        if isinstance(response, Exception):
            logger = logging.getLogger(__name__)
            logger.exception('an exception was encountered while processing a http request:', exc_info=response)
            raise response
        elif response:
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [response.encode()]
        else:
            start_response('404 Not Found', [('Content-Type', 'text/html')])
            return [b'<h1>Not Found</h1>']

    def send_response(self, response):
        self.response_queue.put(response)

    def disconnect(self, e):
        self.response_queue.put(e)

    def run(self):
        server = pywsgi.WSGIServer(('0.0.0.0', self.ports['restapi']),
                                   self.handle_http_request)
        server.serve_forever()


def handle_http(incoming_queue, ports):
    http_handler = HttpHandler(incoming_queue, ports)
    http_handler.run()
