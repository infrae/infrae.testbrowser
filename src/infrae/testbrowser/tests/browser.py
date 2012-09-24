# -*- coding: utf-8 -*-
# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.interface.verify import verifyObject
from infrae.testbrowser.interfaces import ICookie, ICookies
from infrae.testbrowser.tests import app


class BrowserTestCase(unittest.TestCase):

    def Browser(self, app):
        raise NotImplementedError

    def test_cookies_server(self):
        """Test that cookies set by the server are available.
        """
        with self.Browser(app.test_app_cookies_server) as browser:
            self.assertTrue(verifyObject(ICookies, browser.cookies))
            self.assertEqual(len(browser.cookies), 0)
            self.assertEqual(browser.cookies.keys(), [])
            self.assertNotIn('browser', browser.cookies)
            self.assertEqual(repr(browser.cookies), '<no cookies>')
            browser.open('/page.html')
            self.assertEqual(len(browser.cookies), 1)
            self.assertEqual(browser.cookies, ['browser'])
            self.assertTrue(verifyObject(ICookie, browser.cookies['browser']))
            self.assertEqual(browser.cookies['browser'].name, 'browser')
            self.assertEqual(browser.cookies['browser'].value, 'testing')
            self.assertIn('browser', browser.cookies)
            # No cookies set:
            self.assertNotEqual(browser.html, None)
            self.assertEqual(browser.html.xpath('//ul/li/text()'), [])
            browser.reload()
            # Cookies should now be set:
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['browser=testing'])
            self.assertEqual(len(browser.cookies), 1)
            self.assertEqual(browser.cookies, ['browser'])
            self.assertEqual(browser.cookies['browser'].value, 'testing')
            self.assertEqual(repr(browser.cookies), 'browser=testing')

    def test_cookies_client(self):
        """Test cookies can be set by the client.
        """
        with self.Browser(app.test_app_cookies_client) as browser:
            self.assertEqual(len(browser.cookies), 0)
            self.assertEqual(browser.cookies.keys(), [])
            self.assertNotIn('food', browser.cookies)
            browser.open('/page.html')
            self.assertEqual(len(browser.cookies), 0)
            self.assertEqual(browser.cookies.keys(), [])
            self.assertNotIn('food', browser.cookies)
            # No cookies are visible
            self.assertNotEqual(browser.html, None)
            self.assertEqual(browser.html.xpath('//ul/li/text()'), [])
            browser.cookies.add('food', 'vegetables')
            self.assertEqual(len(browser.cookies), 1)
            self.assertEqual(browser.cookies, ['food'])
            self.assertEqual(browser.cookies['food'].value, 'vegetables')
            self.assertIn('food', browser.cookies)
            browser.reload()
            # Cookie should be here
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['food=vegetables'])
            # Can add a second one
            browser.cookies.add('drink', 'sparkling water')
            self.assertEqual(len(browser.cookies), 2)
            self.assertEqual(browser.cookies, ['food', 'drink'])
            self.assertIn('food', browser.cookies)
            self.assertIn('drink', browser.cookies)
            browser.reload()
            # Cookies should be here
            self.assertNotEqual(browser.html, None)
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['food=vegetables', 'drink=sparkling water'])
            # You can clear all cookies
            browser.cookies.clear()
            self.assertEqual(len(browser.cookies), 0)
            self.assertEqual(browser.cookies.keys(), [])
            self.assertNotIn('food', browser.cookies)
            self.assertNotIn('drink', browser.cookies)
            browser.reload()
            # No cookies are visible
            self.assertNotEqual(browser.html, None)
            self.assertEqual(browser.html.xpath('//ul/li/text()'), [])

    def test_handlers(self):
        called = []

        class LoginHandler(object):
            def login(self, browser, user, password):
                called.append(('login', user, password))
            def logout(self, browser):
                called.append(('logout',))

        browser = self.Browser(app.test_app_write)
        browser.handlers.add('login', LoginHandler())
        browser.handlers.add('close', lambda browser: called.append(('close',)))

        with browser:
            browser.open('/index.html')
            browser.login('admin', 'admin')
            browser.logout()

        self.assertEquals(
            called,
            [('login', 'admin', 'admin'), ('logout',), ('close',)])
