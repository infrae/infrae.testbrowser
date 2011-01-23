# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest
import operator
import os.path

from infrae.testbrowser.browser import Browser
from infrae.testbrowser.interfaces import IBrowser
from infrae.testbrowser.tests import app
from infrae.testbrowser.utils import File

from zope.interface.verify import verifyObject

class BrowsingTestCase(unittest.TestCase):

    def test_no_open(self):
        browser = Browser(app.test_app_write)
        self.assertTrue(verifyObject(IBrowser, browser))
        self.assertEqual(browser.url, None)
        self.assertEqual(browser.method, None)
        self.assertEqual(browser.status, None)
        self.assertEqual(browser.status_code, None)
        self.assertEqual(browser.contents, None)
        self.assertEqual(browser.headers, {})
        self.assertEqual(browser.content_type, None)
        self.assertEqual(browser.headers.get('Content-Type'), None)
        self.assertRaises(
            KeyError, operator.itemgetter('Nothing'), browser.headers)
        self.assertEqual(browser.html, None)
        self.assertRaises(
            AssertionError, browser.reload)

    def test_write(self):
        browser = Browser(app.test_app_write)
        browser.open('http://localhost/index.html')
        self.assertEqual(browser.url, '/index.html')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.status_code, 200)
        self.assertEqual(
            browser.contents,
            '<html><ul>'
            '<li>SERVER: http://localhost:80/</li>'
            '<li>METHOD: GET</li>'
            '<li>URL: /index.html</li>'
            '</ul></html>')
        self.assertEqual(browser.headers, {'content-type': 'text/html'})
        self.assertEqual(browser.content_type, 'text/html')
        self.assertEqual(browser.headers.get('Content-Type'), 'text/html')
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['SERVER: http://localhost:80/',
             'METHOD: GET',
             'URL: /index.html'])
        self.assertNotEqual(browser.html, None)

    def test_write_relative_open_with_method(self):
        browser = Browser(app.test_app_write)
        browser.open('/index.html', method='PUT')
        self.assertEqual(browser.url, '/index.html')
        self.assertEqual(browser.method, 'PUT')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.status_code, 200)
        self.assertEqual(
            browser.contents,
            '<html><ul>'
            '<li>SERVER: http://localhost:80/</li>'
            '<li>METHOD: PUT</li>'
            '<li>URL: /index.html</li>'
            '</ul></html>')
        self.assertEqual(browser.headers, {'content-type': 'text/html'})
        self.assertEqual(browser.content_type, 'text/html')
        self.assertEqual(browser.headers.get('Content-Type'), 'text/html')
        self.assertNotEqual(browser.html, None)

    def test_iterator(self):
        browser = Browser(app.test_app_iter)
        browser.open('/index.html', method='PUT')
        self.assertEqual(browser.url, '/index.html')
        self.assertEqual(browser.method, 'PUT')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.status_code, 200)
        self.assertEqual(
            browser.contents,
            '<html><ul>'
            '<li>SERVER: http://localhost:80/</li>'
            '<li>METHOD: PUT</li>'
            '<li>URL: /index.html</li>'
            '</ul></html>')
        self.assertEqual(browser.headers, {'content-type': 'text/html'})
        self.assertEqual(browser.content_type, 'text/html')
        self.assertEqual(browser.headers.get('Content-Type'), 'text/html')
        self.assertNotEqual(browser.html, None)

    def test_iterator_fragment(self):
        browser = Browser(app.test_app_iter)
        browser.open('/index.html#Bottom', method='GET')
        self.assertEqual(browser.url, '/index.html#Bottom')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.status_code, 200)
        self.assertEqual(
            browser.contents,
            '<html><ul>'
            '<li>SERVER: http://localhost:80/</li>'
            '<li>METHOD: GET</li>'
            '<li>URL: /index.html</li>'
            '</ul></html>')

    def test_iterator_empty(self):
        browser = Browser(app.test_app_empty)
        browser.open('/index.html')
        self.assertEqual(browser.url, '/index.html')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.status_code, 200)
        self.assertEqual(browser.contents, '')
        self.assertEqual(browser.headers, {'content-type': 'text/html'})
        self.assertEqual(browser.content_type, 'text/html')
        self.assertEqual(browser.headers.get('Content-Type'), 'text/html')
        self.assertEqual(browser.html, None)

    def test_text(self):
        browser = Browser(app.test_app_text)
        browser.open('/readme.txt')
        self.assertEqual(browser.url, '/readme.txt')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.status_code, 200)
        self.assertEqual(browser.contents, 'Hello world!')
        self.assertEqual(browser.content_type, 'text/plain')
        self.assertEqual(browser.headers.get('Content-Type'), 'text/plain')
        self.assertEqual(browser.html, None)

    def test_history(self):
        browser = Browser(app.test_app_iter)
        self.assertEqual(browser.history, [])

        browser.open('/index.html')
        self.assertEqual(browser.history, [])

        browser.open('/edit.html')
        self.assertEqual(browser.history, ['/index.html'])

        browser.open('/delete.html')
        self.assertEqual(browser.history, ['/index.html', '/edit.html'])

    def test_login_user_in_url(self):
        browser = Browser(app.test_app_headers)
        browser.open('http://user:password@localhost/index.html')
        self.assertEqual(browser.url, '/index.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['HTTP_AUTHORIZATION:Basic dXNlcjpwYXNzd29yZA=='])

    def test_login(self):
        browser = Browser(app.test_app_headers)
        browser.login('user', 'password')
        browser.open('http://localhost/index.html')
        self.assertEqual(browser.url, '/index.html')
        self.assertEqual(browser.location, '/index.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['HTTP_AUTHORIZATION:Basic dXNlcjpwYXNzd29yZA=='])

    def test_set_and_headers(self):
        browser = Browser(app.test_app_headers)
        browser.set_request_header('Accept', 'text/html')
        self.assertEqual(browser.get_request_header('Accept'), 'text/html')
        browser.set_request_header('If-Modified-Since', 'Now')
        browser.open('http://localhost/index.html')
        self.assertEqual(browser.url, '/index.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['HTTP_ACCEPT:text/html', 'HTTP_IF_MODIFIED_SINCE:Now'])

        browser.clear_request_headers()
        browser.reload()
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(browser.html.xpath('//li/text()'), [])

    def test_reload(self):
        browser = Browser(app.TestAppCount())
        browser.open('http://localhost/root.html')
        self.assertEqual(browser.url, '/root.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(
            browser.contents,
            '<html><p>Call 1, path /root.html</p></html>')
        self.assertEqual(browser.history, [])

        browser.reload()
        self.assertEqual(browser.url, '/root.html')
        self.assertEqual(browser.location, '/root.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(
            browser.contents,
            '<html><p>Call 2, path /root.html</p></html>')
        self.assertEqual(browser.history, [])

    def test_query(self):
        browser = Browser(app.test_app_query)
        browser.open('http://localhost/root.html',
                     query={'position': '42', 'name': 'index'})
        self.assertEqual(browser.url, '/root.html?position=42&name=index')
        self.assertEqual(browser.location, '/root.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['METHOD: GET', 'URL: /root.html', 'QUERY: position=42&name=index'])

        browser.reload()
        self.assertEqual(browser.url, '/root.html?position=42&name=index')
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['METHOD: GET', 'URL: /root.html', 'QUERY: position=42&name=index'])

    def test_form_post(self):
        browser = Browser(app.test_app_data)
        browser.open('http://localhost/root.exe',
                     method='POST',
                     form={'position': '42', 'name': 'index'})
        self.assertEqual(browser.url, '/root.exe')
        self.assertEqual(browser.location, '/root.exe')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.method, 'POST')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['content type:application/x-www-form-urlencoded',
             'content length:22',
             'position=42&name=index'])

        browser.reload()
        self.assertEqual(browser.url, '/root.exe')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.method, 'POST')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['content type:application/x-www-form-urlencoded',
             'content length:22',
             'position=42&name=index'])

    def test_form_post_multipart(self):
        browser = Browser(app.test_app_data)
        browser.open('http://localhost/root.exe',
                     method='POST',
                     form={'position': '42', 'name': 'index'},
                     form_enctype='multipart/form-data')
        self.assertEqual(browser.url, '/root.exe')
        self.assertEqual(browser.location, '/root.exe')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.method, 'POST')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['content type:multipart/form-data; '
             'boundary=------------uCtemt3iWu00F3QDhiwZ2nIQ$',
             'content length:234',
             '--------------uCtemt3iWu00F3QDhiwZ2nIQ$\r\n'
             'Content-Disposition: form-data; name="position"\r\n\r\n42\r\n'
             '--------------uCtemt3iWu00F3QDhiwZ2nIQ$\r\n'
             'Content-Disposition: form-data; name="name"\r\n\r\nindex\r\n'
             '--------------uCtemt3iWu00F3QDhiwZ2nIQ$--\r\n'])

        browser.reload()
        self.assertEqual(browser.url, '/root.exe')
        self.assertEqual(browser.location, '/root.exe')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.method, 'POST')

    def test_form_post_multipart_file(self):
        browser = Browser(app.test_app_data)
        filename = os.path.join(os.path.dirname(__file__), 'data', 'readme.txt')
        browser.open('http://localhost/root.exe',
                     method='POST',
                     form={'name': 'index', 'file': File(filename)},
                     form_enctype='multipart/form-data')
        self.assertEqual(browser.url, '/root.exe')
        self.assertEqual(browser.location, '/root.exe')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.method, 'POST')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['content type:multipart/form-data; '
             'boundary=------------uCtemt3iWu00F3QDhiwZ2nIQ$',
             'content length:%d' % (291 + len(filename)),
             '--------------uCtemt3iWu00F3QDhiwZ2nIQ$\r\n'
             'Content-Disposition: form-data; name="name"\r\n\r\nindex\r\n'
             '--------------uCtemt3iWu00F3QDhiwZ2nIQ$\r\n'
             'Content-Disposition: form-data; name="file"; filename="%s"\r\n'
             'Content-Type: text/plain\r\n\r\n'
             'You should readme.\nNow.\n\r\n'
             '--------------uCtemt3iWu00F3QDhiwZ2nIQ$--\r\n' % (filename)])

    def test_form_get(self):
        browser = Browser(app.test_app_data)
        browser.open('http://localhost/root.exe',
                     method='GET',
                     form={'position': '42', 'name': 'index'})
        self.assertEqual(browser.url, '/root.exe?position=42&name=index')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['content type:n/a',
             'content length:n/a'])

        browser.reload()
        self.assertEqual(browser.url, '/root.exe?position=42&name=index')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['content type:n/a',
             'content length:n/a'])

    def test_form_invalid(self):
        browser = Browser(app.test_app_data)
        self.assertRaises(
            AssertionError,
            browser.open, 'http://localhost/root.exe',
            method='GET',
            form={'position': '42', 'name': 'index'},
            query={'color': 'blue'})
        self.assertRaises(
            AssertionError,
            browser.open, 'http://localhost/root.exe',
            method='GET',
            form={'position': '42', 'name': 'index'},
            form_enctype='multipart/form-data')
        self.assertRaises(
            AssertionError,
            browser.open, 'http://localhost/root.exe',
            method='POST',
            form={'position': '42', 'name': 'index'},
            form_enctype='x-unknown/ultra-part')
        self.assertRaises(
            AssertionError,
            browser.open, 'http://localhost/root.exe',
            method='PUT',
            form={'position': '42', 'name': 'index'})

    def test_disabled_redirect(self):
        browser = Browser(app.TestAppRedirect())
        browser.options.follow_redirect = False
        browser.open('/redirect.html')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.url, '/redirect.html')
        self.assertEqual(browser.status, '301 Moved Permanently')
        self.assertEqual(browser.contents, '')

    def test_get_permanent_redirect(self):
        browser = Browser(app.TestAppRedirect())
        browser.open('/redirect.html')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.url, '/target.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_head_permanent_redirect(self):
        browser = Browser(app.TestAppRedirect())
        browser.open('/redirect.html', method='HEAD')
        self.assertEqual(browser.method, 'HEAD')
        self.assertEqual(browser.url, '/target.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_put_permanent_redirect(self):
        browser = Browser(app.TestAppRedirect())
        browser.open('/redirect.html', method='PUT')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.url, '/target.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_post_permanent_redirect(self):
        browser = Browser(app.TestAppRedirect())
        browser.open('/redirect.html', method='POST')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.url, '/target.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_get_temporary_redirect(self):
        browser = Browser(app.TestAppRedirect('302 Moved'))
        browser.open('/redirect.html')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.url, '/target.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_head_temporary_redirect(self):
        browser = Browser(app.TestAppRedirect('302 Moved'))
        browser.open('/redirect.html', method='HEAD')
        self.assertEqual(browser.method, 'HEAD')
        self.assertEqual(browser.url, '/target.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_put_temporary_redirect(self):
        browser = Browser(app.TestAppRedirect('302 Moved'))
        browser.open('/redirect.html', method='PUT')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.url, '/target.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_post_temporary_redirect(self):
        browser = Browser(app.TestAppRedirect('302 Moved'))
        browser.open('/redirect.html', method='POST')
        self.assertEqual(browser.method, 'GET')
        self.assertEqual(browser.url, '/target.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.contents, '<html><p>It works!</p></html>')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BrowsingTestCase))
    return suite
