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
        return self.browser.open(urllib.unquote(self.html.attrib['href']))


class Control(HTMLElement):

    def __init__(self, form, html):
        self.form = form
        self.html = html

    def __getattr__(self, name):
        html = self.html
        multiple = False
        if isinstance(html, list):
            html = html[0]
            multiple = True
        if name in ('name', 'value'):
            return getattr(html, name)
        if html.tag == 'select':
            if name in ('value_options', 'multiple'):
                return getattr(html, name)
            if name in ('checkable', 'checked'):
                return False
            if name == 'type':
                return 'select'
        if html.tag == 'input':
            if name in ('type', 'checkable', 'checked'):
                return getattr(html, name)
            if name == 'value_options':
                return []
            if name == 'multiple':
                return multiple

    def __setattr__(self, name, value):
        if name == 'value':
            if not self.multiple:
                if not isinstance(value, basestring):
                    value = str(value)
            elif ((not isinstance(value, list)) or
                  isinstance(value, basestring)):
                value = [value]
            self.html.value = value
        return super(Control, self).__setattr__(name, value)


class ButtonControl(Control):

    def submit(self):
        return self.form.submit(self.html.name, self.html.value)

    click = submit


class Form(HTMLElement):

    def get_control(self, name):
        node = self.html.inputs[name]
        if (not isinstance(node, list) and
            node.tag == 'input' and
            node.get('type', 'submit') == 'submit'):
            return ButtonControl(self, node)
        return Control(self, node)

    def submit(self, name=None, value=None):
        form = dict()
        if name is not None:
            if value is None:
                value = self.html.inputs[name].value
            form[name] = value
        for name, value in self.html.form_values():
            if value:
                form[name] = value
        return self.browser.open(
            urllib.unquote(self.html.action),
            method=self.html.method,
            form=form)
