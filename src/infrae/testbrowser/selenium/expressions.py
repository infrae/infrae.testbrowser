# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from collections import namedtuple

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

    def __eq__(self, other):
        return self.__str == other

    def __ne__(self, other):
        return self.__str != other

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


ExpressionType = namedtuple(
    'ExpressionType',
    ('converter', 'filter', 'nodes', 'node'))

EXPRESSION_TYPE = {
    'text': ExpressionType(
        node_to_text,
        none_filter,
        lambda elements: list(elements),
        lambda element: element),
    'link': ExpressionType(
        node_to_node,
        compound_filter_factory(visible_filter, tag_filter('a')),
        ClickablesFactory(Link),
        Link),
    'clickable': ExpressionType(
        node_to_node,
        visible_filter,
        ClickablesFactory(Clickable),
        Clickable)
    }


_marker = object()



class ExpressionList(object):

    def __init__(self, runner):
        self._runner = runner
        self._expressions = {}

    def _execute(self, name, default=_marker):
        if name in self._expressions:
            finder, type, unique = self._expressions[name]
            if finder is not None:
                expression = EXPRESSION_TYPE[type]
                nodes = filter(expression.filter,
                               map(expression.converter,
                                   self._runner(finder)))
                if unique:
                    if len(nodes) > 1:
                        raise AssertionError(
                            u'Multiple elements found for %s where only '
                            u'one was expected.' % name)
                    if not len(nodes):
                        return None
                    return expression.node(nodes[0])
                return expression.nodes(nodes)
        return default

    def __getattr__(self, name):
        value = self._execute(name, default=_marker)
        if value is not _marker:
            return value
        raise AttributeError(name)


class NestedResult(ExpressionList):

    def __init__(self, runner, node, definition):
        super(NestedResult, self).__init__(runner)
        self._keys = []
        for name, options in definition.items():
            if name is None and isinstance(options, (list, tuple)):
                self._keys = options
                continue
            finder = None
            if 'xpath' in options:
                finder = (lambda xpath: lambda d: node.get_elements(
                        xpath=xpath))(options['xpath'])
            elif 'css' in options:
                finder = (lambda css: lambda d: node.get_elements(
                        css=css))(options['css'])
            self._expressions[name] = (
                finder,
                options.get('type', 'text'),
                options.get('unique', False))

    def __repr__(self):
        values = []
        for key in self._keys:
            values.append('%r: %r' % (key, self._execute(key, default=None)))
        return '{' + ', '.join(values) + '}'

    def __eq__(self, other):
        if isinstance(other, dict):
            for key, expected in other.items():
                value = self._execute(key, default=_marker)
                if value != expected:
                    return False
            return True
        return False


class Expressions(ExpressionList):

    def __init__(self, runner):
        super(Expressions, self).__init__(runner)
        self._nested = {}

    def add(self, name, xpath=None, type='text', css=None, nested=None, unique=False):
        finder = None
        if xpath is not None:
            finder = lambda d: d.get_elements(xpath=xpath)
        elif css is not None:
            finder = lambda d: d.get_elements(css=css)
        if finder is None:
            raise AssertionError(
                u'You need to provide an XPath or CSS expression')
        if nested is None:
            if type not in EXPRESSION_TYPE:
                raise AssertionError(u'Unknown expression type %s' % type)
            self._expressions[name] = (finder, type, unique)
        else:
            self._nested[name] = (finder, nested)

    def __getattr__(self, name):
        if name in self._nested:
            finder, nested = self._nested[name]
            values = []
            for node in self._runner(finder):
                values.append(NestedResult(self._runner, node, nested))
            return values

        values = self._execute(name, default=_marker)
        if values is not _marker:
            return values
        raise AttributeError(name)

