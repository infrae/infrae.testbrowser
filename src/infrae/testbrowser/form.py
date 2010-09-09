# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import urllib
import lxml.etree

class HTMLElement(object):

    def __init__(self, html, browser):
        self.browser = browser
        self.html = html

    def __str__(self):
        return lxml.etree.tostring(self.html, pretty_print=True)


class Link(HTMLElement):

    def click(self):
        url = urllib.unquote(self.html.attrib['href'])
        return self.browser.open(url)


class Control(object):

    def __init__(self, form, html):
        self.form = form
        self.html = html
        self.__name = html.name
        self.__multiple = False
        if html.tag == 'select':
            self.__type = 'select'
            self.__multiple = html.get('multiple', False) is not False
            self.__value = [] if self.__multiple else ''
            self.__options = []
            for option in html.xpath('descendant::option'):
                value = option.get('value', None)
                if value is None:
                    value = option.text_content()
                self.__options.append(value)
                if option.get('selected', False) is not False:
                    if not self.__multiple:
                        self.__value = value
                    else:
                        self.__value.append(value)
        else:
            if html.tag == 'textarea':
                self.__type = 'textarea'
                self.__value = html.text_content()
            else:
                self.__type = html.get('type', 'submit')
                self.__value = html.get('value', '')
            self.__options = []
        self.__checked = False
        if self.checkable:
            self.__checked = html.get('checked', False) is not False

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
            if self.checkable and not self.checked:
                return ''
            return self.__value
        def setter(self, value):
            if self.checkable:
                self.checked = value
                return
            if self.multiple:
                if not isinstance(value, list) or isinstance(value, tuple):
                    value = [value]
                for subvalue in value:
                    if subvalue not in self.__options:
                        raise AssertionError(u"Invalid choice %s" % subvalue)
            else:
                assert (isinstance(value, basestring) or
                        isinstance(value, bool)), \
                        u'Invalid value type set for control %r' % value
                if self.__options:
                    if value not in self.__options:
                        raise AssertionError(u"Invalid choice %s" % value)
            self.__value = value
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
        assert self.__type == html.get('type', 'submit'), \
            u'%s: control extended with a control type' % html.name
        if self.__type == 'submit':
            # We authorize to have more than one submit with the same name
            return
        assert self.__type in ['checkbox', 'radio'], \
            u'%s: only checkbox and radio can be multiple inputs' % html.name
        assert self.name  == html.name, \
            u'%s: control extended with a different input' % html.name
        if not self.options:
            # Firt time the control is extended
            self.html = [self.html]
            value = self.__value
            selected = self.__checked
            if self.__type == 'checkbox':
                self.__multiple = True
            self.__value = [] if self.__multiple else ''
            self.__options = [value]
            self.__checked = False
            if selected:
                if self.__multiple:
                    self.__value.append(value)
                else:
                    self.__value = value
        value = html.get('value', '')
        if html.get('checked', False) is not False:
            if self.__multiple:
                self.__value.append(value)
            else:
                assert self.__value == '', \
                    u'Not multiple control with multiple value'
                self.__value = value
        self.__options.append(value)
        self.html.append(html)

    def _submit_data(self):
        if self.checkable:
            if not self.checked:
                return []
            if not self.value:
                return [(self.name, 'checked')]
        elif self.multiple:
            return [(self.name, value) for value in self.value]
        return [(self.name, self.value)]


class ButtonControl(Control):

    def __init__(self, form, html):
        super(ButtonControl, self).__init__(form, html)
        self.__selected = False

    def submit(self):
        self.__selected = True
        return self.form.submit()

    click = submit

    def _submit_data(self):
        if not self.__selected:
            return []
        return [(self.name, self.value)]


FORM_ELEMENT_IMPLEMENTATION = {
    'submit': ButtonControl}


class Form(HTMLElement):

    def __init__(self, html, browser):
        super(Form, self).__init__(html, browser)
        self.name = html.get('name', '')
        self.action = urllib.unquote(html.action)
        self.method = html.get('method', 'POST').upper()
        self.controls = {}
        self.__control_names = []
        self.__populate_controls()

    def __populate_controls(self):
        __traceback_info__ = 'Error while parsing form: \n\n%s\n\n' % str(self)
        # Input tags
        for input_node in self.html.xpath('descendant::input'):
            input_name = input_node.get('name', None)
            if not input_name:
                # No name, not a concern to this form
                continue
            if input_name in self.controls:
                self.controls[input_name]._extend(input_node)
            else:
                input_type = input_node.get('type', 'submit')
                factory = FORM_ELEMENT_IMPLEMENTATION.get(input_type, Control)
                self.controls[input_name] = factory(self, input_node)
                self.__control_names.append(input_name)

        # Select tags
        for select_node in self.html.xpath('descendant::select'):
            select_name = select_node.get('name', None)
            if not select_name:
                # No name, not a concern
                continue
            assert select_name not in self.controls
            self.controls[select_name] = Control(self, select_node)
            self.__control_names.append(select_name)

        # Textarea tags
        for text_node in self.html.xpath('descendant::textarea'):
            text_name = text_node.get('name', None)
            if not text_name:
                # No name, not a concern
                continue
            assert text_name not in self.controls
            self.controls[text_name] = Control(self, text_node)
            self.__control_names.append(text_name)

        # Button tags
        for button_node in self.html.xpath('descendant::button'):
            button_name = button_node.get('name', None)
            if not button_name:
                # No name, not a concern
                continue
            assert button_name not in self.controls, \
                u'Duplicate input %s in form %s' % (button_name, self.name)
            self.controls[button_name] = ButtonControl(self, button_node)
            self.__control_names.append(button_name)

    def get_control(self, name):
        if name not in self.controls:
            raise AssertionError(u'No control %s' % name)
        return self.controls.get(name)

    def submit(self, name=None, value=None):
        form = []
        if name is not None:
            if value is None:
                value = self.controls[name].value
            form.append((name, value))
        for name in self.__control_names:
            control = self.controls[name]
            form.extend(control._submit_data())
        return self.browser.open(
            self.action, method=self.method, form=form)
