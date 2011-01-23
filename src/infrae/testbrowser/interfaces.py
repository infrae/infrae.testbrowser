# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.interface import Interface, Attribute

_marker = object()

class IWSGIResponse(Interface):
    status = Attribute(u'HTTP status line')
    headers = Attribute(u'Response headers')
    output = Attribute(u'Response data (except headers)')


class IWSGIServer(Interface):
    server = Attribute(u'Server hostname')
    port = Attribute(u'Server port')
    protocol = Attribute(u'HTTP procotol version')

    def get_default_environ():
        pass

    def get_environ(method, uri, headers, data=None, data_type=None):
        pass

    def __call__(method, uri, headers, data=None, data_type=None):
        """Compute the a response for the query. This return a
        IWSGIResponse object.
        """


class IBrowser(Interface):
    """Test browser interface.
    """
    url = Attribute(u"Currently viewed URL")
    location = Attribute(u"Currently viewed path")
    method = Attribute(u"Method used to view the current page")
    status = Attribute(u"HTTP status")
    status_code = Attribute(u"HTTP status code as an integer")
    headers = Attribute(u"Dictionary like access to response headers")
    content_type = Attribute(u"Content type")
    contents = Attribute(u"Payload")
    html = Attribute(u"HTML payload parsed by LXML, or None")
    history = Attribute(u"Last previously viewed URLs")

    def set_request_header(key, value):
        """Set an HTTP header ``key`` to the given ``value`` for each
        request made to the server.
        """

    def get_request_header(key):
        """Get the value or None corresponding to the HTTP header
        ``key`` that are sent to the server.
        """

    def clear_request_headers():
        """Clear all custom added HTTP headers that are sent to the
        server each time a request is made.
        """

    def login(user, password=_marker):
        """Set a HTTP Basic authorization header in the requests that
        are sent to the server. If no ``password`` is provided, the
        ``login`` will be used as ``password``.
        """

    def open(url, method='GET', query=None,
             form=None, form_enctype='application/x-www-form-urlencoded'):
        pass

    def reload():
        """Reload the current opened URL, re-submitting [form] data if
        any where sent.
        """

    def get_form(name=None, id=None):
        """Return the identified form as a form object, or raise an
        AssertionError if no matching form are found.
        """

    def get_link(content):
        pass


class IFormControl(Interface):
    """Represent a control in a form.
    """
    name = Attribute(u"Control name")
    type = Attribute(u"Control type (text, file, radio, select)")
    value = Attribute(u"Control value")
    multiple = Attribute(u"Does control hold multiple values?")
    options = Attribute(u"Vocabulary from which the control can "
                        u"takes his values, if limited")
    checkable = Attribute(u"Is the control checkable?")
    checked = Attribute(u"If the control is checkable, is it checked")


class IForm(Interface):
    """Represent a form.
    """
    action = Attribute(u"URL to which the form is submitted")
    method = Attribute(u"Method used to submit the form")
    enctype = Attribute(u"Encoding type used to submit the form")
    accept_charset = Attribute(u"Charset used to submit the form")
    controls = Attribute(u"Dict containing all the controls")

    def get_control(name):
        """Return the control identified by name or raise an
        AssertionError.
        """

    def submit(name=None, value=None):
        """Submit the form as-it. ``name`` and ``value`` let you add
        an extra value to the submission.
        """
