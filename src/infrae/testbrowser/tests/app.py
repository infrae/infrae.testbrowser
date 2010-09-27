# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import os

def test_app_write(environ, start_response):
    write = start_response('200 Ok', (('Content-type', 'text/html'),))
    write('<html>')
    write('<ul><li>SERVER: %s://%s:%s/</li>' % (
            environ['wsgi.url_scheme'],
            environ['SERVER_NAME'],
            environ['SERVER_PORT']))
    write('<li>METHOD: %s</li>' % environ['REQUEST_METHOD'])
    write('<li>URL: %s</li></ul></html>' % environ['PATH_INFO'])
    return []


def test_app_iter(environ, start_response):
    start_response('200 Ok', (('Content-type', 'text/html'),))
    return ['<html><ul><li>SERVER: %s://%s:%s/</li>' % (
            environ['wsgi.url_scheme'],
            environ['SERVER_NAME'],
            environ['SERVER_PORT']),
            '<li>METHOD: %s</li>' % environ['REQUEST_METHOD'],
            '<li>URL: %s</li></ul></html>' % environ['PATH_INFO']]


def test_app_headers(environ, start_response):
    start_response('200 Ok', (('Content-type', 'text/html'),))
    headers = map(lambda k: '<li>%s:%s</li>' % (k, environ[k]),
                  filter(lambda k: k.startswith('HTTP_'),
                         environ.keys()))
    return ['<html><ul>'] +  headers + ['</ul></html>']


def test_app_query(environ, start_response):
    start_response('200 Ok', (('Content-type', 'text/html'),))
    return ['<html><ul><li>METHOD: %s</li>' % environ['REQUEST_METHOD'],
            '<li>URL: %s</li>' % environ['PATH_INFO'],
            '<li>QUERY: %s</li></ul></html>' % environ['QUERY_STRING']]


def test_app_text(environ, start_response):
    start_response('200 Ok', (('Content-type', 'text/plain'),))
    return ['Hello world!']


def test_app_data(environ, start_response):
    start_response('200 Ok', (('Content-type', 'text/html'),))
    return ['<html><ul>',
            '<li>content type:%s</li>' % environ.get('CONTENT_TYPE', 'n/a'),
            '<li>content length:%s</li>' % environ.get('CONTENT_LENGTH', 'n/a'),
            '<li>%s</li></ul></html>' % environ['wsgi.input'].read()]


def test_app_empty(environ, start_response):
    start_response('200 Ok', (('Content-type', 'text/html'),))
    return []


class TestAppCount(object):

    def __init__(self):
        self.count = 0

    def __call__(self, environ, start_response):
        self.count += 1
        start_response('200 Ok', (('Content-type', 'text/html'),))
        return ['<html><p>Call %d, path %s</p></html>' % (
                self.count, environ['PATH_INFO'])]


class TestAppRedirect(object):

    def __init__(self, code='301 Moved Permanently'):
        self.code = code

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'] == '/redirect.html':
            start_response(self.code, (('Location', '/target.html'),))
            return []
        start_response('200 Ok', (('Content-type', 'text/html'),))
        return ['<html><p>It works!</p></html>']


class TestAppTemplate(object):

    def __init__(self, filename):
        self.filename = os.path.join(
            os.path.dirname(__file__), 'data', filename)

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'POST':
            start_response('200 Ok', (('Content-type', 'text/html'),))
            return ['<html><pre>%s</pre></html>' % environ['wsgi.input'].read()]
        with open(self.filename, 'r') as data:
            start_response('200 Ok', (('Content-type', 'text/html'),))
            return [data.read()]
        start_response('404 Not Found', (('Content-type', 'text/html')))
        return ['<html>File not found</html>']
