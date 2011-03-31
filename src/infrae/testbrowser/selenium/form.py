# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$


class Control(object):

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
            self._element.send_keys(value)
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

    def __init__(self, element):
        self.name = element.get_attribute('name') or None
        self.method = (element.get_attribute('method') or 'POST').upper()
        self.enctype = element.get_attribute('enctype') or 'application/x-www-form-urlencoded'
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

    def submit(self):
        self.__element.submit()
