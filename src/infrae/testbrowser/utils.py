# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import urlparse
import urllib
import mimetypes


def resolve_url(link, browser):
    parsed = urlparse.urlparse(urllib.unquote(link))
    if not parsed.path.startswith('/'):
        # Be sure to always not have any relative links
        parsed = list(parsed)
        base = '/'.join(browser.location.split('/')[:-1])
        parsed[2] = '/'.join((base, parsed[2]))
    return urlparse.urlunparse(parsed)

def format_auth(user, password):
    return 'Basic ' + ':'.join((user, password)).encode('base64').strip()

def encode_multipart_form_data(fields):
    BOUNDARY = '------------uCtemt3iWu00F3QDhiwZ2nIQ$'
    data = []
    if isinstance(fields, dict):
        fields = fields.iteritems()
    for key, value in fields:
        data.append('--' + BOUNDARY)
        if isinstance(value, File):
            data.append(
                'Content-Disposition: form-data; name="%s"; filename="%s"' % (
                    key, value.filename))
            data.append('Content-Type: %s' % value.content_type)
        else:
            data.append('Content-Disposition: form-data; name="%s"' % key)
        data.append('')
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
