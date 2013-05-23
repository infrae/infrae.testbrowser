# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from infrae.testbrowser.selenium.browser import Browser
from infrae.testbrowser.interfaces import IBrowser
from infrae.testbrowser.tests import app, browser

from zope.interface.verify import verifyObject


class BrowsingTestCase(browser.BrowserTestCase):

    def Browser(self, app):
        return Browser(app)

    def test_no_open(self):
        with Browser(app.test_app_write) as browser:
            self.assertTrue(verifyObject(IBrowser, browser))
            self.assertEqual(browser.url, None)
            self.assertEqual(browser.location, None)
            self.assertEqual(browser.contents, None)

    def test_simple(self):
        with Browser(app.test_app_text) as browser:
            browser.open('/readme.txt')
            self.assertEqual(browser.location, '/readme.txt')
            self.assertTrue('Hello world!' in browser.contents)

    def test_environ(self):
        with Browser(app.test_app_environ) as browser:
            browser.open('/root+to%E2%80%A6.html?v=%E2%88%9A')
            self.assertEqual(browser.location, '/root+to%E2%80%A6.html')
            self.assertNotEqual(browser.html, None)
            environ = dict(
                map(lambda s: map(lambda t: t.strip(), s.split(':', 1)),
                    browser.html.xpath('//li/text()')))
            for key, value in {'PATH_INFO': u'/root+to….html',
                               'QUERY_STRING': 'v=%E2%88%9A',
                               'REQUEST_METHOD': 'GET'}.iteritems():
                self.assertIn(key, environ)
                self.assertEqual(environ[key], value)

    def test_reload(self):
        with Browser(app.TestAppCount()) as browser:
            browser.open('/root.html')
            self.assertEqual(browser.location, '/root.html')
            self.assertIn('<p>Call 1, path /root.html</p>', browser.contents)
            browser.reload()
            self.assertEqual(browser.location, '/root.html')
            self.assertIn('<p>Call 2, path /root.html</p>', browser.contents)


