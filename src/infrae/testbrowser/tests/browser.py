# -*- coding: utf-8 -*-
# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from infrae.testbrowser.tests import app


class BrowserTestCase(unittest.TestCase):

    def Browser(self):
        raise NotImplementedError

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
