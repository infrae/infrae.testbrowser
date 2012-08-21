# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import sysconfig
import urllib2

# You can add your platform here.
PLATFORM_MAPPING = {
    'win': 'WIN',
    'win32': 'WIN',
    'linux': 'LINUX',
    'freebsd': 'UNIX',
    'netbsd': 'UNIX',
    'openbsd': 'UNIX',
    'macosx': 'MAC'}


def get_current_platform():
    platform = sysconfig.get_platform()
    system = platform.split('-')[0]
    if system in PLATFORM_MAPPING:
        return PLATFORM_MAPPING[system]
    return 'ANY'



class HTTPRequest(urllib2.Request):
    """Extends the urllib2.Request to support GET, POST, PUT, DELETE
    request on demand.
    """

    def __init__(self, url, data=None, method=None):
        """Initialise a new HTTP request.

        Args:
          url - String for the URL to send the request to.
          data - Data to send with the request.
        """
        if method is None:
            method = data is not None and 'POST' or 'GET'
        elif method != 'POST' and method != 'PUT':
            data = None
        self._method = method
        urllib2.Request.__init__(self, url, data=data)

    def get_method(self):
        """Returns the HTTP method used by this request."""
        return self._method


class HTTPErrorResponse(object):
    """Represents an HTTP response where the status is not 200.

    Attributes:
      fp - File object for the response body.
      code - The HTTP status code returned by the server.
      headers - A dictionary of headers returned by the server.
      url - URL of the retrieved resource represented by this Response.
    """

    def __init__(self, fp, code, headers, url):
        self.fp = fp
        self.read = fp.read
        self.code = code
        self.headers = headers
        self.url = url

    def close(self):
        self.fp.close()
        self.fp = None
        self.read = None

    def info(self):
        return self.headers

    def geturl(self):
        return self.url


class HTTPErrorResponseHandler(urllib2.HTTPDefaultErrorHandler):
    """A custom HTTP error handler.

    Used to return an object instead of raising an HTTPError exception.
    """

    def http_error_default(self, req, fp, code, msg, headers):
        return HTTPErrorResponse(fp, code, headers, req.get_full_url())


def create_http_opener():
    return urllib2.build_opener(
        urllib2.HTTPRedirectHandler(),
        HTTPErrorResponseHandler())
