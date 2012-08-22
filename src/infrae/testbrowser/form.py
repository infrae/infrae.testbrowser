# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import functools
import lxml.etree

from infrae.testbrowser.interfaces import IFormControl, IForm
from infrae.testbrowser.interfaces import IClickableFormControl
from infrae.testbrowser.interfaces import ISubmitableFormControl
from infrae.testbrowser.utils import File, ResultSet, resolve_url
from infrae.testbrowser.utils import parse_charset, charset_encoder

from zope.interface import implements


class ControlResultSet(ResultSet):

    def __init__(self, controls, name):

        def prepare(control):
            key = getattr(control, name, 'missing')
            return (key.lower(), key, control)

        super(ControlResultSet, self).__init__(map(prepare, controls))


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

            return ControlResultSet(
                filter(matcher, self.__form.controls.values()),
                expression[1])
        raise AttributeError(name)


class Control(object):
    implements(IFormControl)

    def __init__(self, form, element_type, element, register_submit):
        self.form = form
        self.html = element
        self.__name = element.get('name')
        assert self.__name is not None
        self.__multiple = False
        self.__type = element_type
        submit = None
        if element_type == 'select':
            self.__multiple = element.get('multiple', False) is not False
            self.__value = [] if self.__multiple else ''
            self.__options = []
            for option in element.xpath('descendant::option'):
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

            def submit(encoder):
                if self.__multiple:
                    return [(self.name, encoder(value)) for value in self.value]
                return [(self.name, encoder(self.value))]

        else:
            if element_type == 'textarea':
                self.__value = element.text_content()
            else:
                self.__value = element.get('value', '')
            self.__options = []

            if element_type == 'file':
                submit = lambda encoder: [(self.name, File(self.value))]
            else:

                def submit(encoder):
                    if self.__multiple:
                        if len(self.__value):
                            return [(self.name, encoder(self.__value[0]))]
                        return []
                    return [(self.name, encoder(self.__value))]

        self.__checked = False
        if element_type in ['radio', 'checkbox']:
            self.__checked = element.get('checked', False) is not False

            def submit(encoder):
                if self.__multiple:
                    return [(self.name, encoder(value)) for value in self.value]
                if self.checkable and not self.__checked:
                    return []
                if not self.__value:
                    return [(self.name, 'checked')]
                return [(self.name, encoder(self.__value))]

        if submit is not None:
            register_submit(submit)

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

    def _extend(self, element_type, element, register_submit):
        if self.__type == 'submit' and element_type == 'submit':
            # We authorize to have more than one submit with the same name
            return
        if self.__type not in ['checkbox', 'radio']:
            # Support for multiple fields (hidden, other)
            assert element_type not in ['file', 'submit', 'select'], \
                u"%s: multiple input or mixing input %s and %s is not supported" % (
                element.name, self.__type, element_type)
            if self.__type != element_type:
                self.__type = 'mixed'
            if not self.__multiple:
                self.__multiple = True
                self.__value = [self.__value]
            value_index = len(self.__value)
            if element_type == 'textarea':
                self.__value.append(element.text_content())
            else:
                self.__value.append(element.get('value', ''))

            def submit(encoder):
                if len(self.__value) > value_index:
                    return [(self.name, encoder(self.__value[value_index]))]
                return []

            register_submit(submit)
            return
        # Checkbox, radio
        assert self.__type == element_type, \
            u'%s: control extended with a different control type (%s with %s)' % (
            element.name, self.__type, element_type)
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
        value = element.get('value', '')
        if element.get('checked', False) is not False:
            if self.__multiple:
                self.__value.append(value)
            else:
                assert self.__value == '', \
                    u'Not multiple control with multiple value'
                self.__value = value
        self.__options.append(value)
        self.html.append(element)

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

    def __init__(self, form, element_type, element, register_submit):
        super(SubmitControl, self).__init__(
            form, element_type, element, lambda r: None)
        self.__selected = False

        def submit(encoder):
            if self.__selected:
                return [(self.name, encoder(self.value))]
            return []

        register_submit(submit)

    def submit(self):
        self.__selected = True
        return self.form.submit()

    click = submit


FORM_ELEMENT_IMPLEMENTATION = {
    'button': ButtonControl,
    'submit': SubmitControl,
    'image': SubmitControl
}

FORM_ELEMENT_DEFAULT = {
    'button': 'submit',
    'input': 'text'
}


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
        self.__control_submits = []
        self.__populate_controls()

    def __populate_controls(self):
        __traceback_info__ = 'Error while parsing form: \n\n%s\n\n' % str(self)
        # Input tags
        # XXX: Test that the order is conserved form the source page.
        # XXX: Use an ordered dict ?
        for input_node in self.html.xpath(
            'descendant::input|descendant::select|descendant::textarea|' \
                'descendant::button'):

            input_name = input_node.get('name', None)
            if not input_name:
                # No name, not a concern to this form
                # XXX: Should default to the good default
                continue
            if input_node.tag in ['input', 'button']:
                input_type = input_node.get(
                    'type', FORM_ELEMENT_DEFAULT[input_node.tag])
            else:
                input_type = input_node.tag
            if input_name in self.controls:
                self.controls[input_name]._extend(
                    input_type, input_node, self.__control_submits.append)
            else:
                factory = FORM_ELEMENT_IMPLEMENTATION.get(input_type, Control)
                self.controls[input_name] = factory(
                    self, input_type, input_node, self.__control_submits.append)
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
        for submitter in self.__control_submits:
            form.extend(submitter(encoder))
        return self.__browser.open(
            self.action,
            method=self.method,
            form=form,
            form_charset=self.accept_charset[0],
            form_enctype=self.enctype)

    def __str__(self):
        return lxml.etree.tostring(self.html, pretty_print=True)

    def __repr__(self):
        return '<form action="%s" />' % (self.action)
