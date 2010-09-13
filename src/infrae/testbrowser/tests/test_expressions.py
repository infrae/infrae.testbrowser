# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import operator
import unittest

from infrae.testbrowser.tests import app
from infrae.testbrowser.browser import Browser


class ExpressionsTestCase(unittest.TestCase):

    def test_no_html(self):
        browser = Browser(app.test_app_text)

        self.assertRaises(
            AssertionError,
            browser.inspect.add, 'blue', '//li', type='blue')

        browser.inspect.add('list', '//li')
        browser.open('/index.html')

        self.assertRaises(
            AssertionError,
            operator.attrgetter('list'), browser.inspect)
        self.assertRaises(
            AttributeError,
            operator.attrgetter('noexisting'), browser.inspect)

    def test_text(self):
        browser = Browser(app.TestAppTemplate('text_expressions.html'))
        browser.inspect.add('values', '//li')
        browser.inspect.add('ingredients', '//li/span', type='text')
        browser.open('/index.html')

        self.assertEqual(
            browser.inspect.values,
            ['Flour', 'Sugar', 'Chocolate', 'Butter'])
        self.assertEqual(
            browser.inspect.ingredients,
            ['Flour', 'Sugar', 'Butter'])

    def test_link(self):
        browser = Browser(app.TestAppTemplate('link_expressions.html'))
        browser.inspect.add(
            'navigation', '//ul[@class="navigation"]/li/a', type='link')
        browser.inspect.add(
            'breadcrumbs', '//ul[@class="breadcrumbs"]/li/a', type='link')

        browser.open('/development/lisp.html')
        self.assertEqual(
            browser.inspect.navigation,
            ['Home', 'Contact', 'python'])
        self.assertEqual(
            browser.inspect.breadcrumbs,
            ['Home ...', 'Development ...', 'Advanced Lisp ...'])
        self.assertNotEqual(
            browser.inspect.navigation,
            ['Home', 'python'])
        self.assertEqual(
            repr(browser.inspect.navigation),
            repr(['Home', 'Contact', 'python']))

        self.assertEqual(
            browser.inspect.breadcrumbs.keys(),
            ['Home ...', 'Development ...', 'Advanced Lisp ...'])
        self.assertEqual(len(browser.inspect.breadcrumbs), 3)

        links = browser.inspect.navigation
        self.assertTrue('home' in links)
        self.assertTrue('Home' in links)
        self.assertFalse('download' in links)

        self.assertEqual(repr(links['contact']), repr('Contact'))
        self.assertEqual(links['contact'].title, 'Contact')
        self.assertEqual(links['contact'].url, '/contact.html')
        self.assertEqual(links['contact'].click(), 200)

        self.assertEqual(browser.url, '/contact.html')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExpressionsTestCase))
    return suite
