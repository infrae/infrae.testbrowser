# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt

import re

from zope.interface import implements
from infrae.testbrowser.interfaces import ICookies, ICookie


class Cookie(object):
    """Represent a single cookie value.
    """
    implements(ICookie)
    QPARMRE= re.compile(
            '([\x00- ]*([^\x00- ;,="]+)="([^"]*)"([\x00- ]*[;,])?[\x00- ]*)')
    PARMRE = re.compile(
            '([\x00- ]*([^\x00- ;,="]+)=([^;]*)([\x00- ]*[;,])?[\x00- ]*)')
    PARAMLESSRE = re.compile(
            '([\x00- ]*([^\x00- ;,="]+)[\x00- ]*[;,][\x00- ]*)')

    def __init__(self, name, value, options=None):
        self.name = name
        self.value = value
        self.options = {}
        if options is not None:
            self.options = {}

    @classmethod
    def parse(cls, text, result=None):
        """Parse a cookie, and return a dictionnary (code inspired
        from the Zope 2 parse_cookie function).
        """
        mo_q = cls.QPARMRE.match(text)

        if mo_q:
            # Match quoted correct cookies
            l = len(mo_q.group(1))
            name = mo_q.group(2)
            value = mo_q.group(3)
        else:
            # Match evil MSIE cookies ;)
            mo_p = cls.PARMRE.match(text)

            if mo_p:
                l = len(mo_p.group(1))
                name = mo_p.group(2)
                value = mo_p.group(3)
            else:
                # Broken Cookie without = nor value.
                broken_p = cls.PARAMLESSRE.match(text)
                if broken_p:
                    l = len(broken_p.group(1))
                    name = broken_p.group(2)
                    value = ''
                else:
                    return result
        if result is not None:
            result.options[name] = value
        else:
            result = cls(name, value)
        return cls.parse(text[l:], result)

    def __repr__(self):
        return '%s=%s' % (self.name, self.value)


class Cookies(object):
    """A cookie container.
    """
    implements(ICookies)

    def __init__(self):
        self.clear()

    def add(self, name, value):
        if name not in self.cookies:
            self.cookies[name] = Cookie(name, value)
        else:
            self.cookies[name].value = value

    def parse(self, text):
        cookie = Cookie.parse(text)
        if cookie is not None:
            self.cookies[cookie.name] = cookie

    def clear(self):
        self.cookies = {}

    def keys(self):
        return self.cookies.keys()

    def __getitem__(self, key):
        return self.cookies[key]

    def __contains__(self, key):
        return key in self.cookies

    def __len__(self):
        return len(self.cookies)

    def __eq__(self, other):
        if isinstance(other, Cookies):
            other = other.keys()
        return self.keys() == other

    def __ne__(self, other):
        if isinstance(other, Cookies):
            other = other.keys()
        return self.keys() != other

    def get_request_headers(self):
        """Return the headers to use in the next request.
        """
        if self.cookies:
            result = ''
            for cookie in self.cookies.values():
                if result:
                    result += "; "
                result += '%s=%s' % (cookie.name, cookie.value)
            return {'Cookie': result}
        return {}

    def __repr__(self):
        cookies = '; '.join(map(repr, self.cookies.values()))
        if cookies:
            return cookies
        return '<no cookies>'
