# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import threading
import wsgiref.simple_server


class WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):

    def log_message(self, *args):
        # We don't log.
        pass


class WSGIRunner(threading.Thread):

    def __init__(self, app, options):
        super(WSGIRunner, self).__init__()
        self.server = wsgiref.simple_server.make_server(
            options.server, int(options.port), app,
            handler_class=WSGIRequestHandler)
        # 0.5s polling for shutdown check.
        self.server.timeout = 0.5
        self.stopping = False

    def run(self):
        while not self.stopping:
            self.server.handle_request()


class Server(object):

    def __init__(self, app, options):
        self.__app = app
        self.__options = options
        self.__runner = None

    def start(self):
        if self.__runner is None:
            self.__runner = WSGIRunner(self.__app, self.__options)
            self.__runner.start()

    def stop(self):
        if self.__runner is not None:
            self.__runner.stopping = True
            self.__runner.join()
            self.__runner = None
