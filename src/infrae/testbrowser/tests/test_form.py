# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import os.path
import unittest

from infrae.testbrowser.browser import Browser
from infrae.testbrowser.interfaces import IForm, IFormControl
from infrae.testbrowser.tests import app, form

from zope.interface.verify import verifyObject


class FormTestCase(form.FormSupportTestCase):

    def Browser(self, app):
        return Browser(app)

    def test_malformed_form(self):
        with Browser(app.TestAppTemplate('malformed_form.html')) as browser:
            browser.open('/index.html?option=on')
            form = browser.get_form('malform')
            # This form has no action. It default to the browser location
            self.assertEqual(form.name, 'malform')
            self.assertEqual(form.method, 'POST')
            self.assertEqual(form.action, '/index.html')
            self.assertEqual(len(form.controls), 2)

    def test_form_cache(self):
        # If you find a form and set a value it must be keept for the
        # opened URL.
        with Browser(app.TestAppTemplate('simple_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('loginform')
            self.assertTrue(verifyObject(IForm, form))

            field = form.get_control('login')
            self.assertEqual(field.value, 'arthur')
            field.value = 'something i changed'
            self.assertEqual(field.value, 'something i changed')

            second_form = browser.get_form('loginform')
            second_field = second_form.get_control('login')
            self.assertEqual(second_field.value, 'something i changed')

            # Reload, and the cache is gone
            browser.open('/index.html')
            third_form = browser.get_form('loginform')
            third_field = third_form.get_control('login')
            self.assertEqual(third_field.value, 'arthur')

    def test_multi_hidden_input(self):
        """Support for multiple fields
        """
        with Browser(app.TestAppTemplate('multi_hidden_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('form')

            self.assertEqual(len(form.controls), 3)
            hidden_field = form.get_control('secret')
            self.assertNotEqual(hidden_field, None)
            self.assertTrue(verifyObject(IFormControl, hidden_field))
            self.assertEqual(hidden_field.value, ['First', 'Second'])
            self.assertEqual(hidden_field.type, 'hidden')
            self.assertEqual(hidden_field.multiple, True)
            self.assertEqual(hidden_field.checkable, False)
            self.assertEqual(hidden_field.checked, False)
            self.assertEqual(hidden_field.options, [])

            # The field is for two values, you can only set two of them
            self.assertRaises(
                AssertionError,
                setattr, hidden_field, 'value', 'One')
            self.assertRaises(
                AssertionError,
                setattr, hidden_field, 'value', ['One', 'Two', 'Three'])

            hidden_field.value = ['One', 'Two']
            self.assertEqual(hidden_field.value, ['One', 'Two'])

            # Submit the form
            submit_field = form.get_control('save')
            self.assertEqual(submit_field.submit(), 200)
            self.assertEqual(browser.url, '/submit.html')
            self.assertEqual(browser.method, 'POST')
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['secret: One', 'secret: Two', 'save: Save'])

    def test_file_input(self):
        with Browser(app.TestAppTemplate('file_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('feedbackform')
            self.assertNotEqual(form, None)
            self.assertEqual(len(form.controls), 2)

            file_field = form.get_control('document')
            self.assertNotEqual(file_field, None)
            self.assertTrue(verifyObject(IFormControl, file_field))
            self.assertEqual(file_field.value, '')
            self.assertEqual(file_field.type, 'file')
            self.assertEqual(file_field.multiple, False)
            self.assertEqual(file_field.checkable, False)
            self.assertEqual(file_field.checked, False)
            self.assertEqual(file_field.options, [])

            file_field.value = os.path.join(
                os.path.dirname(__file__), 'data', 'readme.txt')

            submit_field = form.get_control('send')
            self.assertEqual(submit_field.submit(), 200)
            self.assertEqual(browser.url, '/submit.html')
            self.assertEqual(browser.method, 'POST')
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['document: You should readme.\nNow.\n', 'send: Send'])

    def test_file_input_no_file_selected(self):
        with Browser(app.TestAppTemplate('file_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('feedbackform')
            self.assertNotEqual(form, None)
            self.assertEqual(len(form.controls), 2)

            submit_field = form.get_control('send')
            self.assertEqual(submit_field.submit(), 200)
            self.assertEqual(browser.url, '/submit.html')
            self.assertEqual(browser.method, 'POST')
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['send: Send'])

    def test_lxml_regression(self):
        browser = Browser(app.TestAppTemplate('lxml_regression.html'))
        browser.open('/index.html')
        form = browser.get_form(id='regressions')
        self.assertNotEqual(form, None)
        self.assertEqual(len(form.controls), 1)

        strange_button = form.get_control('refresh')
        self.assertNotEqual(strange_button, None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FormTestCase))
    return suite
