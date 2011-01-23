# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import operator
import functools
import codecs
import lxml.etree

from infrae.testbrowser.interfaces import IFormControl, IForm
from infrae.testbrowser.expressions import ExpressionResult
from infrae.testbrowser.utils import File, resolve_url

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

    def __init__(self, form, html):
        super(ButtonControl, self).__init__(form, html)
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
    'submit': ButtonControl,
    'image': ButtonControl}


def parse_charset(charsets):
    """Parse form accept charset and return a list of charset that can
    be used in Python.
    """
    seen = set()

    def resolve_charset(charset):
        if not charset:
            return None
        try:
            name = codecs.lookup(charset).name
            if name in seen:
                return None
            seen.add(name)
            return name
        except LookupError:
            return None
        return None

    return filter(lambda c: c != None,
                  map(resolve_charset,
                      reduce(operator.add,
                             map(lambda c: c.split(), charsets.split(',')))))


def charset_encoder(charset, value):
    """Encoder a value in the given charset.
    """
    if isinstance(value, unicode):
        return value.encode(charset, 'ignore')
    return str(value)


class Controls(ExpressionResult):

    def __init__(self, controls, name):

        def prepare(control):
            key = getattr(control, name, 'missing')
            return (key.lower(), key, control)

        super(Controls, self).__init__(map(prepare, controls))


class ControlExpressions(object):

    def __init__(self, form):
        self.__form = form
        self.__expressions = {}

    def add(self, name, expression):
        self.__expressions[name] = expression

    def __getattr__(self, name):
        if name in self.__expressions:
            expression = self.__expressions[name]

            def matcher(control):
                for key, value in expression[0].items():
                    if getattr(control, key, None) != value:
                        return False
                return True

            return Controls(
                filter(matcher, self.__form.controls.values()),
                expression[1])
        raise AttributeError(name)


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
            form=form, form_enctype=self.enctype)

    def __str__(self):
        return lxml.etree.tostring(self.html, pretty_print=True)
