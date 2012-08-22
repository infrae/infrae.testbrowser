# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import operator

from infrae.testbrowser.tests import app, expressions
from infrae.testbrowser.browser import Browser


class ExpressionsTestCase(expressions.ExpressionsTestCase):

    def Browser(self, app):
        return Browser(app)

    def test_no_html(self):
        with Browser(app.test_app_text) as browser:
            browser.inspect.add('list', '//li')
            browser.inspect.add('definition', css='dd.definition')
            browser.open('/index.html')

            self.assertRaises(
                AssertionError,
                operator.attrgetter('list'), browser.inspect)

    def test_no_http_encoding(self):
        with Browser(app.TestAppTemplate('utf8_index.html')) as browser:
            browser.open('/index.html')
            browser.inspect.add('values', '//p')
            # we get a latin1 interpretation of utf-8
            self.assertEqual(browser.inspect.values,
                             [u'âccèntùâtïon'.encode('utf-8').decode('latin1')])

    def test_normalized_spaces_xpath(self):
        with Browser(app.TestAppTemplate('normalized_spaces.html')) as browser:
            browser.inspect.add(
                'menu', xpath='//ul[@class="menu"]/li', type='normalized-text')
            browser.inspect.add(
                'raw_menu', xpath='//ul[@class="menu"]/li', type='text')

            browser.open('/index.html')
            self.assertEqual(
                browser.inspect.menu,
                ['Home',
                 'Development ( tradional way )',
                 'Modern development'])
            self.assertEqual(
                browser.inspect.raw_menu,
                ['Home',
                 'Development\n( tradional    way\n)',
                 'Modern\n\ndevelopment'])

    def test_normalized_spaces_css(self):
        with Browser(app.TestAppTemplate('normalized_spaces.html')) as browser:
            browser.inspect.add(
                'menu', css='ul.menu li', type='normalized-text')
            browser.inspect.add(
                'raw_menu', css='ul.menu li', type='text')

            browser.open('/index.html')
            self.assertEqual(
                browser.inspect.menu,
                ['Home',
                 'Development ( tradional way )',
                 'Modern development'])
            self.assertEqual(
                browser.inspect.raw_menu,
                ['Home',
                 'Development\n( tradional    way\n)',
                 'Modern\n\ndevelopment'])

