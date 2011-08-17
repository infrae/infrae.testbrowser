# -*- coding: utf-8 -*-
# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from infrae.testbrowser.interfaces import IForm, IFormControl
from infrae.testbrowser.interfaces import ISubmitableFormControl
from infrae.testbrowser.tests import app

from zope.interface.verify import verifyObject


class FormSupportTestCase(unittest.TestCase):

    def Browser(self, app):
        raise NotImplementedError

    def test_invalid_form_name_or_id(self):
        with self.Browser(app.test_app_text) as browser:
            browser.open('/index.html')
            self.assertRaises(
                AssertionError, browser.get_form, 'form')

        with self.Browser(app.TestAppTemplate('simple_form.html')) as browser:
            browser.open('/index.html')
            self.assertRaises(
                AssertionError, browser.get_form)
            self.assertRaises(
                AssertionError, browser.get_form, 'notexisting')

    def test_nameless_form(self):
        with self.Browser(app.TestAppTemplate('nameless_form.html')) as browser:
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
        with self.Browser(app.TestAppTemplate('simple_form.html')) as browser:
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
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['login: arthur', 'password: secret', 'save: Save'])

    def test_default_input(self):
        # Test that input and button defaults to the correct type
        with self.Browser(app.TestAppTemplate('default_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('loginform')
            self.assertNotEqual(form, None)
            self.assertEqual(len(form.controls), 3)

            input_field = form.get_control('login')
            self.assertNotEqual(input_field, None)
            self.assertTrue(verifyObject(IFormControl, input_field))
            self.assertEqual(input_field.value, 'arthur')
            self.assertEqual(input_field.type, 'text')
            self.assertEqual(input_field.multiple, False)
            self.assertEqual(input_field.checkable, False)
            self.assertEqual(input_field.checked, False)
            self.assertEqual(input_field.options, [])

            button_field = form.get_control('save')
            self.assertNotEqual(button_field, None)
            self.assertTrue(verifyObject(ISubmitableFormControl, button_field))
            self.assertEqual(button_field.value, '')
            self.assertEqual(button_field.type, 'submit')
            self.assertEqual(button_field.multiple, False)
            self.assertEqual(button_field.checkable, False)
            self.assertEqual(button_field.checked, False)
            self.assertEqual(button_field.options, [])

    def test_checkbox_input(self):
        with self.Browser(app.TestAppTemplate('checkbox_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('isitrueform')
            self.assertNotEqual(form, None)
            self.assertEqual(len(form.controls), 3)

            true_field = form.get_control('true')
            self.assertNotEqual(true_field, None)
            self.assertTrue(verifyObject(IFormControl, true_field))
            self.assertEqual(true_field.value, '')
            self.assertEqual(true_field.type, 'checkbox')
            self.assertEqual(true_field.multiple, False)
            self.assertEqual(true_field.checkable, True)
            self.assertEqual(true_field.checked, False)
            self.assertEqual(true_field.options, [])

            false_field = form.get_control('false')
            self.assertNotEqual(false_field, None)
            self.assertTrue(verifyObject(IFormControl, false_field))
            self.assertEqual(false_field.value, 'No')
            self.assertEqual(false_field.type, 'checkbox')
            self.assertEqual(false_field.multiple, False)
            self.assertEqual(false_field.checkable, True)
            self.assertEqual(false_field.checked, True)
            self.assertEqual(false_field.options, [])

            true_field.checked = True
            false_field.checked = False
            self.assertEqual(true_field.value, 'Yes')
            self.assertEqual(true_field.checked, True)
            self.assertEqual(false_field.value, '')
            self.assertEqual(false_field.checked, False)

            submit_field = form.get_control('send')
            submit_field.submit()

            self.assertEqual(browser.location, '/submit.html')
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['send: Send', 'true: Yes'])

    def test_multi_checkbox_input(self):
        with self.Browser(app.TestAppTemplate('multicheckbox_form.html')) as browser:
            browser.open('/index.html')
            form = browser.get_form('langform')
            self.assertNotEqual(form, None)
            self.assertEqual(len(form.controls), 2)

            multicheck_field = form.get_control('language')
            self.assertNotEqual(multicheck_field, None)
            self.assertTrue(verifyObject(IFormControl, multicheck_field))
            self.assertEqual(multicheck_field.value, ['Python', 'Lisp'])
            self.assertEqual(multicheck_field.type, 'checkbox')
            self.assertEqual(multicheck_field.multiple, True)
            self.assertEqual(multicheck_field.checkable, False)
            self.assertEqual(multicheck_field.checked, False)
            self.assertEqual(
                multicheck_field.options,
                ['C', 'Java', 'Erlang', 'Python', 'Lisp'])

            self.assertRaises(
                AssertionError, setattr, multicheck_field, 'value', 'C#')
            multicheck_field.value = 'Erlang'
            self.assertEqual(multicheck_field.value, ['Erlang'])
            multicheck_field.value = ['C', 'Python', 'Lisp']
            self.assertEqual(multicheck_field.value, ['C', 'Python', 'Lisp'])

            submit_field = form.get_control('choose')
            submit_field.submit()

            self.assertEqual(browser.location, '/submit.html')
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['choose: Choose', 'language: C',
                 'language: Python', 'language: Lisp'])

    def test_select(self):
        with self.Browser(app.TestAppTemplate('select_form.html')) as browser:
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

            other_select_field = form.get_control('giberish')
            self.assertNotEqual(other_select_field, None)
            self.assertTrue(verifyObject(IFormControl, other_select_field))
            self.assertEqual(other_select_field.value, 'German')
            self.assertEqual(other_select_field.type, 'select')
            self.assertEqual(other_select_field.multiple, False)
            self.assertEqual(other_select_field.checkable, False)
            self.assertEqual(other_select_field.checked, False)
            self.assertEqual(
                other_select_field.options,
                ['German', 'French'])

            submit_field = form.get_control('choose')
            submit_field.submit()

            self.assertEqual(browser.location, '/submit.html')
            self.assertEqual(
                browser.html.xpath('//ul/li/text()'),
                ['choose: Choose', 'giberish: German', 'language: C'])
