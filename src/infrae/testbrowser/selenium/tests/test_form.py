# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from infrae.testbrowser.interfaces import IForm
from infrae.testbrowser.interfaces import IFormControl
from infrae.testbrowser.interfaces import IClickableFormControl
from infrae.testbrowser.interfaces import ISubmitableFormControl
from infrae.testbrowser.selenium.browser import Browser
from infrae.testbrowser.tests import app, form

from zope.interface.verify import verifyObject


class FormTestCase(form.FormSupportTestCase):

    def Browser(self, app):
        return Browser(app)

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
                ['save: Save', 'secret: One', 'secret: Two'])

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
                ['save: Save', 'secret: Eerste', 'secret: Tweede', 'secret: Derde'])

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
            submit_field.submit()

            self.assertEqual(browser.location, '/submit.html')
            self.assertTrue(
                '<ul><li>choose: Choose</li><li>language: C</li><li>language: Python</li><li>language: Lisp</li></ul>'
                in browser.contents)

    def test_textarea(self):
        with Browser(app.TestAppTemplate('textarea_form.html')) as browser:
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
            self.assertEqual(textarea_field.value, 'A really blue sky')

            submit_field = form.get_control('save')
            submit_field.submit()

            self.assertEqual(browser.location, '/submit.html')
            self.assertTrue(
                '<ul><li>comment: A really blue sky</li><li>save: Save</li></ul>'
                in browser.contents)

    def test_radio_input(self):
        with Browser(app.TestAppTemplate('radio_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('feedbackform')
            self.assertNotEqual(form, None)
            self.assertEqual(len(form.controls), 2)

            radio_field = form.get_control('adapter')
            self.assertNotEqual(radio_field, None)
            self.assertTrue(verifyObject(IFormControl, radio_field))
            self.assertEqual(radio_field.value, 'No')
            self.assertEqual(radio_field.type, 'radio')
            self.assertEqual(radio_field.multiple, False)
            self.assertEqual(radio_field.checkable, False)
            self.assertEqual(radio_field.checked, False)
            self.assertEqual(radio_field.options, ['Yes', 'No'])

            # You are limitied the options to set the value. No list are
            # authorized.
            self.assertRaises(
                AssertionError, setattr, radio_field, 'value', 'Maybe')
            self.assertRaises(
                AssertionError, setattr, radio_field, 'value', ['Yes'])
            radio_field.value = 'Yes'
            self.assertEqual(radio_field.value, 'Yes')

            submit_field = form.get_control('send')
            submit_field.submit()

            self.assertEqual(browser.location, '/submit.html')
            self.assertTrue(
                '<ul><li>adapter: Yes</li><li>send: Send</li></ul>'
                in browser.contents)

    def test_button(self):
        with Browser(app.TestAppTemplate('button_form.html')) as browser:
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

            form = browser.get_form('dreamform')
            save_button = form.get_control('save')
            self.assertTrue(verifyObject(ISubmitableFormControl, save_button))
            save_button.submit()
