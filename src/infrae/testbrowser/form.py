# -*- coding: utf-8 -*-
# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import functools
import lxml.etree

from infrae.testbrowser.interfaces import IFormControl, IForm
from infrae.testbrowser.interfaces import IClickableFormControl
from infrae.testbrowser.interfaces import ISubmitableFormControl
from infrae.testbrowser.expressions import ControlExpressions
from infrae.testbrowser.utils import File, resolve_url
from infrae.testbrowser.utils import parse_charset, charset_encoder

from zope.interface import implements


class Control(object):
    implements(IFormControl)

    def __init__(self, form, html):
        self.form = form
        self.html = html
        self.__name = html.get('name')
        assert self.__name is not None
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
            if not self.__value and not self.__multiple and self.__options:
                # In case of non multiple select, the first value
                # should be selected by default
                self.__value = self.__options[0]
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
                if self.__type in ['radio', 'checkbox', 'select']:
                    for subvalue in value:
                        assert subvalue in self.__options, \
                            u"Invalid choice %s" % subvalue
                else:
                    assert len(value) == len(self.__value), u"Not enough values"
            else:
                if isinstance(value, int):
                    value = str(value)
                assert (isinstance(value, basestring) or
                        isinstance(value, bool)), \
                        u'Invalid value type %s set for control %r' % (
                            type(value).__name__, value)
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
        if html.tag in ['select', 'textarea']:
            html_type = html.tag
        else:
            html_type = html.get('type', 'submit')
        if self.__type == 'submit' and html_type == 'submit':
            # We authorize to have more than one submit with the same name
            return
        if self.__type not in ['checkbox', 'radio']:
            # Support for multiple fields (hidden, other)
            assert html_type not in ['file', 'submit', 'select', 'checkbox', 'radio'], \
                u"%s: multiple input or mixing input %s and %s is not supported" % (
                html.name, self.__type, html_type)
            if self.__type != html_type:
                self.__type = 'mixed'
            if not self.__multiple:
                self.__multiple = True
                self.__value = [self.__value]
            if html_type == 'textarea':
                self.__value.append(html.text_content())
            else:
                self.__value.append(html.get('value', ''))
            return
        # Checkbox, radio
        assert self.__type == html_type, \
            u'%s: control extended with a different control type (%s with %s)' % (
            html.name, self.__type, html_type)
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

    def _submit_data(self, encoder):
        if self.checkable:
            if not self.checked:
                return []
            if not self.value:
                return [(self.name, 'checked')]
        elif self.multiple:
            return [(self.name, encoder(value)) for value in self.value]
        if self.type in ['file']:
            return [(self.name, File(self.value))]
        return [(self.name, encoder(self.value))]

    def __str__(self):
        if isinstance(self.html, list):
            html = self.html
        else:
            html = [self.html]
        return '\n'.join(
            map(lambda h:lxml.etree.tostring(h, pretty_print=True), html))


class ButtonControl(Control):
    implements(IClickableFormControl)

    def click(self):
        pass


class SubmitControl(Control):
    implements(ISubmitableFormControl)

    def __init__(self, form, html):
        super(SubmitControl, self).__init__(form, html)
        self.__selected = False

    def submit(self):
        self.__selected = True
        return self.form.submit()

    click = submit

    def _submit_data(self, encoder):
        if not self.__selected:
            return []
        return [(self.name, encoder(self.value))]


FORM_ELEMENT_IMPLEMENTATION = {
    'button': ButtonControl,
    'submit': SubmitControl,
    'image': SubmitControl}


class Form(object):
    implements(IForm)

    def __init__(self, html, browser):
        self.html = html
        self.name = html.get('name', None)
        base_action = html.get('action')
        if base_action:
            self.action = resolve_url(base_action, browser)
        else:
            self.action = browser.location
        self.method = html.get('method', 'POST').upper()
        self.enctype = html.get('enctype', 'application/x-www-form-urlencoded')
        self.accept_charset = parse_charset(html.get('accept-charset', 'utf-8'))
        self.controls = {}
        self.inspect = ControlExpressions(self)
        self.inspect.add('actions', ({'type': 'submit'}, 'value'))
        self.__browser = browser
        self.__control_names = []
        self.__populate_controls()

    def __populate_controls(self):
        __traceback_info__ = 'Error while parsing form: \n\n%s\n\n' % str(self)
        # Input tags
        # XXX: Test that the order is conserved form the source page.
        # XXX: Use an ordered dict ?
        for input_node in self.html.xpath(
            'descendant::input|select|textarea|button'):

            input_name = input_node.get('name', None)
            if not input_name:
                # No name, not a concern to this form
                # XXX: Default to the good default
                continue
            if input_name in self.controls:
                self.controls[input_name]._extend(input_node)
            else:
                if input_node.tag in ['input', 'button']:
                    input_type = input_node.get('type', 'submit')
                else:
                    input_type = input_node.tag
                factory = FORM_ELEMENT_IMPLEMENTATION.get(input_type, Control)
                self.controls[input_name] = factory(self, input_node)
                self.__control_names.append(input_name)

    def get_control(self, name):
        if name not in self.controls:
            raise AssertionError(u'No control %s' % name)
        return self.controls.get(name)

    def submit(self, name=None, value=None):
        form = []
        encoder = functools.partial(charset_encoder, self.accept_charset[0])
        if name is not None:
            if value is None:
                value = self.controls[name].value
            form.append((name, value))
        for name in self.__control_names:
            control = self.controls[name]
            form.extend(control._submit_data(encoder))
        return self.__browser.open(
            self.action, method=self.method,
            form=form, form_charset=self.accept_charset[0], form_enctype=self.enctype)

    def __str__(self):
        return lxml.etree.tostring(self.html, pretty_print=True)
