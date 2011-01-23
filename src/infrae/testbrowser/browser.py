# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import collections
import functools
import lxml.html
import urllib
import urlparse

from infrae.testbrowser.expressions import Expressions, Link
from infrae.testbrowser.form import Form
from infrae.testbrowser.interfaces import IBrowser, _marker
from infrae.testbrowser.utils import encode_multipart_form_data, format_auth
from infrae.testbrowser.wsgi import WSGIServer

from zope.interface import implements

HISTORY_LENGTH = 20


class Options(object):
    follow_redirect = True
    cookie_support = True
    handle_errors = True


class Macros(object):

    def __init__(self, browser):
        self.__browser = browser
        self.__macros = {}

    def add(self, name, macro):
        self.__macros[name] = functools.partial(macro, self.__browser)

    def __getattr__(self, name):
        macro = self.__macros.get(name)
        if macro is not None:
            return macro
        raise AttributeError(name)


class Browser(object):
    implements(IBrowser)

    def __init__(self, app):
        self.options = Options()
        self.inspect = Expressions(self)
        self.macros = Macros(self)
        self.__server = WSGIServer(app, self.options)
        self.__url = None
        self.__method = None
        self.__response = None
        self.__data = None
        self.__data_type = None
        self.__request_headers = dict()
        self.__history = collections.deque([], HISTORY_LENGTH)
        self.__cache = {}
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

    def get_request_header(self, key):
        return self.__request_headers.get(key)

    def clear_request_headers(self):
        self.__request_headers = dict()

    def login(self, user, password=_marker):
        if password is _marker:
            password = user
        self.set_request_header('Authorization', format_auth(user, password))

    @property
    def location(self):
        if self.__url:
            return urlparse.urlparse(self.__url).path
        return None

    @property
    def history(self):
        return map(lambda e: e[0], self.__history)

    def _query_application(self, url, method, query, data, data_type):
        self.__cache = {}
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
                self.set_request_header('Cookie', cookie.split(';', 1)[0])

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
            contents = self.contents
            if contents:
                self.html = lxml.html.document_fromstring(contents)
                self.html.resolve_base_href()

    def open(self, url, method='GET', query=None,
             form=None, form_enctype='application/x-www-form-urlencoded'):
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
                assert form_enctype == 'application/x-www-form-urlencoded', \
                    u'Invalid form encoding for GET method'
                if query is not None:
                    raise AssertionError(
                        u'Cannot handle a query with a GET form')
                query = form
            else:
                assert method == 'POST', u'Only support POST or GET forms'
                if form_enctype == 'application/x-www-form-urlencoded':
                    data_type = 'application/x-www-form-urlencoded'
                    data = urllib.urlencode(form)
                elif form_enctype == 'multipart/form-data':
                    data_type, data = encode_multipart_form_data(form)
                else:
                    raise AssertionError(
                        u"Unsupported form encoding %s" % form_enctype)
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

    def get_form(self, name=None, id=None):
        assert self.html is not None, 'Not viewing HTML'
        expression = None
        if name is not None:
            expression = '//form[@name="%s"]' % name
        elif id is not None:
            expression = '//form[@id="%s"]' % id
        assert expression is not None, 'Provides an id or a name to get_form'
        if expression not in self.__cache:
            nodes = self.html.xpath(expression)
            assert len(nodes) == 1, 'Form element not found'
            self.__cache[expression] = Form(nodes[0], self)
        return self.__cache[expression]

    def get_link(self, content):
        assert self.html is not None, 'Not viewing HTML'
        urls = {}
        for link in self.html.xpath(
            '//a[contains(normalize-space(text()), "%s")]' % content):
            urls[link.attrib['href']] = link
        assert len(urls) == 1, 'No link found'
        return Link(urls.values()[0], self)
