# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import os
import urlparse

def test_app_write(environ, start_response):
    write = start_response('200 Ok', [('Content-type', 'text/html'),])
    write('<html>')
    write('<ul><li>SERVER: %s://%s:%s/</li>' % (
            environ['wsgi.url_scheme'],
            environ['SERVER_NAME'],
            environ['SERVER_PORT']))
    write('<li>METHOD: %s</li>' % environ['REQUEST_METHOD'])
    write('<li>URL: %s</li></ul></html>' % environ['PATH_INFO'])
    return []


def test_app_iter(environ, start_response):
    start_response('200 Ok', [('Content-type', 'text/html'),])
    return ['<html><ul><li>SERVER: %s://%s:%s/</li>' % (
            environ['wsgi.url_scheme'],
            environ['SERVER_NAME'],
            environ['SERVER_PORT']),
            '<li>METHOD: %s</li>' % environ['REQUEST_METHOD'],
            '<li>URL: %s</li></ul></html>' % environ['PATH_INFO']]


def test_app_headers(environ, start_response):
    start_response('200 Ok', [('Content-type', 'text/html'),])
    headers = map(lambda k: '<li>%s:%s</li>' % (k, environ[k]),
                  filter(lambda k: k.startswith('HTTP_'),
                         environ.keys()))
    return ['<html><ul>'] +  headers + ['</ul></html>']


def test_app_query(environ, start_response):
    start_response('200 Ok', [('Content-type', 'text/html'),])
    return ['<html><ul><li>METHOD: %s</li>' % environ['REQUEST_METHOD'],
            '<li>URL: %s</li>' % environ['PATH_INFO'],
            '<li>QUERY: %s</li></ul></html>' % environ['QUERY_STRING']]


def test_app_text(environ, start_response):
    start_response('200 Ok', [('Content-type', 'text/plain'),])
    return ['Hello world!']


def test_app_json(environ, start_response):
    start_response('200 Ok', [('Content-type', 'application/json')])
    return ['[true, false, 1, "a"]']


def test_app_data(environ, start_response):
    start_response('200 Ok', [('Content-type', 'text/html'),])
    return ['<html><ul>',
            '<li>content type:%s</li>' % environ.get('CONTENT_TYPE', 'n/a'),
            '<li>content length:%s</li>' % environ.get('CONTENT_LENGTH', 'n/a'),
            '<li>%s</li></ul></html>' % environ['wsgi.input'].read()]

def test_app_environ(environ, start_response):
    start_response('200 Ok' , [('Content-type', 'text/html'),])
    yield '<html><ul>'
    for key in sorted(environ.keys()):
        if key not in ('wsgi.input', 'wsgi.errors'):
            # We ignore file containers
            yield '<li>%s: %s</li>' % (str(key), str(environ[key]))
    yield '</ul></html>'

def test_app_empty(environ, start_response):
    start_response('200 Ok', [('Content-type', 'text/html'),])
    return []


def test_app_cookies_server(environ, start_response):
    headers = [('Content-type', 'text/html')]
    if 'HTTP_COOKIE' not in environ.keys():
        # No cookies, set cookies !
        headers.append(('Set-Cookie', 'browser=testing;Path=/'))
    start_response('200 Ok', headers)
    yield '<html><ul>'
    if 'HTTP_COOKIE' in environ.keys():
        # Cookies, display them !
        for cookie in environ['HTTP_COOKIE'].split(';'):
            yield '<li>' + cookie.strip() + '</li>'
    yield '</ul></html>'

def test_app_cookies_client(environ, start_response):
    headers = [('Content-type', 'text/html')]
    start_response('200 Ok', headers)
    yield '<html><ul>'
    if 'HTTP_COOKIE' in environ.keys():
        # Cookies, display them !
        for cookie in environ['HTTP_COOKIE'].split(';'):
            yield '<li>' + cookie.strip() + '</li>'
    yield '</ul></html>'


class TestAppCount(object):

    def __init__(self):
        self.counts = {}

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        count = self.counts.get(path, 0)
        count += 1
        self.counts[path] = count
        start_response('200 Ok', [('Content-type', 'text/html'),])
        return ['<html><p>Call %d, path %s</p></html>' % (count, path)]


class TestAppRedirect(object):

    def __init__(self, code='301 Moved Permanently', url='/target.html'):
        self.code = code
        self.url = url

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'] == '/redirect.html':
            start_response(self.code, [('Location', self.url),])
            return []
        start_response('200 Ok', [('Content-type', 'text/html'),])
        return ['<html><p>It works!</p></html>']


class TestAppTemplate(object):

    def __init__(self, filename, default_headers=None):
        self.filename = os.path.join(
            os.path.dirname(__file__), 'data', filename)
        self.default_headers = default_headers or {}

    def __call__(self, environ, start_response):
        headers = {'Content-type': 'text/html'}
        headers.update(self.default_headers)
        if environ['REQUEST_METHOD'] == 'POST':
            start_response('200 Ok', headers.items())
            environ_length = environ.get('CONTENT_LENGTH')
            length = int(environ_length) if environ_length else 0
            data = urlparse.parse_qsl(environ['wsgi.input'].read(length))
            return ['<html><ul>%s</ul></html>' % ''.join(map(
                        lambda v: '<li>%s: %s</li>' % (v[0], ''.join(v[1])), data))]
        with open(self.filename, 'r') as data:
            start_response('200 Ok', headers.items())
            return [data.read()]
        start_response('404 Not Found', headers.items())
        return ['<html>File not found</html>']
