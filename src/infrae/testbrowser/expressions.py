# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import lxml
from collections import defaultdict
from collections import namedtuple

from infrae.testbrowser.utils import ExpressionResult
from infrae.testbrowser.utils import node_to_node, none_filter
from infrae.testbrowser.utils import resolve_url

def node_to_normalized_text(node):
    return ' '.join(
        filter(
            lambda s: s,
            map(
                lambda s: s.strip(),
                node_to_text(node).split())))

def node_to_text(node):
    return node.text_content().strip()

def tag_filter(name):
    def node_filter(node):
        return node.tag == name
    return node_filter


class Link(object):

    def __init__(self, html, browser):
        self.html = html
        self.browser = browser
        self.text = html.text_content().strip()

    @property
    def url(self):
        return resolve_url(self.html.attrib['href'], self.browser)

    def click(self):
        return self.browser.open(self.url)

    def __str__(self):
        if isinstance(self.text, unicode):
            return self.text.encode('utf-8', 'replace')
        return str(self.text)

    def __eq__(self, other):
        return self.text == other

    def __ne__(self, other):
        return self.text != other

    def __unicode__(self):
        return unicode(self.text)

    def __repr__(self):
        return repr(str(self))


class Links(ExpressionResult):

    def __init__(self, links, browser):
        super(Links, self).__init__(
            map(lambda link: (str(link).lower(), unicode(link), link),
                map(lambda link: Link(link, browser), links)))



ExpressionType = namedtuple(
    'ExpressionType',
    ('converter', 'filter', 'nodes', 'node'))

EXPRESSION_TYPE = {
    'node': ExpressionType(
        node_to_node,
        none_filter,
        lambda nodes, browser: list(nodes),
        lambda node, browser: node),
    'text': ExpressionType(
        node_to_text,
        none_filter,
        lambda nodes, browser: list(nodes),
        lambda node, browser: node),
    'normalized-text': ExpressionType(
        node_to_normalized_text,
        none_filter,
        lambda nodes, browser: list(nodes),
        lambda node, browser: node),
    'link': ExpressionType(
        node_to_node,
        tag_filter('a'),
        Links,
        Link),
    }


class Expressions(object):

    def __init__(self, browser):
        self.__browser = browser
        self.__expressions = defaultdict(lambda: tuple((None, None, None)))

    def add(self, name, xpath=None, type='text', css=None, unique=False):
        if type not in EXPRESSION_TYPE:
            raise AssertionError(u'Unknown expression type %s' % type)
        finder = None
        if xpath is not None:
            finder = lxml.etree.XPath(xpath)
        elif css is not None:
            finder = lxml.cssselect.CSSSelector(css)
        if finder is None:
            raise AssertionError(
                u'You need to provide an XPath or CSS expression')
        self.__expressions[name] = (finder, type, unique)

    def __getattr__(self, name):
        finder, type, unique = self.__expressions[name]
        if finder is not None:
            if self.__browser.html is None:
                raise AssertionError(u'Not viewing HTML')
            expression = EXPRESSION_TYPE[type]
            nodes = filter(expression.filter,
                           map(expression.converter,
                               finder(self.__browser.html)))
            if unique:
                if len(nodes) > 1:
                    raise AssertionError(
                        u'Multiple elements found for %s where only '
                        u'one was expected.' % name)
                if not len(nodes):
                    return None
                return expression.node(nodes[0], self.__browser)
            return expression.nodes(nodes, self.__browser)
        raise AttributeError(name)


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
