# -*- coding: utf-8 -*-
# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import os.path
import unittest

from infrae.testbrowser.browser import Browser
from infrae.testbrowser.interfaces import IForm, IFormControl
from infrae.testbrowser.interfaces import IClickableFormControl
from infrae.testbrowser.interfaces import ISubmitableFormControl
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
        browser = Browser(app.TestAppTemplate('simple_form.html'))
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

    def test_multi_mixed_input(self):
        with Browser(app.TestAppTemplate('multi_mixed_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('form')

            self.assertEqual(len(form.controls), 3)
            hidden_field = form.get_control('secret')
            self.assertNotEqual(hidden_field, None)
            self.assertTrue(verifyObject(IFormControl, hidden_field))
            self.assertEqual(hidden_field.value, ['First', 'Second', 'Third'])
            self.assertEqual(hidden_field.type, 'mixed')
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
                setattr, hidden_field, 'value', ['One', 'Two'])

            hidden_field.value = ['Eerste', 'Tweede', 'Derde']
            self.assertEqual(hidden_field.value, ['Eerste', 'Tweede', 'Derde'])

            # Submit the form
            submit_field = form.get_control('save')
            self.assertEqual(submit_field.submit(), 200)
            self.assertEqual(browser.url, '/submit.html')
            self.assertEqual(browser.method, 'POST')
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['secret: Eerste', 'secret: Tweede', 'secret: Derde', 'save: Save'])

    def test_multi_select(self):
        with Browser(app.TestAppTemplate('multiselect_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('langform')
            self.assertNotEqual(form, None)
            self.assertEqual(len(form.controls), 2)

            select_field = form.get_control('language')
            self.assertNotEqual(select_field, None)
            self.assertTrue(verifyObject(IFormControl, select_field))
            self.assertEqual(select_field.value, ['C', 'Python'])
            self.assertEqual(select_field.type, 'select')
            self.assertEqual(select_field.multiple, True)
            self.assertEqual(select_field.checkable, False)
            self.assertEqual(select_field.checked, False)
            self.assertEqual(
                select_field.options,
                ['C', 'Java', 'Erlang', 'Python', 'Lisp'])

            self.assertRaises(
                AssertionError, setattr, select_field, 'value', 'C#')
            select_field.value = 'Erlang'
            self.assertEqual(select_field.value, ['Erlang'])
            select_field.value = ['C', 'Python', 'Lisp']
            self.assertEqual(select_field.value, ['C', 'Python', 'Lisp'])

            submit_field = form.get_control('choose')
            self.assertEqual(submit_field.submit(), 200)
            self.assertEqual(browser.url, '/submit.html')
            self.assertEqual(browser.method, 'POST')
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['language: C', 'language: Python', 'language: Lisp', 'choose: Choose'])

    def test_textarea(self):
        browser = Browser(app.TestAppTemplate('textarea_form.html'))
        browser.open('/index.html')
        form = browser.get_form('commentform')
        self.assertNotEqual(form, None)
        self.assertEqual(len(form.controls), 2)

        textarea_field = form.get_control('comment')
        self.assertNotEqual(textarea_field, None)
        self.assertTrue(verifyObject(IFormControl, textarea_field))
        self.assertEqual(textarea_field.value, 'The sky is blue')
        self.assertEqual(textarea_field.type, 'textarea')
        self.assertEqual(textarea_field.multiple, False)
        self.assertEqual(textarea_field.checkable, False)
        self.assertEqual(textarea_field.checked, False)
        self.assertEqual(textarea_field.options, [])

        self.assertRaises(
            AssertionError, setattr, textarea_field, 'value', ['A list'])

        textarea_field.value = 'A really blue sky'
        submit_field = form.get_control('save')
        self.assertEqual(submit_field.submit(), 200)
        self.assertEqual(browser.url, '/submit.html')
        self.assertEqual(browser.method, 'POST')
        self.assertEqual(
            browser.html.xpath('//ul/li/text()'),
            ['comment: A really blue sky', 'save: Save'])

    def test_file_input(self):
        browser = Browser(app.TestAppTemplate('file_form.html'))
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
        browser = Browser(app.TestAppTemplate('file_form.html'))
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

    def test_button(self):
        browser = Browser(app.TestAppTemplate('button_form.html'))
        browser.open('/index.html')
        form = browser.get_form('dreamform')
        self.assertNotEqual(form, None)
        self.assertEqual(len(form.controls), 4)

        cancel_button = form.get_control('cancel')
        self.assertTrue(verifyObject(ISubmitableFormControl, cancel_button))
        cancel_button.click()

        browser.open('/index.html')
        form = browser.get_form('dreamform')
        lost_button = form.get_control('lost')
        self.assertTrue(verifyObject(IClickableFormControl, lost_button))
        self.assertFalse(ISubmitableFormControl.providedBy(lost_button))
        lost_button.click()     # This does nothing.

        save_button = form.get_control('save')
        self.assertTrue(verifyObject(ISubmitableFormControl, save_button))
        save_button.submit()

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
