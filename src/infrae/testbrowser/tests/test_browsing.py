# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import operator
import os.path

from infrae.testbrowser.browser import Browser
from infrae.testbrowser.interfaces import IAdvancedBrowser
from infrae.testbrowser.tests import app, browser
from infrae.testbrowser.utils import File

from zope.interface.verify import verifyObject


class BrowsingTestCase(browser.BrowserTestCase):

    def Browser(self, app):
        return Browser(app)

    def test_no_open(self):
        with Browser(app.test_app_write) as browser:
            self.assertTrue(verifyObject(IAdvancedBrowser, browser))
            self.assertEqual(browser.options.server, 'localhost')
            self.assertEqual(browser.options.port, '80')
            self.assertEqual(browser.url, None)
            self.assertEqual(browser.location, None)
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
        with Browser(app.test_app_write) as browser:
            browser.open('http://localhost/index.html')
            self.assertEqual(browser.url, '/index.html')
            self.assertEqual(browser.location, '/index.html')
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
        with Browser(app.test_app_write) as browser:
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
        with Browser(app.test_app_empty) as browser:
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
            self.assertEqual(browser.xml, None)
            self.assertEqual(browser.json, None)

    def test_text(self):
        with Browser(app.test_app_text) as browser:
            browser.open('/readme.txt')
            self.assertEqual(browser.url, '/readme.txt')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.status_code, 200)
            self.assertEqual(browser.contents, 'Hello world!')
            self.assertEqual(browser.content_type, 'text/plain')
            self.assertEqual(browser.headers.get('Content-Type'), 'text/plain')
            self.assertEqual(browser.html, None)
            self.assertEqual(browser.xml, None)
            self.assertEqual(browser.json, None)

    def test_json(self):
        with Browser(app.test_app_json) as browser:
            browser.open('/data')
            self.assertEqual(browser.url, '/data')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.status_code, 200)
            self.assertEqual(browser.contents, '[true, false, 1, "a"]')
            self.assertEqual(browser.content_type, 'application/json')
            self.assertEqual(
                browser.headers.get('Content-Type'),
                'application/json')
            self.assertEqual(browser.html, None)
            self.assertEqual(browser.xml, None)
            self.assertEqual(browser.json, [True, False, 1, u'a'])

    def test_history(self):
        with Browser(app.test_app_iter) as browser:
            self.assertEqual(browser.history, [])

            browser.open('/index.html')
            self.assertEqual(browser.history, [])

            browser.open('/edit.html')
            self.assertEqual(browser.history, ['/index.html'])

            browser.open('/delete.html')
            self.assertEqual(browser.history, ['/index.html', '/edit.html'])

    def test_login_user_in_url(self):
        with Browser(app.test_app_headers) as browser:
            browser.open('http://user:password@localhost/index.html')
            self.assertEqual(browser.url, '/index.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//li/text()'),
                ['HTTP_AUTHORIZATION:Basic dXNlcjpwYXNzd29yZA=='])

    def test_login(self):
        with Browser(app.test_app_headers) as browser:
            browser.login('user', 'password')
            browser.open('http://localhost/index.html')
            self.assertEqual(browser.url, '/index.html')
            self.assertEqual(browser.location, '/index.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//li/text()'),
                ['HTTP_AUTHORIZATION:Basic dXNlcjpwYXNzd29yZA=='])

    def test_logout(self):
        with Browser(app.test_app_headers) as browser:
            browser.login('user', 'password')
            browser.open('http://localhost/index.html')
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//li/text()'),
                ['HTTP_AUTHORIZATION:Basic dXNlcjpwYXNzd29yZA=='])

            browser.logout()
            browser.reload()

            self.assertEqual(browser.url, '/index.html')
            self.assertEqual(browser.location, '/index.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//li/text()'),
                [])

    def test_set_and_headers(self):
        with Browser(app.test_app_headers) as browser:
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
        with Browser(app.TestAppCount()) as browser:
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
        with Browser(app.test_app_query) as browser:
            browser.open('http://localhost/root.html',
                         query={'position': '42', 'name': 'index'})
            self.assertEqual(browser.url, '/root.html?position=42&name=index')
            self.assertEqual(browser.location, '/root.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//li/text()'),
                ['METHOD: GET', 'URL: /root.html',
                 'QUERY: position=42&name=index'])

            browser.reload()
            self.assertEqual(browser.url, '/root.html?position=42&name=index')
            self.assertEqual(browser.status, '200 Ok')
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//li/text()'),
                ['METHOD: GET', 'URL: /root.html',
                 'QUERY: position=42&name=index'])

    def test_environ_default(self):
        # You can view and customize the default environ.
        with Browser(app.test_app_environ) as browser:
            browser.open('http://localhost/root.html')
            self.assertEqual(browser.location, '/root.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//li/text()'),
                ['PATH_INFO: /root.html',
                 'QUERY_STRING: ',
                 'REQUEST_METHOD: GET',
                 'SCRIPT_NAME: ',
                 'SERVER_NAME: localhost',
                 'SERVER_PORT: 80',
                 'SERVER_PROTOCOL: HTTP/1.0',
                 'wsgi.handleErrors: True',
                 'wsgi.multiprocess: False',
                 'wsgi.multithread: False',
                 'wsgi.run_once: False',
                 'wsgi.url_scheme: http',
                 'wsgi.version: (1, 0)'])

    def test_environ_changed_hostname(self):
        with Browser(app.test_app_environ) as browser:
            browser.options.server = 'example.com'
            browser.options.port = '8080'
            browser.open('http://example.com:8080/root.html')
            self.assertEqual(browser.location, '/root.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//li/text()'),
                ['PATH_INFO: /root.html',
                 'QUERY_STRING: ',
                 'REQUEST_METHOD: GET',
                 'SCRIPT_NAME: ',
                 'SERVER_NAME: example.com',
                 'SERVER_PORT: 8080',
                 'SERVER_PROTOCOL: HTTP/1.0',
                 'wsgi.handleErrors: True',
                 'wsgi.multiprocess: False',
                 'wsgi.multithread: False',
                 'wsgi.run_once: False',
                 'wsgi.url_scheme: http',
                 'wsgi.version: (1, 0)'])

    def test_environ_https_hostname(self):
        with Browser(app.test_app_environ) as browser:
            browser.options.server = 'admin.localhost'
            browser.options.port = '443'
            browser.open('/root.html')
            self.assertEqual(browser.location, '/root.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//li/text()'),
                ['HTTPS: on',
                 'PATH_INFO: /root.html',
                 'QUERY_STRING: ',
                 'REQUEST_METHOD: GET',
                 'SCRIPT_NAME: ',
                 'SERVER_NAME: admin.localhost',
                 'SERVER_PORT: 443',
                 'SERVER_PROTOCOL: HTTP/1.0',
                 'wsgi.handleErrors: True',
                 'wsgi.multiprocess: False',
                 'wsgi.multithread: False',
                 'wsgi.run_once: False',
                 'wsgi.url_scheme: https',
                 'wsgi.version: (1, 0)'])

    def test_environ_custom(self):
        # You can view and customize the default environ.
        browser = Browser(app.test_app_environ)
        browser.options.default_wsgi_environ = {'REMOTE_USER': 'hacker'}
        browser.open('http://localhost/root.html')
        self.assertEqual(browser.location, '/root.html')
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['PATH_INFO: /root.html',
             'QUERY_STRING: ',
             'REMOTE_USER: hacker',
             'REQUEST_METHOD: GET',
             'SCRIPT_NAME: ',
             'SERVER_NAME: localhost',
             'SERVER_PORT: 80',
             'SERVER_PROTOCOL: HTTP/1.0',
             'wsgi.handleErrors: True',
             'wsgi.multiprocess: False',
             'wsgi.multithread: False',
             'wsgi.run_once: False',
             'wsgi.url_scheme: http',
             'wsgi.version: (1, 0)'])

    def test_environ_query(self):
        # You can view and customize the default environ.
        browser = Browser(app.test_app_environ)
        browser.open('http://localhost/root.html',
                     query={'position': '42', 'name': 'index'},
                     method='POST')
        self.assertEqual(browser.status, '200 Ok')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['PATH_INFO: /root.html',
             'QUERY_STRING: position=42&name=index',
             'REQUEST_METHOD: POST',
             'SCRIPT_NAME: ',
             'SERVER_NAME: localhost',
             'SERVER_PORT: 80',
             'SERVER_PROTOCOL: HTTP/1.0',
             'wsgi.handleErrors: True',
             'wsgi.multiprocess: False',
             'wsgi.multithread: False',
             'wsgi.run_once: False',
             'wsgi.url_scheme: http',
             'wsgi.version: (1, 0)'])

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
        
    def test_open_put_with_data(self):
        browser = Browser(app.test_app_data)
        browser.open('http://localhost/root.exe',
                     method='PUT',
                     data='blah',
                     data_type='text/plain')
        self.assertEqual(browser.url, '/root.exe')
        self.assertEqual(browser.location, '/root.exe')
        self.assertEqual(browser.status, '200 Ok')
        self.assertEqual(browser.method, 'PUT')
        self.assertNotEqual(browser.html, None)
        self.assertEqual(
            browser.html.xpath('//li/text()'),
            ['content type:text/plain',
             'content length:4',
             'blah'])

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
        with Browser(app.test_app_data) as browser:
            with self.assertRaises(AssertionError):
                browser.open('http://localhost/root.exe',
                             method='GET',
                             form={'position': '42', 'name': 'index'},
                             query={'color': 'blue'})
            with self.assertRaises(AssertionError):
                browser.open('http://localhost/root.exe',
                             method='GET',
                             form={'position': '42', 'name': 'index'},
                             form_enctype='multipart/form-data')
            with self.assertRaises(AssertionError):
                browser.open('http://localhost/root.exe',
                             method='POST',
                             form={'position': '42', 'name': 'index'},
                             form_enctype='x-unknown/ultra-part')
            with self.assertRaises(AssertionError):
                browser.open('http://localhost/root.exe',
                             method='PUT',
                             form={'position': '42', 'name': 'index'})

    def test_disabled_redirect(self):
        with Browser(app.TestAppRedirect()) as browser:
            browser.options.follow_redirect = False
            browser.open('/redirect.html')
            self.assertEqual(browser.method, 'GET')
            self.assertEqual(browser.url, '/redirect.html')
            self.assertEqual(browser.status, '301 Moved Permanently')
            self.assertEqual(browser.contents, '')
            self.assertEqual(
                browser.headers.get('Location'),
                '/target.html')

    def test_get_permanent_redirect(self):
        with Browser(app.TestAppRedirect()) as browser:
            browser.open('/redirect.html')
            self.assertEqual(browser.method, 'GET')
            self.assertEqual(browser.url, '/target.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_head_permanent_redirect(self):
        with Browser(app.TestAppRedirect()) as browser:
            browser.open('/redirect.html', method='HEAD')
            self.assertEqual(browser.method, 'HEAD')
            self.assertEqual(browser.url, '/target.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_put_permanent_redirect(self):
        with Browser(app.TestAppRedirect()) as browser:
            browser.open('/redirect.html', method='PUT')
            self.assertEqual(browser.method, 'GET')
            self.assertEqual(browser.url, '/target.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_post_permanent_redirect(self):
        with Browser(app.TestAppRedirect()) as browser:
            browser.open('/redirect.html', method='POST')
            self.assertEqual(browser.method, 'GET')
            self.assertEqual(browser.url, '/target.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_get_temporary_redirect(self):
        with Browser(app.TestAppRedirect('302 Moved')) as browser:
            browser.open('/redirect.html')
            self.assertEqual(browser.method, 'GET')
            self.assertEqual(browser.url, '/target.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_head_temporary_redirect(self):
        with Browser(app.TestAppRedirect('302 Moved')) as browser:
            browser.open('/redirect.html', method='HEAD')
            self.assertEqual(browser.method, 'HEAD')
            self.assertEqual(browser.url, '/target.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_put_temporary_redirect(self):
        with Browser(app.TestAppRedirect('302 Moved')) as browser:
            browser.open('/redirect.html', method='PUT')
            self.assertEqual(browser.method, 'GET')
            self.assertEqual(browser.url, '/target.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_post_temporary_redirect(self):
        with Browser(app.TestAppRedirect('302 Moved')) as browser:
            browser.open('/redirect.html', method='POST')
            self.assertEqual(browser.method, 'GET')
            self.assertEqual(browser.url, '/target.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_get_temporary_redirect_absolute_url(self):
        with Browser(app.TestAppRedirect(
                code='302 Moved', url='https://other/index.html')) as browser:
            browser.open('/redirect.html', method='GET')
            self.assertEqual(browser.url, '/redirect.html')
            self.assertEqual(browser.status, '302 Moved')
            self.assertEqual(
                browser.headers.get('Location'),
                'https://other/index.html')

            browser.options.follow_external_redirect = True
            browser.reload()
            self.assertEqual(browser.options.server, 'other')
            self.assertEqual(browser.options.port, '443')
            self.assertEqual(browser.method, 'GET')
            self.assertEqual(browser.url, '/index.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')

    def test_get_permanent_redirect_absolute_url(self):
        with Browser(app.TestAppRedirect(
                url='https://other/index.html')) as browser:
            browser.open('/redirect.html', method='GET')
            self.assertEqual(browser.url, '/redirect.html')
            self.assertEqual(browser.status, '301 Moved Permanently')
            self.assertEqual(
                browser.headers.get('Location'),
                'https://other/index.html')

            browser.options.follow_external_redirect = True
            browser.reload()
            self.assertEqual(browser.options.server, 'other')
            self.assertEqual(browser.options.port, '443')
            self.assertEqual(browser.method, 'GET')
            self.assertEqual(browser.url, '/index.html')
            self.assertEqual(browser.status, '200 Ok')
            self.assertEqual(browser.contents, '<html><p>It works!</p></html>')
