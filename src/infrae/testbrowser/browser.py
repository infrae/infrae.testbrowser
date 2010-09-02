# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import collections
import urlparse
import urllib
import lxml.html

from infrae.testbrowser.wsgi import WSGIServer

HISTORY_LENGTH = 20


def format_auth(user, password):
    return ':'.join((user, password)).encode('base64').strip()


class Browser(object):

    def __init__(self, app):
        self.__server = WSGIServer(app)
        self.__url = None
        self.__method = None
        self.__response = None
        self.__content = None
        self.__query = {}
        self.__request_headers = dict()
        self.__history = collections.deque([], HISTORY_LENGTH)
        self.html = None

    @property
    def url(self):
        return self.__url

    @property
    def method(self):
        return self.__method

    @property
    def status(self):
        if self.__response is not None:
            return self.__response.status
        return None

    @property
    def status_code(self):
        status = self.status
        if status is None:
            return None
        try:
            return int(status.split(' ', 1)[0])
        except ValueError:
            raise AssertionError('Invalid HTTP status %s' % status)

    @property
    def headers(self):
        if self.__response is not None:
            return self.__response.headers
        return {}

    @property
    def content(self):
        if self.__response is not None:
            return self.__response.output.getvalue()
        return None

    @property
    def content_type(self):
        return self.headers.get('content-type')

    def set_request_header(self, key, value):
        self.__request_headers[key] = value

    def clear_request_headers(self):
        self.__request_headers = dict()

    def login(self, user, password):
        self.set_request_header('Authorization', format_auth(user, password))

    @property
    def history(self):
        return map(lambda e: e[0], self.__history)

    def _query_application(self, url, method, query):
        url_info = urlparse.urlparse(url)
        query_string = urllib.urlencode(query) if query else ''
        uri = urlparse.urlunparse(
            (None,
             None,
             url_info.path,
             url_info.params,
             query_string or url_info.query,
             url_info.fragment))
        self.__url = uri
        headers = self.__request_headers.copy()
        if url_info.username and url_info.password:
            headers['Authorization'] = format_auth(
                url_info.username, url_info.password)
        self._process_response(self.__server(method, uri, headers.items()))

    def _process_response(self, response):
        self.__response = response
        content_type = self.content_type
        if content_type.startswith('text/html') or \
                content_type.startswith('text/xhtml'):
            self.html = lxml.html.document_fromstring(self.content)

    def open(self, url, method='GET', query=None):
        if self.__response:
            self.__history.append(
                (self.__url, self.__method, self.__response))
        query = query if query is not None else {}
        self.html = None
        self.__response = None
        self.__method = method
        self._query_application(url, method, query)
        return self.status_code

    def reload(self):
        self.html = None
        self.__response = None
        self._query_application(self.__url, self.__method, None)
        return self.status_code
