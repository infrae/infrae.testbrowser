# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import functools
import operator
import os

def node_to_node(node):
    return node

def none_filter(node):
    return True


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


class Macros(object):

    def __init__(self, browser):
        self.__browser = browser
        self.__macros = {}

    def add(self, name, macro):
        self.__macros[name] = functools.partial(macro, self.__browser)

    def __getattr__(self, name):
        macro = self.__macros.get(name)
        if macro is not None:
            return macro
        raise AttributeError(name)


class CustomizableOptions(object):

    def __init__(self, interface=None):
        if interface is not None:
            for name, _ in interface.namesAndDescriptions():
                key = 'TESTBROWSER_%s' % name.upper()
                if key in os.environ:
                    setattr(self, os.environ[key])
