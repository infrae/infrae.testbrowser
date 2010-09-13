# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import urllib
from collections import defaultdict


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
        self.title = html.text_content()

    @property
    def url(self):
        return urllib.unquote(self.html.attrib['href'])

    def click(self):
        return self.browser.open(self.url)

    def __str__(self):
        return self.title

    def __repr__(self):
        return repr(self.title)


class Links(object):

    def __init__(self, links, browser):
        self.__browser = browser
        self.__links = map(lambda link: Link(link, browser), links)

    def keys(self):
        return map(str, self.__links)

    def values(self):
        return list(self.__links)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key):
        key = key.lower()
        matches = filter(lambda l: key in str(l).lower(), self.__links)
        if not matches:
            raise KeyError(key)
        if len(matches) == 1:
            return matches[0]
        raise AssertionError(
            "Multiple matches (%d)" % len(matches), map(str, matches))

    def __contains__(self, key):
        try:
            self.__getitem__(key)
            return True
        except (KeyError, AssertionError):
            return False

    def __len__(self):
        return len(self.__links)

    def __eq__(self, other):
        if isinstance(other, Links):
            other = other.keys()
        return self.keys() == other

    def __ne__(self, other):
        if isinstance(other, Links):
            other = other.keys()
        return self.keys() != other

    def __repr__(self):
        return repr(map(str, self.__links))


EXPRESSION_TYPE = {
    'text': (node_to_text, none_filter, lambda nodes, browser: list(nodes)),
    'link': (node_to_node, tag_filter('a'), Links),
    }


class Expressions(object):

    def __init__(self, browser):
        self.__browser = browser
        self.__expressions = defaultdict(lambda: tuple((None, None)))

    def add(self, name, xpath, type='text'):
        assert type in EXPRESSION_TYPE, u'Unknown expression type %s' % type
        self.__expressions[name] = (xpath, type)

    def __getattr__(self, name):
        expression, type = self.__expressions[name]
        if expression is not None:
            assert self.__browser.html is not None, u'Not viewing HTML'
            node_converter, node_filter, factory = EXPRESSION_TYPE[type]
            return factory(filter(node_filter,
                                  map(node_converter,
                                      self.__browser.html.xpath(expression))),
                           self.__browser)
        raise AttributeError(name)
