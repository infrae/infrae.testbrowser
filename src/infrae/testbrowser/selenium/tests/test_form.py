# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from infrae.testbrowser.interfaces import IForm, IFormControl
from infrae.testbrowser.selenium.browser import Browser
from infrae.testbrowser.tests import app

from zope.interface.verify import verifyObject


class FormTestCase(unittest.TestCase):

    def test_invalid_form_name_or_id(self):
        with Browser(app.test_app_text) as browser:
            browser.open('/index.html')
            self.assertRaises(
                AssertionError, browser.get_form, 'form')

        with Browser(app.TestAppTemplate('simple_form.html')) as browser:
            browser.open('/index.html')
            self.assertRaises(
                AssertionError, browser.get_form)
            self.assertRaises(
                AssertionError, browser.get_form, 'notexisting')

    def test_nameless_form(self):
        with Browser(app.TestAppTemplate('nameless_form.html')) as browser:
            browser.open('/index.html?option=on')
            self.assertRaises(
                AssertionError, browser.get_form, name='loginform')
            form = browser.get_form(id='loginform')
            self.assertTrue(verifyObject(IForm, form))
            self.assertEqual(form.name, None)
            self.assertEqual(form.method, 'POST')
            self.assertEqual(form.action, '/submit.html')
            self.assertEqual(len(form.controls), 3)

    def test_simple_input(self):
        with Browser(app.TestAppTemplate('simple_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('loginform')
            self.assertNotEqual(form, None)
            self.assertEqual(form.name, 'loginform')
            self.assertEqual(form.method, 'POST')
            self.assertEqual(form.action, '/submit.html')
            self.assertEqual(len(form.controls), 3)

            self.assertRaises(
                AssertionError, form.get_control, 'notexisting')

            login_field = form.get_control('login')
            self.assertNotEqual(login_field, None)
            self.assertTrue(verifyObject(IFormControl, login_field))
            self.assertEqual(login_field.value, 'arthur')
            self.assertEqual(login_field.type, 'text')
            self.assertEqual(login_field.multiple, False)
            self.assertEqual(login_field.checkable, False)
            self.assertEqual(login_field.checked, False)
            self.assertEqual(login_field.options, [])

            # Cannot set value to a list
            self.assertRaises(
                AssertionError, setattr, login_field, 'value', ['me'])

            password_field = form.get_control('password')
            self.assertNotEqual(password_field, None)
            self.assertTrue(verifyObject(IFormControl, password_field))
            self.assertEqual(password_field.value, '')
            self.assertEqual(password_field.type, 'password')
            self.assertEqual(password_field.multiple, False)
            self.assertEqual(password_field.checkable, False)
            self.assertEqual(password_field.checked, False)
            self.assertEqual(password_field.options, [])

            # Can only set string values
            self.assertRaises(
                AssertionError, setattr, password_field, 'value', ['something'])
            password_field.value = u'secret'

            submit_field = form.get_control('save')
            self.assertNotEqual(submit_field, None)
            self.assertTrue(verifyObject(IFormControl, submit_field))
            self.assertEqual(submit_field.value, 'Save')
            self.assertEqual(submit_field.type, 'submit')
            self.assertEqual(submit_field.multiple, False)
            self.assertEqual(submit_field.checkable, False)
            self.assertEqual(submit_field.checked, False)
            self.assertEqual(submit_field.options, [])
            self.assertTrue(hasattr(submit_field, 'submit'))
            submit_field.submit()

            self.assertEqual(browser.location, '/submit.html')
            self.assertTrue(
                '<ul><li>login: arthur</li><li>password: secret</li><li>save: Save</li></ul>'
                in browser.contents)

    def test_select(self):
        with Browser(app.TestAppTemplate('select_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('langform')
            self.assertNotEqual(form, None)
            self.assertEqual(len(form.controls), 3)

            select_field = form.get_control('language')
            self.assertNotEqual(select_field, None)
            self.assertTrue(verifyObject(IFormControl, select_field))
            self.assertEqual(select_field.value, 'Python')
            self.assertEqual(select_field.type, 'select')
            self.assertEqual(select_field.multiple, False)
            self.assertEqual(select_field.checkable, False)
            self.assertEqual(select_field.checked, False)
            self.assertEqual(
                select_field.options,
                ['C', 'Java', 'Erlang', 'Python', 'Lisp'])

            self.assertRaises(
                AssertionError, setattr, select_field, 'value', 'C#')
            select_field.value = 'C'
            self.assertEqual(select_field.value, 'C')

            submit_field = form.get_control('choose')
            submit_field.submit()

            self.assertEqual(browser.location, '/submit.html')
            self.assertTrue(
                '<ul><li>choose: Choose</li><li>giberish: German</li><li>language: C</li></ul>'
                in browser.contents)

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
