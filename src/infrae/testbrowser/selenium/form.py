# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import collections
import operator

from infrae.testbrowser.interfaces import IForm
from infrae.testbrowser.interfaces import IFormControl
from infrae.testbrowser.interfaces import IClickableFormControl
from infrae.testbrowser.interfaces import ISubmitableFormControl
from infrae.testbrowser.form import ControlExpressions
from infrae.testbrowser.utils import parse_charset, resolve_location
from infrae.testbrowser.selenium.errors import SeleniumElementNotFound

from zope.interface import implements


class Control(object):
    implements(IFormControl)

    def __init__(self, form, element_type, element_name, element):
        self.form = form
        self._element = element
        self.__name = element_name
        assert self.__name is not None
        self.__multiple = False
        self.__identifier = None
        self.__label = None
        self.__type = element_type
        if element_type == 'select':
            self.__multiple = element.get_attribute('multiple') not in (None, 'false')
            self.__options = collections.OrderedDict()
            for option in element.get_elements(xpath='descendant::option'):
                value = option.get_attribute('value')
                if value is None:
                    value = option.text
                self.__options[value] = option
        else:
            self.__options = collections.OrderedDict()
            if self.__type in ['checkbox', 'radio']:
                self.__options[element.value] = element

    @apply
    def label():
        def getter(self):
            if self.__label:
                return self.__label
            if not self.__multiple:
                if self.__identifier is None:
                    self.__identifier = self._element.get_attribute('id')
                if self.__identifier:
                    try:
                        label = self.form._element.get_element(
                            xpath="//label[@for='%s']" % self.__identifier)
                    except SeleniumElementNotFound:
                        pass
                    else:
                        self.__label = label.text
                        return self.__label
            return self.__name
        return property(getter)

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
            if self.__type in ['select', 'radio', 'checkbox']:
                values = map(operator.itemgetter(0),
                               filter(lambda (name, option): option.is_selected,
                                      self.__options.items()))
                if self.__multiple:
                    return values
                assert len(values) < 2
                return values and values[0] or ''
            if self.__multiple:
                return map(operator.attrgetter('value'), self._element)
            return self._element.value
        def setter(self, value):
            if self.__type in ['select', 'radio', 'checkbox']:
                if self.__multiple:
                    if isinstance(value, basestring):
                        value = [value]
                    value = set(value)
                    valid_value = set(self.__options.keys())
                    assert not value.difference(valid_value), \
                        u'Invalid value selected'
                    selected = set(filter(
                            lambda option: option.is_selected,
                            self.__options.values()))
                    wanted = set(map(lambda v: self.__options[v], value))
                    for option in selected.difference(wanted):
                        option.click()
                    for option in wanted.difference(selected):
                        option.click()
                else:
                    assert value in self.__options.keys(), \
                        u'Invalid value %s selected' % value
                    self.__options[value].click()
            else:
                if self.__multiple:
                    if not isinstance(value, list) or isinstance(value, tuple):
                        value = [value]
                    assert len(value) == len(self._element), \
                        u"Not enough values"
                    for element, element_value in zip(self._element, value):
                        element.clear()
                        element.send_keys(element_value)
                else:
                    assert isinstance(value, basestring), \
                        u'Multiple values not accepted for this field'
                    self._element.clear()
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
            if len(self.__options) > 1 or self.__type == 'select':
                return self.__options.keys()
            return []
        return property(getter)

    @apply
    def checkable():
        def getter(self):
            return self.__type in ['checkbox', 'radio'] and len(self.__options) < 2
        return property(getter)

    @apply
    def checked():
        def getter(self):
            if self.checkable:
                if not self.__multiple:
                    return self._element.is_selected
            return False
        def setter(self, value):
            assert self.checkable, u"Not checkable"
            if not self.__multiple:
                status = self._element.is_selected
                if status != value:
                    self._element.click()
        return property(getter, setter)

    def _extend(self, element_type, element):
        if self.__type == 'submit' and element_type == 'submit':
            # We authorize to have more than one submit with the same name
            return

        if self.__type not in ['checkbox', 'radio']:
            # Support for multiple fields (hidden, other)
            assert element_type not in ['file', 'submit', 'select', 'checkbox', 'radio'], \
                u"multiple input or mixing input %s and %s is not supported" % (
                self.__type, element_type)
            if self.__type != element_type:
                self.__type = 'mixed'
            if not self.__multiple:
                self.__multiple = True
                self._element = [self._element]
            self._element.append(element)
            return
        assert self.__type ==  element_type, \
            u'Control extended with a different control type'
        if self.__type == 'checkbox':
            self.__multiple = True
        self.__options[element.value] = element


class ButtonControl(Control):
    implements(IClickableFormControl)

    def click(self):
        return self._element.click()


class SubmitControl(ButtonControl):
    implements(ISubmitableFormControl)

    submit = ButtonControl.click


FORM_ELEMENT_IMPLEMENTATION = {
    'submit': SubmitControl,
    'button': ButtonControl,
    'image': SubmitControl}


class Form(object):
    implements(IForm)

    def __init__(self, element):
        self.name = element.get_attribute('name') or None
        self.action = None
        action = element.get_attribute('action')
        if action:
            self.action = resolve_location(action)
        self.method = (element.get_attribute('method') or
                       'POST').upper()
        self.enctype = (element.get_attribute('enctype') or
                        'application/x-www-form-urlencoded')
        self.accept_charset = parse_charset(
            element.get_attribute('accept-charset') or 'utf-8')
        self.controls = {}
        self.inspect = ControlExpressions(self)
        self.inspect.add('actions', ({'type': 'submit'}, 'value'))
        self.inspect.add('fields', ({}, 'label'))
        self._element = element
        self.__populate_controls()

    def __populate_controls(self):
        get_elements = self._element.get_elements

        # Input tags
        for input_node in get_elements(
            xpath='descendant::input|descendant::select|descendant::textarea|' \
                'descendant::button'):
            input_name = input_node.get_attribute('name')
            if not input_name:
                # Not usefull for our form
                continue
            input_tag = input_node.tag
            if input_tag in ['input', 'button']:
                input_type = input_node.get_attribute('type') or 'submit'
            else:
                input_type = input_tag
            if input_name in self.controls:
                self.controls[input_name]._extend(input_type, input_node)
            else:
                factory = FORM_ELEMENT_IMPLEMENTATION.get(input_type, Control)
                self.controls[input_name] = factory(
                    self, input_type, input_name, input_node)

    def get_control(self, name):
        if name not in self.controls:
            raise AssertionError(u'No control %s' % name)
        return self.controls.get(name)

    def submit(self, name=None, value=None):
        self._element.submit()

    def __repr__(self):
        return '<form action="%s" />' % (self.action)
