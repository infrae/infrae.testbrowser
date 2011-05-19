# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import collections
import operator

from infrae.testbrowser.interfaces import IFormControl, IForm
from infrae.testbrowser.expressions import ControlExpressions
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
        tag_name = element.tag
        if tag_name == 'select':
            self.__type = 'select'
            self.__multiple = element.get_attribute('multiple') != 'false'
            self.__options = collections.OrderedDict()
            for option in element.get_elements(xpath='descendant::option'):
                value = option.get_attribute('value')
                if value is None:
                    value = option.text
                self.__options[value] = option
        else:
            if tag_name == 'textarea':
                self.__type = 'textarea'
            else:
                self.__type = element.get_attribute('type') or 'submit'
            self.__options = collections.OrderedDict()
            if self.__type in ['checkbox', 'radio']:
                self.__options[element.value] = element

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
                        option.toggle()
                    for option in wanted.difference(selected):
                        option.select()
                else:
                    assert value in self.__options.keys(), \
                        u'Invalid value %s selected' % value
                    self.__options[value].select()
            else:
                if not isinstance(value, basestring):
                    raise AssertionError(
                        u'Multiple values not accepted for this field')
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
                    self._element.toggle()
        return property(getter, setter)

    def _extend(self, element):
        element_type = element.get_attribute('type') or 'submit'
        assert self.__type ==  element_type, \
            u'Control extended with a different control type'
        if self.__type == 'submit':
            # We authorize to have more than one submit with the same name
            return
        assert self.__type in ['checkbox', 'radio'], \
            u'Only checkbox and radio can be multiple inputs'
        if self.__type == 'checkbox':
            self.__multiple = True
        self.__options[element.value] = element


class ButtonControl(Control):

    def click(self):
        self._element.click()

    submit = click


FORM_ELEMENT_IMPLEMENTATION = {
    'submit': ButtonControl,
    'button': ButtonControl,
    'image': ButtonControl}


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
        self.__element = element
        self.__populate_controls()

    def __populate_controls(self):
        get_elements = self.__element.get_elements

        # Input tags
        for input_element in get_elements(xpath='descendant::input'):
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

        # Select tags
        for select_node in get_elements(xpath='descendant::select'):
            select_name = select_node.get_attribute('name')
            if not select_name:
                # No name, not a concern
                continue
            assert select_name not in self.controls
            self.controls[select_name] = Control(self, select_node)

        # Textarea tags
        for text_node in get_elements(xpath='descendant::textarea'):
            text_name = text_node.get_attribute('name')
            if not text_name:
                # No name, not a concern
                continue
            assert text_name not in self.controls
            self.controls[text_name] = Control(self, text_node)

        # Button tags
        for button_node in get_elements(xpath='descendant::button'):
            button_name = button_node.get_attribute('name')
            if not button_name:
                # No name, not a concern
                continue
            assert button_name not in self.controls
            button_type = button_node.get_attribute('type') or 'button'
            factory = FORM_ELEMENT_IMPLEMENTATION.get(button_type, ButtonControl)
            self.controls[button_name] = factory(self, button_node)


    def get_control(self, name):
        if name not in self.controls:
            raise AssertionError(u'No control %s' % name)
        return self.controls.get(name)

    def submit(self, name=None, value=None):
        self.__element.submit()
