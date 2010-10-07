# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from cStringIO import StringIO
from zope.interface import implements

from infrae.testbrowser.headers import HTTPHeaders
from infrae.testbrowser.interfaces import IWSGIServer, IWSGIResponse


class WSGIResponse(object):
    implements(IWSGIResponse)

    def __init__(self, app, environ):
        self.__app = app
        self.__environ = environ
        self.status = None
        self.headers = HTTPHeaders()
        self.output = StringIO()

    def start_response(self, status, response_headers, exc_info=None):
        self.status = status
        self.headers.update(response_headers)
        return self.output.write

    def __call__(self):
        result = self.__app(self.__environ, self.start_response)
        try:
            for item in result:
                self.output.write(item)
        finally:
            if hasattr(result, 'close'):
                result.close()
        self.output.seek(0)


class WSGIServer(object):
    implements(IWSGIServer)
    server = 'localhost'
    port = '80'
    protocol = 'HTTP/1.0'

    def __init__(self, app, options):
        self.__app = app
        self.options = options

    def get_default_environ(self):
        environ = {}
        environ['SERVER_PROTOCOL'] = self.protocol
        environ['SERVER_NAME'] = self.server
        environ['SERVER_PORT'] = self.port
        environ['wsgi.version'] = (1,0)
        environ['wsgi.url_scheme'] = 'http'
        environ['wsgi.input'] = StringIO()
        environ['wsgi.errors'] = StringIO()
        environ['wsgi.multithread'] = False
        environ['wsgi.multiprocess'] = False
        environ['wsgi.run_once'] = False
        environ['wsgi.handleErrors'] = self.options.handle_errors
        return environ

    def get_environ(self, method, uri, headers, data=None, data_type=None):
        query = ''
        environ = self.get_default_environ()
        environ['REQUEST_METHOD'] = method
        environ['SCRIPT_NAME'] = ''
        if '?' in uri:
            uri, query = uri.split('?', 1)
        if '#' in uri:
            uri, _ = uri.split('#', 1)
        environ['PATH_INFO'] = uri
        environ['QUERY_STRING'] = query
        if data is not None and data_type is not None:
            environ['wsgi.input'].write(data)
            environ['wsgi.input'].seek(0)
            environ['CONTENT_LENGTH'] = len(data)
            environ['CONTENT_TYPE'] = data_type
        for name, value in headers:
            http_name = ('HTTP_' + name.upper()).replace('-', '_')
            environ[http_name] = value
        return environ

    def __call__(self, method, uri, headers, data=None, data_type=None):
        environ = self.get_environ(method, uri, headers, data, data_type)
        response = WSGIResponse(self.__app, environ)
        response()
        return response
