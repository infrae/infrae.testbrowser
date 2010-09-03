# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import collections
import urlparse
import urllib
import lxml.html

from infrae.testbrowser.wsgi import WSGIServer
from infrae.testbrowser.form import Form, Link

HISTORY_LENGTH = 20


def format_auth(user, password):
    return 'Basic ' + ':'.join((user, password)).encode('base64').strip()


def node_to_text(node):
    return node.text_content().strip()


class Options(object):
    follow_redirect = True
    cookie_support = True


class Expressions(object):

    def __init__(self, browser):
        self.__browser = browser
        self.__expressions = {}

    def add(self, name, xpath):
        self.__expressions[name] = xpath

    def __getattr__(self, name):
        expression = self.__expressions.get(name)
        if expression:
            assert self.__browser.html is not None, u'Not viewing HTML'
            return map(node_to_text, self.__browser.html.xpath(expression))
        raise AttributeError(name)


class Browser(object):

    def __init__(self, app):
        self.__server = WSGIServer(app)
        self.options = Options()
        self.inspect = Expressions(self)
        self.__url = None
        self.__method = None
        self.__response = None
        self.__data = None
        self.__data_type = None
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
    def contents(self):
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

    def _query_application(self, url, method, query, data, data_type):
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
        self._process_response(
            self.__server(method, uri, headers.items(), data, data_type))

    def _process_response(self, response):
        self.__response = response

        # Cookie support
        if self.options.cookie_support:
            cookie = self.headers.get('Set-Cookie')
            if cookie:
                self.set_request_header('Cookie', cookie)

        # Redirect
        if (self.status_code in (301, 302, 303) and
            self.options.follow_redirect):
            if self.__method not in ('GET', 'HEAD'):
                self.__method = 'GET'
            location = self.headers.get('Location')
            assert location is not None, 'Redirect without location header'
            return self._query_application(
                location, self.__method, None, None, None)

        # Parse HTML
        content_type = self.content_type
        if content_type and (content_type.startswith('text/html') or
                             content_type.startswith('text/xhtml')):
            self.html = lxml.html.document_fromstring(self.contents)
            self.html.resolve_base_href()

    def open(self, url, method='GET', query=None, form=None):
        if self.__response:
            self.__history.append(
                (self.__url, self.__method, self.__response))
        data = None
        data_type = None
        self.html = None
        self.__response = None
        self.__method = method
        if form is not None:
            # We posted a form
            if method == 'GET':
                if query is not None:
                    raise AssertionError(
                        u'Cannot handle aquery with a GET form')
                query = form
            else:
                assert method == 'POST', u'Only support POST or GET forms'
                data = urllib.urlencode(form)
                data_type = 'application/x-www-form-urlencoded'
        self.__data = data
        self.__data_type = data_type
        self._query_application(url, method, query, data, data_type)
        return self.status_code

    def reload(self):
        assert self.__url is not None, 'No URL to reload'
        self.html = None
        self.__response = None
        self._query_application(
            self.__url, self.__method, None, self.__data, self.__data_type)
        return self.status_code

    def get_form(self, name):
        assert self.html is not None, 'Not viewing HTML'
        nodes = self.html.xpath('//form[@name="%s"]' % name)
        assert len(nodes) == 1, 'Form element not found'
        return Form(nodes[0], self)

    def get_link(self, content):
        assert self.html is not None, 'Not viewing HTML'
        links = self.html.xpath(
            '//a[contains(normalize-space(text()), "%s")]' % content)
        assert len(links) == 1, 'No link found'
        return Link(links[0], self)
