# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import operator
import lxml
from collections import defaultdict

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

def node_to_node(node):
    return node

def none_filter(node):
    return True

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
        return self.text

    def __repr__(self):
        return repr(self.text)


class ExpressionResult(object):

    def __init__(self, values):
        self.__values = values

    def keys(self):
        return map(operator.itemgetter(1), self.__values)

    def values(self):
        return list(map(operator.itemgetter(2), self.__values))

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key):
        key = key.lower()
        matches = filter(lambda link: key in link[0], self.__values)
        if not matches:
            raise KeyError(key)
        if len(matches) == 1:
            return matches[0][2]
        exact_matches = filter(lambda link: key == link[0], matches)
        if len(exact_matches) == 1:
            return exact_matches[0][2]
        raise AssertionError(
            "Multiple matches (%d)" % len(matches), map(str, matches))

    def __contains__(self, key):
        try:
            self.__getitem__(key)
            return True
        except (KeyError, AssertionError):
            return False

    def __len__(self):
        return len(self.__values)

    def __eq__(self, other):
        if isinstance(other, ExpressionResult):
            other = other.keys()
        return self.keys() == other

    def __ne__(self, other):
        if isinstance(other, ExpressionResult):
            other = other.keys()
        return self.keys() != other

    def __repr__(self):
        return repr(map(operator.itemgetter(1), self.__values))


class Links(ExpressionResult):

    def __init__(self, links, browser):
        super(Links, self).__init__(
            map(lambda link: (str(link).lower(), str(link), link),
                map(lambda link: Link(link, browser), links)))


EXPRESSION_TYPE = {
    'text': (
        node_to_text,
        none_filter,
        lambda nodes, browser: list(nodes)),
    'normalized-text': (
        node_to_normalized_text,
        none_filter,
        lambda nodes, browser: list(nodes)),
    'link': (
        node_to_node,
        tag_filter('a'),
        Links),
    }


class Expressions(object):

    def __init__(self, browser):
        self.__browser = browser
        self.__expressions = defaultdict(lambda: tuple((None, None)))

    def add(self, name, xpath=None, type='text', css=None):
        assert type in EXPRESSION_TYPE, u'Unknown expression type %s' % type
        expression = None
        if xpath is not None:
            expression = lxml.etree.XPath(xpath)
        elif css is not None:
            expression = lxml.cssselect.CSSSelector(css)
        assert expression is not None, u'You need to provide an XPath or CSS expression'
        self.__expressions[name] = (expression, type)

    def __getattr__(self, name):
        expression, type = self.__expressions[name]
        if expression is not None:
            assert self.__browser.html is not None, u'Not viewing HTML'
            node_converter, node_filter, factory = EXPRESSION_TYPE[type]
            return factory(filter(node_filter,
                                  map(node_converter,
                                      expression(self.__browser.html))),
                           self.__browser)
        raise AttributeError(name)
