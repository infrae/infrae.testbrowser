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
