# -*- coding: utf-8 -*-
# Copyright (c) 2010-2011 Infrae. All rights reserved.
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
        self.assertRaises(
            AttributeError,
            operator.attrgetter('noexisting'), browser.inspect)
        self.assertRaises(
            AssertionError,
            browser.inspect.add, 'simple')

        browser.inspect.add('list', '//li')
        browser.inspect.add('definition', css='dd.definition')
        browser.open('/index.html')

        self.assertRaises(
            AssertionError,
            operator.attrgetter('list'), browser.inspect)

    def test_text_xpath(self):
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

        # You can call list of the inspect result.
        self.assertEqual(
            list(browser.inspect.values),
            ['Flour', 'Sugar', 'Chocolate', 'Butter'])

    def test_http_encoding(self):
        browser = Browser(
            app.TestAppTemplate(
                'utf8_index.html',
                default_headers={'Content-type': 'text/html; charset=utf-8'}))
        browser.open('/index.html')
        browser.inspect.add('values', '//p')
        self.assertEqual(browser.inspect.values, [u'âccèntùâtïon'])

    def test_no_http_encoding(self):
        browser = Browser(app.TestAppTemplate('utf8_index.html'))
        browser.open('/index.html')
        browser.inspect.add('values', '//p')
        # we get a latin1 interpretation of utf-8
        self.assertEqual(browser.inspect.values,
                         [u'âccèntùâtïon'.encode('utf-8').decode('latin1')])

    def test_text_css(self):
        browser = Browser(app.TestAppTemplate('text_expressions.html'))
        browser.inspect.add('values', css='li')
        browser.inspect.add('ingredients', css='span', type='text')
        browser.open('/index.html')

        self.assertEqual(
            browser.inspect.values,
            ['Flour', 'Sugar', 'Chocolate', 'Butter'])
        self.assertEqual(
            browser.inspect.ingredients,
            ['Flour', 'Sugar', 'Butter'])

        # You can call list of the inspect result.
        self.assertEqual(
            list(browser.inspect.values),
            ['Flour', 'Sugar', 'Chocolate', 'Butter'])

    def test_link_xpath(self):
        browser = Browser(
            app.TestAppTemplate(
                'link_expressions.html',
                default_headers={'Content-type': 'text/html; charset=utf-8'}))
        browser.inspect.add(
            'navigation', '//ul[@class="navigation"]/li/a', type='link')
        browser.inspect.add(
            'breadcrumbs', '//ul[@class="breadcrumbs"]/li/a', type='link')

        browser.open('/development/lisp.html')
        self.assertEqual(
            browser.inspect.navigation,
            ['Home', 'Contact', 'Contact Abroad', 'python'])
        self.assertEqual(
            browser.inspect.breadcrumbs,
            [u'Home ...',
             u'Development ...',
             u'Advanced Lisp ...',
             u'Échange culturel ...'])
        self.assertNotEqual(
            browser.inspect.navigation,
            ['Home', 'python'])
        self.assertEqual(
            repr(browser.inspect.navigation),
            repr([u'Home', u'Contact', u'Contact Abroad', u'python']))
        self.assertEqual(
            map(lambda l: l.url, browser.inspect.navigation.values()),
            ['/home.html', '/contact.html',
             '/contact_abroad.html', '/development/python.html'])

        self.assertEqual(
            browser.inspect.breadcrumbs.keys(),
            [u'Home ...',
             u'Development ...',
             u'Advanced Lisp ...',
             u'Échange culturel ...'])
        self.assertEqual(len(browser.inspect.breadcrumbs), 4)

        # In the same fashion you can iter through it as a list.
        self.assertEqual(
            repr(list(browser.inspect.breadcrumbs)),
            repr(['Home ...',
                  'Development ...',
                  'Advanced Lisp ...',
                  'Échange culturel ...']))

        links = browser.inspect.navigation
        self.assertTrue('home' in links)
        self.assertTrue('Home' in links)
        self.assertFalse('download' in links)

        self.assertEqual(repr(links['contact']), repr('Contact'))
        self.assertEqual(links['contact'].text, 'Contact')
        self.assertEqual(links['contact'].url, '/contact.html')
        self.assertEqual(links['contact'].click(), 200)

        self.assertEqual(browser.url, '/contact.html')

    def test_link_css(self):
        browser = Browser(
            app.TestAppTemplate(
                'link_expressions.html',
                default_headers={'Content-type': 'text/html; charset=utf-8'}))
        browser.inspect.add(
            'navigation', css='ul.navigation a', type='link')
        browser.inspect.add(
            'breadcrumbs', css='ul.breadcrumbs a', type='link')

        browser.open('/development/lisp.html')
        self.assertEqual(
            browser.inspect.navigation,
            ['Home', 'Contact', 'Contact Abroad', 'python'])
        self.assertEqual(
            browser.inspect.breadcrumbs,
            [u'Home ...',
             u'Development ...',
             u'Advanced Lisp ...',
             u'Échange culturel ...'])
        self.assertNotEqual(
            browser.inspect.navigation,
            ['Home', 'python'])
        self.assertEqual(
            repr(browser.inspect.navigation),
            repr([u'Home', u'Contact', u'Contact Abroad', u'python']))
        self.assertEqual(
            map(lambda l: l.url, browser.inspect.navigation.values()),
            ['/home.html', '/contact.html',
             '/contact_abroad.html', '/development/python.html'])

        self.assertEqual(
            browser.inspect.breadcrumbs.keys(),
            [u'Home ...',
             u'Development ...',
             u'Advanced Lisp ...',
             u'Échange culturel ...'])
        self.assertEqual(len(browser.inspect.breadcrumbs), 4)

        # In the same fashion you can iter through it as a list.
        self.assertEqual(
            repr(list(browser.inspect.breadcrumbs)),
            repr(['Home ...',
                  'Development ...',
                  'Advanced Lisp ...',
                  'Échange culturel ...']))

    def test_normalized_spaces_xpath(self):
        browser = Browser(app.TestAppTemplate('normalized_spaces.html'))
        browser.inspect.add(
            'menu', xpath='//ul[@class="menu"]/li', type='normalized-text')
        browser.inspect.add(
            'raw_menu', xpath='//ul[@class="menu"]/li', type='text')

        browser.open('/index.html')
        self.assertEqual(
            browser.inspect.menu,
            ['Home', 'Development ( tradional way )', 'Modern development'])
        self.assertEqual(
            browser.inspect.raw_menu,
            ['Home', 'Development\n( tradional    way\n)', 'Modern\n\ndevelopment'])

    def test_normalized_spaces_css(self):
        browser = Browser(app.TestAppTemplate('normalized_spaces.html'))
        browser.inspect.add(
            'menu', css='ul.menu li', type='normalized-text')
        browser.inspect.add(
            'raw_menu', css='ul.menu li', type='text')

        browser.open('/index.html')
        self.assertEqual(
            browser.inspect.menu,
            ['Home', 'Development ( tradional way )', 'Modern development'])
        self.assertEqual(
            browser.inspect.raw_menu,
            ['Home', 'Development\n( tradional    way\n)', 'Modern\n\ndevelopment'])

