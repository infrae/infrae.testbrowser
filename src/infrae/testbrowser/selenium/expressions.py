# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$


from collections import defaultdict

from infrae.testbrowser.common import node_to_node, none_filter
from infrae.testbrowser.common import ExpressionResult


def node_to_text(node):
    return node.text

def tag_filter(name):
    def element_filter(element):
        return element.tag_name == name
    return element_filter


class Link(object):

    def __init__(self, element):
        self.element = element
        self.text = element.text
        # Need to absolutize url
        self.url = element.get_attribute('href')

    def click(self):
        self.element.click()

    def __str__(self):
        return self.text

    def __repr__(self):
        return repr(self.text)


class Links(ExpressionResult):

    def __init__(self, links):
        super(Links, self).__init__(
            map(lambda link: (str(link).lower(), str(link), link),
                map(lambda link: Link(link), links)))


EXPRESSION_TYPE = {
    'text': (
        node_to_text,
        none_filter,
        lambda elements: list(elements)),
    'link': (
        node_to_node,
        tag_filter('a'),
        Links),
    }


class Expressions(object):

    def __init__(self, runner):
        self.__runner = runner
        self.__expressions = defaultdict(lambda: tuple((None, None)))

    def add(self, name, xpath=None, type='text', css=None):
        assert type in EXPRESSION_TYPE, u'Unknown expression type %s' % type
        finder = None
        if xpath is not None:
            finder = lambda d: d.find_elements_by_xpath(xpath)
        elif css is not None:
            finder = lambda d: d.find_elements_by_css_selector(css)
        assert finder is not None, u'You need to provide an XPath or CSS expression'
        self.__expressions[name] = (finder, type)

    def __getattr__(self, name):
        finder, type = self.__expressions[name]
        if finder is not None:
            node_converter, node_filter, factory = EXPRESSION_TYPE[type]
            return factory(filter(node_filter,
                                  map(node_converter,
                                      self.__runner(finder))))
        raise AttributeError(name)
