# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt

import operator

from zope.interface import implements
from infrae.testbrowser.interfaces import ICookies, ICookie


class Cookie(object):
    implements(ICookie)

    def __init__(self, options):
        self.name = options['name']
        self.value = options['value']
        self.options = options

    def __repr__(self):
        return '%s=%s' % (self.name, self.value)


class Cookies(object):
    """Cookies API for selenium.
    """
    implements(ICookies)

    def __init__(self, driver):
        self.__driver = driver

    def add(self, name, value):
        if self.__driver is not None:
            self.__driver.set_cookie(name, value)

    def clear(self):
        if self.__driver is not None:
            self.__driver.clear_cookies()

    def keys(self):
        if self.__driver is not None:
            return map(operator.itemgetter('name'), self.__driver.cookies)
        return []

    def __getitem__(self, key):
        if self.__driver is not None:
            for cookie in self.__driver.cookies:
                if cookie['name'] == key:
                    return Cookie(cookie)
        raise KeyError

    def __contains__(self, key):
        return key in self.keys()

    def __len__(self):
        if self.__driver is not None:
            return len(self.__driver.cookies)
        return 0

    def __eq__(self, other):
        if isinstance(other, Cookies):
            other = other.keys()
        return self.keys() == other

    def __ne__(self, other):
        if isinstance(other, Cookies):
            other = other.keys()
        return self.keys() != other

    def __repr__(self):
        if self.__driver is not None:
            cookies = '; '.join(map(repr, map(Cookie, self.__driver.cookies)))
            if cookies:
                return cookies
        return '<no cookies>'
