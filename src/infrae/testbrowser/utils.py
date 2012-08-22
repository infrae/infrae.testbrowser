# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import codecs
import functools
import mimetypes
import operator
import os
import urllib
import urlparse


def parse_charset(charsets):
    """Parse form accept charset and return a list of charset that can
    be used in Python.
    """
    seen = set()

    def resolve_charset(charset):
        if not charset:
            return None
        try:
            name = codecs.lookup(charset).name
            if name in seen:
                return None
            seen.add(name)
            return name
        except LookupError:
            return None
        return None

    return filter(lambda c: c != None,
                  map(resolve_charset,
                      reduce(operator.add,
                             map(lambda c: c.split(), charsets.split(',')))))

def charset_encoder(charset, value):
    """Encoder a value in the given charset.
    """
    if isinstance(value, unicode):
        return value.encode(charset, 'ignore')
    return str(value)

def resolve_url(url, browser):
    """Resolve an absolute url given the current browser location.
    """
    parsed = urlparse.urlparse(urllib.unquote(url))
    if (parsed.scheme in ('', 'http', 'https') and
        not parsed.path.startswith('/')):
        # Be sure to always not have any relative links
        parsed = list(parsed)
        base = '/'.join(browser.location.split('/')[:-1])
        parsed[2] = '/'.join((base, parsed[2]))
    return urlparse.urlunparse(parsed)

def resolve_location(url):
    """Resolve a location out of an url. It does the opposite of
    resolve_url.
    """
    parsed = urlparse.urlparse(urllib.unquote(url))
    if parsed.netloc:
        parsed = list(parsed)
        parsed[1] = ''
        parsed[0] = ''
    return urlparse.urlunparse(parsed)

def format_auth(user, password):
    return 'Basic ' + ':'.join((user, password)).encode('base64').strip()

def encode_multipart_form_data(fields, charset):
    """Encode form data as a mutlipart payload.
    """
    BOUNDARY = '------------uCtemt3iWu00F3QDhiwZ2nIQ$'
    data = []
    if isinstance(fields, dict):
        fields = fields.iteritems()
    for key, value in fields:
        data.append('--' + BOUNDARY)
        if isinstance(key, unicode):
            key = key.encode(charset)
        if isinstance(value, File):
            data.append(
                'Content-Disposition: form-data; name="%s"; filename="%s"' % (
                    key, unicode(value.filename).encode(charset)))
            data.append('Content-Type: %s' % value.content_type)
        else:
            data.append('Content-Disposition: form-data; name="%s"' % key)
        data.append('')
        if isinstance(data, unicode):
            data.append(value.encode(charset))
        else:
            data.append(str(value))
    data.append('--'+ BOUNDARY + '--')
    data.append('')
    return 'multipart/form-data; boundary=%s' % BOUNDARY, '\r\n'.join(data)


class File(object):

    def __init__(self, filename):
        self.__filename = filename

    @property
    def filename(self):
        return self.__filename

    @property
    def content_type(self):
        return (mimetypes.guess_type(self.__filename)[0] or
                'application/octet-stream')

    @property
    def data(self):
        if self.__filename:
            with open(self.__filename, 'rb') as data:
                return data.read()
        return ''

    def __str__(self):
        return self.data


def node_to_node(node):
    """To be used with ResultSet.
    """
    return node

def none_filter(node):
    """To be used with ResultSet.
    """
    return True


def compound_filter_factory(*functions):
    """To be used with ResultSet.
    """

    def compound_filter(element):
        for function in functions:
            if not function(element):
                return False
        return True

    return compound_filter


class ResultSet(object):
    """Clever collection type used as result of a browser expression.
    """

    def __init__(self, values):
        self._values = values

    def keys(self):
        return map(operator.itemgetter(1), self._values)

    def values(self):
        return list(map(operator.itemgetter(2), self._values))

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key][2]
        key = key.lower()
        matches = filter(lambda item: key in item[0], self._values)
        if not matches:
            raise KeyError(key)
        if len(matches) == 1:
            return matches[0][2]
        exact_matches = filter(lambda item: key == item[0], matches)
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
        return len(self._values)

    def __eq__(self, other):
        if isinstance(other, ResultSet):
            other = other.keys()
        return self.keys() == other

    def __ne__(self, other):
        if isinstance(other, ResultSet):
            other = other.keys()
        return self.keys() != other

    def __repr__(self):
        return repr(map(operator.itemgetter(1), self._values))


_marker = object()


class Handlers(object):
    """Browser handlers.
    """

    def __init__(self):
        self.__handlers = {}

    def add(self, name, handler, unique=False):
        if unique:
            if name not in self.__handlers:
                self.__handlers[name] = []
            self.__handlers[name].append(handler)
        else:
            self.__handlers[name] = handler

    def __contains__(self, name):
        return name in self.__handlers

    def get(self, name, default=None):
        if name not in self.__handlers:
            return default

        handlers = self.__handlers[name]
        if isinstance(handlers, list):
            def wrapper(*args, **kwargs):
                for handler in handlers:
                    handler(*args, **kwargs)

            return wrapper
        return handlers

    def __getitem__(self, name):
        handler = self.get(name, _marker)
        if handler is _marker:
            raise KeyError(name)
        return handler

    def __getattr__(self, name):
        handler = self.get(name, _marker)
        if handler is _marker:
            raise AttributeError(name)
        return handler


class Macros(object):
    """Browser macros.
    """

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
    """Browser options (configurable from the operating system).
    """

    def __init__(self, interface=None):
        if interface is not None:
            for name, _ in interface.namesAndDescriptions():
                key = 'TESTBROWSER_%s' % name.upper()
                if key in os.environ:
                    setattr(self, name, os.environ[key])
