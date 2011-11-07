# -*- coding: utf-8 -*-
# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.interface import Interface, Attribute

_marker = object()


class IBrowser(Interface):
    """Test browser interface.
    """
    inspect = Attribute(u"Browser Expression (inspect current HTML)")
    macros = Attribute(u"Browser macros")
    options = Attribute(u"Options")
    handlers = Attribute(u"Handlers used to customize browser behavior")

    url = Attribute(u"Currently viewed URL")
    location = Attribute(u"Currently viewed path")
    contents = Attribute(u"Payload")
    html = Attribute(u"HTML payload parsed by LXML, or None")

    def __enter__():
        """Use a browser as a context manager. It will auto-close at
        the end of the context.
        """

    def __exit__(exc_type, exc_val, exc_tb):
        """Use a browser as a context manager. It will auto-close at
        the end of the context.
        """

    def open(url):
        """Open the given URL.
        """

    def close():
        """Close the browser.
        """

    def reload():
        """Reload the current opened URL, re-submitting [form] data if
        any where sent.
        """

    def login(user, password=_marker):
        """Set a HTTP Basic authorization header in the requests that
        are sent to the server. If no ``password`` is provided, the
        ``login`` will be used as ``password``.

        If ``login`` is None, it will remove any set HTTP Basic
        authorization header.
        """

    def logout():
        """Remove an HTTP Basic authorization set.
        """

    def get_form(name=None, id=None):
        """Return the identified form as a form object, or raise an
        AssertionError if no matching form are found.
        """

    def get_link(content):
        """Return a link that matches ``content``.
        """


class IAdvancedBrowser(IBrowser):
    """Browser with more low level API to the HTTP layer.
    """
    method = Attribute(u"Method used to view the current page")
    status = Attribute(u"HTTP status")
    status_code = Attribute(u"HTTP status code as an integer")
    content_type = Attribute(u"Content type")
    content_encoding = Attribute(u"Content encoding")
    headers = Attribute(u"Dictionary like access to response headers")
    history = Attribute(u"Last previously viewed URLs")
    xml = Attribute(u"XML payload parsed by LXML, or None")

    def set_request_header(key, value):
        """Set an HTTP header ``key`` to the given ``value`` for each
        request made to the server.
        """

    def get_request_header(key):
        """Get the value or None corresponding to the HTTP header
        ``key`` that are sent to the server.
        """

    def del_request_header(key):
        """If set, remove the HTTP header ``key`` from each request
        made to the server.
        """

    def clear_request_headers():
        """Clear all custom added HTTP headers that are sent to the
        server each time a request is made.
        """

    def open(url, method='GET', query=None,
             form=None, form_enctype='application/x-www-form-urlencoded'):
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


class IClickableFormControl(IFormControl):

    def click():
        """Click that control.
        """


class ISubmitableFormControl(IClickableFormControl):

    def submit():
        """Submit the current form.
        """


class IForm(Interface):
    """Represent a form.
    """
    name = Attribute(u"HTML name of the form")
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


class ICustomizableOptions(Interface):
    server = Attribute(u'Name of the server to use')
    port = Attribute(u'Port of the server to use')


class ISeleniumCustomizableOptions(Interface):
    # We don't inherit from ICustomizableOptions due zope.interface API suckiness
    server = Attribute(u'Name of the server to use')
    port = Attribute(u'Port of the server to use')
    browser = Attribute(u'Browser to use firefox/internet explorer/chrome')
    selenium_host = Attribute(u'Host to use to connect to Selenium')
    selenium_port = Attribute(u'Port to use to connect to Selenium')
    selenium_platform = Attribute(u'Platform to request to Selenium')

# API of sub components.

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

