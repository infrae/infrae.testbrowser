# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from infrae.testbrowser.tests import app
from infrae.testbrowser.browser import Browser


class FormTestCase(unittest.TestCase):

    def test_get_form(self):
        browser = Browser(app.test_app_text)
        self.assertRaises(
            AssertionError, browser.get_form, 'form')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FormTestCase))
    return suite
