# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import os.path
import unittest

from infrae.testbrowser.browser import Browser
from infrae.testbrowser.form import parse_charset
from infrae.testbrowser.interfaces import IForm, IFormControl
from infrae.testbrowser.tests import app

from zope.interface.verify import verifyObject


class FormTestCase(unittest.TestCase):

    def test_parse_charset(self):
        self.assertEqual(
            parse_charset('utf-8'),
            ['utf-8'])
        self.assertEqual(
            parse_charset('utf-8,latin-1 ISO-8859-1 , invalid'),
            ['utf-8', 'iso8859-1'])
        self.assertEqual(
            parse_charset('invalid ,, invalid utf8'),
            ['utf-8'])

    def test_invalid_form_name_or_id(self):
        browser = Browser(app.test_app_text)
        browser.open('/index.html')
        self.assertRaises(
            AssertionError, browser.get_form, 'form')

        browser = Browser(app.TestAppTemplate('simple_form.html'))
        browser.open('/index.html')
        self.assertRaises(
            AssertionError, browser.get_form)
        self.assertRaises(
            AssertionError, browser.get_form, 'notexisting')

    def test_nameless_form(self):
        browser = Browser(app.TestAppTemplate('nameless_form.html'))
        browser.open('/index.html?option=on')
        self.assertRaises(
            AssertionError, browser.get_form, name='loginform')
        form = browser.get_form(id='loginform')
        self.assertTrue(verifyObject(IForm, form))
        self.assertEqual(form.name, None)
        self.assertEqual(form.method, 'POST')
        self.assertEqual(form.action, '/submit.html')
        self.assertEqual(len(form.controls), 3)

    def test_malformed_form(self):
        browser = Browser(app.TestAppTemplate('malformed_form.html'))
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

    def test_simple_input(self):
        browser = Browser(app.TestAppTemplate('simple_form.html'))
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

        self.assertEqual(submit_field.submit(), 200)
        self.assertEqual(browser.url, '/submit.html')
        self.assertEqual(browser.method, 'POST')
        self.assertEqual(
            browser.html.xpath('//pre/text()'),
            ['login=arthur&password=secret&save=Save'])

    def test_checkbox_input(self):
        browser = Browser(app.TestAppTemplate('checkbox_form.html'))
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
        self.assertEqual(submit_field.submit(), 200)
        self.assertEqual(browser.url, '/submit.html')
        self.assertEqual(browser.method, 'POST')
        self.assertEqual(
            browser.html.xpath('//pre/text()'),
            ['true=Yes&send=Send'])

    def test_multi_checkbox_input(self):
        browser = Browser(app.TestAppTemplate('multicheckbox_form.html'))
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
        self.assertEqual(submit_field.submit(), 200)
        self.assertEqual(browser.url, '/submit.html')
        self.assertEqual(browser.method, 'POST')
        self.assertEqual(
            browser.html.xpath('//pre/text()'),
            ['language=C&language=Python&language=Lisp&choose=Choose'])

    def test_select(self):
        browser = Browser(app.TestAppTemplate('select_form.html'))
        browser.open('/index.html')
        form = browser.get_form('langform')
        self.assertNotEqual(form, None)
        self.assertEqual(len(form.controls), 2)

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
        self.assertEqual(submit_field.submit(), 200)
        self.assertEqual(browser.url, '/submit.html')
        self.assertEqual(browser.method, 'POST')
        self.assertEqual(
            browser.html.xpath('//pre/text()'),
            ['choose=Choose&language=C'])

    def test_multi_select(self):
        browser = Browser(app.TestAppTemplate('multiselect_form.html'))
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
            browser.html.xpath('//pre/text()'),
            ['choose=Choose&language=C&language=Python&language=Lisp'])

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
            browser.html.xpath('//pre/text()'),
            ['save=Save&comment=A+really+blue+sky'])

    def test_radio_input(self):
        browser = Browser(app.TestAppTemplate('radio_form.html'))
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
        self.assertEqual(submit_field.submit(), 200)
        self.assertEqual(browser.url, '/submit.html')
        self.assertEqual(browser.method, 'POST')
        self.assertEqual(
            browser.html.xpath('//pre/text()'),
            ['adapter=Yes&send=Send'])

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
            browser.html.xpath('//pre/text()'),
            ['document=You+should+readme.%0ANow.%0A&send=Send'])

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
            browser.html.xpath('//pre/text()'),
            ['document=&send=Send'])

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
