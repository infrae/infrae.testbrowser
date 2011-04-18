# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from infrae.testbrowser.interfaces import IFormControl, IForm
from infrae.testbrowser.utils import parse_charset, resolve_location

from zope.interface import implements


class Control(object):
    implements(IFormControl)

    def __init__(self, form, element):
        self.form = form
        self._element = element
        self.__name = element.get_attribute('name')
        assert self.__name is not None
        self.__multiple = False
        if element.tag_name == 'select':
            self.__type = 'select'
        else:
            if element.tag_name == 'textarea':
                self.__type = 'textarea'
            else:
                self.__type = element.get_attribute('type') or 'submit'
            self.__options = []
        self.__checked = False

    @apply
    def name():
        def getter(self):
            return self.__name
        return property(getter)

    @apply
    def type():
        def getter(self):
            return self.__type
        return property(getter)

    @apply
    def value():
        def getter(self):
            return self._element.value
        def setter(self, value):
            if not isinstance(value, basestring):
                raise AssertionError(u'Multiple values not accepted for this field')
            self._element.send_keys(value)
        return property(getter, setter)

    @apply
    def multiple():
        def getter(self):
            return self.__multiple
        return property(getter)

    @apply
    def options():
        def getter(self):
            return self.__options
        return property(getter)

    @apply
    def checkable():
        def getter(self):
            return self.__type in ['checkbox', 'radio'] and not self.__options
        return property(getter)

    @apply
    def checked():
        def getter(self):
            return self.__checked
        def setter(self, value):
            assert self.checkable, u"Not checkable"
            self.__checked = bool(value)
        return property(getter, setter)

    def _extend(self, html):
        pass


class ButtonControl(Control):

    def click(self):
        self._element.click()

    submit = click


FORM_ELEMENT_IMPLEMENTATION = {
    'submit': ButtonControl,
    'image': ButtonControl}


class Form(object):
    implements(IForm)

    def __init__(self, element):
        self.name = element.get_attribute('name') or None
        self.action = None
        action = element.get_attribute('action')
        if action:
            self.action = resolve_location(action)
        self.method = (element.get_attribute('method') or 'POST').upper()
        self.enctype = element.get_attribute('enctype') or 'application/x-www-form-urlencoded'
        self.accept_charset = parse_charset(element.get_attribute('accept-charset') or 'utf-8')
        self.controls = {}
        self.__element = element
        self.__populate_controls()

    def __populate_controls(self):
        for input_element in self.__element.find_elements_by_xpath('//input'):
            input_name = input_element.get_attribute('name')
            if not input_name:
                # Not usefull for our form
                continue
            if input_name in self.controls:
                self.controls[input_name]._extend(input_element)
            else:
                input_type = input_element.get_attribute('type') or 'submit'
                factory = FORM_ELEMENT_IMPLEMENTATION.get(input_type, Control)
                self.controls[input_name] = factory(self, input_element)

    def get_control(self, name):
        if name not in self.controls:
            raise AssertionError(u'No control %s' % name)
        return self.controls.get(name)

    def submit(self, name=None, value=None):
        self.__element.submit()
