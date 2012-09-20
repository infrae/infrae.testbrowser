# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import collections
import json
import lxml.etree
import lxml.html
import re
import urllib
import urlparse

from infrae.testbrowser.cookies import Cookies
from infrae.testbrowser.expressions import Expressions, Link
from infrae.testbrowser.form import Form
from infrae.testbrowser.interfaces import IAdvancedBrowser, _marker
from infrae.testbrowser.interfaces import ICustomizableOptions
from infrae.testbrowser.utils import Macros, CustomizableOptions, Handlers
from infrae.testbrowser.utils import encode_multipart_form_data, format_auth
from infrae.testbrowser.wsgi import WSGIServer

from zope.interface import implements

HISTORY_LENGTH = 20


class Options(CustomizableOptions):
    # Browser options
    follow_external_redirect = False
    follow_redirect = True
    cookie_support = True
    handle_errors = True

    # Server options
    server = 'localhost'
    port = '80'
    protocol = 'HTTP/1.0'
    default_wsgi_environ = {}

    def __init__(self):
        super(Options, self).__init__(ICustomizableOptions)


CHARSET_CAPTURE = re.compile(r'charset=(?P<charset>[^;]+)')


class Browser(object):
    implements(IAdvancedBrowser)

    def __init__(self, app):
        self.options = Options()
        self.inspect = Expressions(self)
        self.macros = Macros(self)
        self.handlers = Handlers()
        self.__server = WSGIServer(app, self.options)
        self.__url = None
        self.__method = None
        self.__response = None
        self.__data = None
        self.__data_type = None
        self.cookies = Cookies()
        self.__request_headers = dict()
        self.__history = collections.deque([], HISTORY_LENGTH)
        self.__cache = {}
        self.html = None
        self.xml = None
        self.json = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def url(self):
        return self.__url

    @property
    def location(self):
        if self.__url:
            return urlparse.urlparse(self.__url).path
        return None

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
            raise AssertionError(u'Invalid HTTP status %s' % status)

    @property
    def headers(self):
        if self.__response is not None:
            return self.__response.headers
        return {}

    @property
    def contents(self):
        if self.__response is not None:
            contents = self.__response.output.getvalue()
            if self.content_encoding is not None:
                return contents.decode(self.content_encoding)
            else:
                return contents
        return None

    @property
    def content_type(self):
        return self.headers.get('content-type')

    @property
    def content_encoding(self):
        content_type = self.content_type
        if content_type and 'charset=' in content_type:
            charset_match = CHARSET_CAPTURE.search(content_type)
            if charset_match:
                return charset_match.group('charset').lower()

    def set_request_header(self, key, value):
        self.__request_headers[key] = value

    def get_request_header(self, key):
        return self.__request_headers.get(key)

    def del_request_header(self, key):
        if key in self.__request_headers:
            del self.__request_headers[key]

    def clear_request_headers(self):
        self.__request_headers = dict()

    def login(self, user, password=_marker):
        if user is None:
            self.logout()
        if password is _marker:
            password = user
        if 'login' in self.handlers:
            self.handlers.login.login(self, user, password)
        else:
            if password is _marker:
                password = user
            self.set_request_header(
                'Authorization',
                format_auth(user, password))

    def logout(self):
        if 'login' in self.handlers:
            self.handlers.login.logout(self)
        else:
            self.del_request_header(
                'Authorization')

    @property
    def history(self):
        return map(lambda e: e[0], self.__history)

    def _query_application(self, url, method, query, data, data_type):
        self.__cache = {}
        info = urlparse.urlparse(url)
        query_string = urllib.urlencode(query) if query else ''
        uri = urlparse.urlunparse(
            (None,
             None,
             info.path,
             info.params,
             query_string or info.query,
             info.fragment))
        self.__url = uri
        headers = self.__request_headers.copy()
        headers.update(self.cookies.get_request_headers())
        if info.username and info.password:
            headers['Authorization'] = format_auth(
                info.username, info.password)
        self._process_response(
            self.__server(method, uri, headers.items(), data, data_type))

    def _process_response(self, response):
        self.__response = response

        # Cookie support
        if self.options.cookie_support:
            cookie = self.headers.get('Set-Cookie')
            if cookie:
                self.cookies.parse(cookie)

        # Redirect
        if (self.status_code in (301, 302, 303) and
            self.options.follow_redirect):
            if self.__method not in ('GET', 'HEAD'):
                self.__method = 'GET'
            location = self.headers.get('Location')
            assert location is not None, 'Redirect without location header'
            location_url = urlparse.urlparse(location)
            location_uri = None
            if location_url.netloc:
                # Inspect redirect URL
                if ':' in location_url.netloc:
                    server, port = location_url.netloc.split(':', 1)
                else:
                    server = location_url.netloc
                    if location_url.scheme == 'https':
                        port = '443'
                    else:
                        port = '80'
                if server != self.options.server or port != self.options.port:
                    if self.options.follow_external_redirect:
                        # XXX Should include this information in history as well
                        self.options.server = server
                        self.options.port = port
                        location_uri = urlparse.urlunparse(
                            (None, None) + location_url[2:])
                else:
                    location_uri = urlparse.urlunparse(
                        (None, None) + location_url[2:])
            else:
                location_uri = location
            if location_uri is not None:
                return self._query_application(
                    location_uri, self.__method, None, None, None)

        # Parse HTML or XML
        if response is not None:
            content_type = response.headers.get('content-type')
            data = response.output.getvalue()
            if content_type and data:
                if (content_type.startswith('text/html') or
                    content_type.startswith('text/xhtml')):
                    self.html = lxml.html.document_fromstring(self.contents)
                    self.html.resolve_base_href()
                elif content_type.startswith('text/xml'):
                    self.xml = lxml.etree.fromstring(data)
                elif content_type.startswith('application/json'):
                    self.json = json.loads(self.contents)

    def open(self, url, method='GET', query=None,
             form=None, form_charset='utf-8', form_enctype='application/x-www-form-urlencoded',
             data=None, data_type=None):
        if self.__response:
            self.__history.append(
                (self.__url, self.__method, self.__response))
        self.html = None
        self.xml = None
        self.json = None
        self.__response = None
        self.__method = method
        
        if form is not None:
            assert not data, u'cannot have both form and data'
            assert not data_type, u'cannot specify data_type when using form'
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
                    data_type, data = encode_multipart_form_data(form, form_charset)
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
        self.xml = None
        self.json = None
        self.__response = None
        self._query_application(
            self.__url, self.__method, None, self.__data, self.__data_type)
        return self.status_code

    def get_form(self, name=None, id=None):
        assert self.html is not None, u'Not viewing HTML'
        expression = None
        if name is not None:
            expression = '//form[@name="%s"]' % name
        elif id is not None:
            expression = '//form[@id="%s"]' % id
        assert expression is not None, u'Provides an id or a name to get_form'
        if expression not in self.__cache:
            nodes = self.html.xpath(expression)
            assert len(nodes) == 1, 'Form element not found'
            self.__cache[expression] = Form(nodes[0], self)
        return self.__cache[expression]

    def get_link(self, content):
        assert self.html is not None, u'Not viewing HTML'
        urls = {}
        for link in self.html.xpath(
            '//a[contains(normalize-space(text()), "%s")]' % content):
            urls[link.attrib['href']] = link
        assert len(urls) == 1, u'No link found'
        return Link(urls.values()[0], self)

    def close(self):
        if 'close' in self.handlers:
            self.handlers.close(self)
