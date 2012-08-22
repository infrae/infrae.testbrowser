# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest
import operator

from infrae.testbrowser.tests import app
from infrae.testbrowser.interfaces import IForm


class ExpressionsTestCase(unittest.TestCase):

    def Browser(self, app):
        raise NotImplementedError

    def test_invalid_expressions(self):
        with self.Browser(app.test_app_text) as browser:
            self.assertRaises(
                AssertionError,
                browser.inspect.add, 'blue', '//li', type='blue')
            self.assertRaises(
                AttributeError,
                operator.attrgetter('noexisting'), browser.inspect)
            self.assertRaises(
                AssertionError,
                browser.inspect.add, 'simple')

    def test_text_xpath(self):
        with self.Browser(app.TestAppTemplate(
                'text_expressions.html')) as browser:
            browser.inspect.add('values', '//li')
            browser.inspect.add('ingredients', '//li/span', type='text')
            browser.open('/index.html')

            self.assertEqual(
                browser.inspect.values,
                ['Flour', 'Sugar', 'Chocolate', 'Butter'])
            self.assertEqual(
                browser.inspect.ingredients,
                ['Flour', 'Sugar', 'Butter'])

    def test_text_css(self):
        with self.Browser(app.TestAppTemplate(
                'text_expressions.html')) as browser:
            browser.inspect.add('values', css='li')
            browser.inspect.add('ingredients', css='span', type='text')
            browser.open('/index.html')

            self.assertEqual(
                browser.inspect.values,
                ['Flour', 'Sugar', 'Chocolate', 'Butter'])
            self.assertEqual(
                browser.inspect.ingredients,
                ['Flour', 'Sugar', 'Butter'])

            # You can call list on the inspect result.
            self.assertEqual(
                list(browser.inspect.values),
                ['Flour', 'Sugar', 'Chocolate', 'Butter'])

    def test_link_xpath(self):
        with self.Browser(app.TestAppTemplate(
                'link_expressions.html',
                default_headers={'Content-type': 'text/html; charset=utf-8'})) as browser:
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
            links['contact'].click()

            self.assertEqual(browser.location, '/contact.html')

    def test_link_css(self):
        with self.Browser(app.TestAppTemplate(
                'link_expressions.html',
                default_headers={'Content-type': 'text/html; charset=utf-8'})) as browser:
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

    def test_unique_xpath(self):
        with self.Browser(app.TestAppTemplate(
                'link_expressions.html',
                default_headers={'Content-type': 'text/html; charset=utf-8'})) as browser:
            browser.inspect.add(
                'title', '//h1', unique=True)
            browser.inspect.add(
                'address', '//address/a', type='link', unique=True)
            browser.inspect.add(
                'navigation', css='ul.navigation a', type='link', unique=True)
            browser.inspect.add(
                'footer', css='p.footer', unique=True)

            browser.open('/development/lisp.html')
            self.assertEqual(
                browser.inspect.title,
                'Links')
            self.assertNotEqual(
                browser.inspect.title,
                'Tchernobyl')
            self.assertEqual(
                browser.inspect.address,
                'Sylvain Viollon')
            self.assertNotEqual(
                browser.inspect.address,
                'Arthur de Pandragor')
            self.assertEqual(
                browser.inspect.address.url,
                'mailto:sylvain@infrae.com')
            self.assertEqual(
                browser.inspect.footer,
                None)
            self.assertRaises(
                AssertionError,
                operator.attrgetter('navigation'), browser.inspect)

    def test_form_css(self):
        with self.Browser(app.TestAppTemplate('nameless_form.html')) as browser:
            browser.inspect.add('form', css='form', type='form')
            browser.open('/access.html')
            self.assertEqual(
                map(lambda f: IForm.providedBy(f), browser.inspect.form),
                [True, True])
            self.assertEqual(
                map(lambda f: f.action, browser.inspect.form),
                ['/submit.html', '/transaction.html'])
            self.assertTrue(IForm.providedBy(browser.inspect.form[0]))
            self.assertTrue(IForm.providedBy(browser.inspect.form[1]))

    def test_http_encoding(self):
        with self.Browser(app.TestAppTemplate(
                'utf8_index.html',
                default_headers={'Content-type': 'text/html; charset=utf-8'})) as browser:
            browser.open('/index.html')
            browser.inspect.add('values', '//p')
            self.assertEqual(browser.inspect.values, [u'âccèntùâtïon'])
