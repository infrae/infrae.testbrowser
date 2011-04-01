# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from infrae.testbrowser.selenium.browser import Browser
from infrae.testbrowser.interfaces import IBrowser
from infrae.testbrowser.tests import app

from zope.interface.verify import verifyObject


class BrowsingTestCase(unittest.TestCase):

    def test_no_open(self):
        browser = Browser(app.test_app_write)
        self.assertTrue(verifyObject(IBrowser, browser))
        self.assertEqual(browser.url, None)
        self.assertEqual(browser.location, None)
        self.assertEqual(browser.contents, None)
        browser.close()

    def test_simple(self):
        browser = Browser(app.test_app_text)
        browser.open('/readme.txt')
        self.assertEqual(browser.location, '/readme.txt')
        self.assertTrue('Hello world!' in browser.contents)
        browser.close()

    def test_reload(self):
        browser = Browser(app.TestAppCount())
        browser.open('/root.html')
        self.assertEqual(browser.location, '/root.html')
        self.assertTrue('<p>Call 1, path /root.html</p>' in browser.contents)
        browser.reload()
        self.assertEqual(browser.location, '/root.html')
        self.assertTrue('<p>Call 2, path /root.html</p>' in browser.contents)
        browser.close()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BrowsingTestCase))
    return suite
