# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import urllib


def node_to_text(node):
    return node.text_content().strip()


class Expressions(object):

    def __init__(self, browser):
        self.__browser = browser
        self.__expressions = {}

    def add(self, name, xpath):
        self.__expressions[name] = xpath

    def __getattr__(self, name):
        expression = self.__expressions.get(name)
        if expression:
            assert self.__browser.html is not None, u'Not viewing HTML'
            return map(node_to_text, self.__browser.html.xpath(expression))
        raise AttributeError(name)


class Link(object):

    def __init__(self, html, browser):
        self.html = html
        self.browser = browser

    @property
    def url(self):
        return urllib.unquote(self.html.attrib['href'])

    def click(self):
        return self.browser.open(self.url)


class Links(object):

    def __init__(self, links, browser):
        self.__browser = browser
        self.__links = links

    def keys(self):
        return map(node_to_text, self.__links)

    def values(self):
        return map(lambda l: Link(l, self.__browser), self.__links)

    def __getitem__(self, key):
        matches = filter(lambda l: key in l.text_content(), self.__links)
        if not matches:
            raise KeyError(key)
        if len(matches) == 1:
            return Link(matches[0], self.__browser)
        raise AssertionError("Multiple matches (%d)" % len(matches), matches)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default


class ExpressionLinks(object):

    def __init__(self, browser):
        self.__browser = browser
        self.__links = {}

    def add(self, name, xpath):
        self.__links[name] = xpath

    def __getattr__(self, name):
        expression = self.__links[name]
        if expression:
            assert self.__browser.html is not None, u'Not viewing HTML'
            links = filter(lambda l: l.tag == 'a',
                           self.__browser.html.xpath(expression))
            return Links(links, self.__browser)
        raise AttributeError(name)
