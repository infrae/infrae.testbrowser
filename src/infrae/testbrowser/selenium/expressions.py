# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from collections import defaultdict

from infrae.testbrowser.utils import node_to_node
from infrae.testbrowser.utils import none_filter
from infrae.testbrowser.utils import resolve_location
from infrae.testbrowser.utils import compound_filter_factory
from infrae.testbrowser.utils import ExpressionResult


def node_to_text(node):
    return node.text

def tag_filter(name):
    def element_filter(element):
        return element.tag == name
    return element_filter

def visible_filter(element):
    return element.is_displayed


class Clickable(object):

    def __init__(self, element):
        self.element = element
        self.text = element.text
        self.__str = self.text
        if not self.__str:
            self.__str = '<%s />' % element.tag

    def click(self):
        return self.element.click()

    def __str__(self):
        if isinstance(self.__str, unicode):
            return self.__str.encode('utf-8', 'replace')
        return str(self.__str)

    def __unicode__(self):
        return unicode(self.__str)

    def __repr__(self):
        return repr(str(self))


class Link(Clickable):

    @property
    def url(self):
        return resolve_location(self.element.get_attribute('href'))


def ClickablesFactory(factory):

    class Clickables(ExpressionResult):

        def __init__(self, items):
            super(Clickables, self).__init__(
                map(lambda item: (str(item).lower(), unicode(item), item),
                    map(lambda item: factory(item), items)))

    return Clickables


EXPRESSION_TYPE = {
    'text': (
        node_to_text,
        none_filter,
        lambda elements: list(elements)),
    'link': (
        node_to_node,
        compound_filter_factory(visible_filter, tag_filter('a')),
        ClickablesFactory(Link)),
    'clickable': (
        node_to_node,
        visible_filter,
        ClickablesFactory(Clickable))
    }


_marker = object()

class Expressions(object):

    def __init__(self, runner):
        self.__runner = runner
        self.__expressions = defaultdict(lambda: tuple((None, None)))
        self.__compound = {}

    def add(self, name, xpath=None, type='text', css=None, compound=None):
        if compound is None:
            assert type in EXPRESSION_TYPE, u'Unknown expression type %s' % type
            finder = None
            if xpath is not None:
                finder = lambda d: d.get_elements(xpath=xpath)
            elif css is not None:
                finder = lambda d: d.get_elements(css=css)
            assert finder is not None, \
                u'You need to provide an XPath or CSS expression'
            self.__expressions[name] = (finder, type)
        else:
            self.__compound[name] = compound

    def __getattr__(self, name):

        def get_expression(name):
            finder, type = self.__expressions[name]
            if finder is not None:
                node_converter, node_filter, factory = EXPRESSION_TYPE[type]
                return factory(filter(node_filter,
                                      map(node_converter,
                                          self.__runner(finder))))
            return _marker

        expression_values = get_expression(name)
        if expression_values is not _marker:
            return expression_values

        if name in self.__compound:

            class Object(object):

                def __init__(self, definition):
                    self.__dict__.update(definition)

            initial = True
            definitions = []
            for key, expression_name in self.__compound[name].items():
                expression_values = get_expression(expression_name)
                if expression_values is _marker:
                    continue
                for position, value in enumerate(expression_values):
                    if initial:
                        definitions.append({key: value})
                    else:
                        definitions[position][key] = value
                initial = False
            return definitions

        raise AttributeError(name)

