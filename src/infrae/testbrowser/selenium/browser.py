# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import urlparse
import lxml.html

from infrae.testbrowser.interfaces import IBrowser, _marker
from infrae.testbrowser.interfaces import ISeleniumCustomizableOptions
from infrae.testbrowser.selenium.cookies import Cookies
from infrae.testbrowser.selenium.driver import DRIVERS
from infrae.testbrowser.selenium.expressions import Expressions, Link
from infrae.testbrowser.selenium.form import Form
from infrae.testbrowser.selenium.server import Server
from infrae.testbrowser.selenium.utils import get_current_platform
from infrae.testbrowser.utils import Macros, CustomizableOptions, Handlers

from zope.interface import implements


class Options(CustomizableOptions):
    implements(ISeleniumCustomizableOptions)
    enable_javascript = True
    browser = 'firefox'
    selenium_platform = None
    selenium_host = 'localhost'
    selenium_port = '4444'
    server = 'localhost'
    port = '8000'

    def __init__(self):
        super(Options, self).__init__(ISeleniumCustomizableOptions)
        if self.selenium_platform is None:
            self.selenium_platform = get_current_platform()


def SeleniumElementProxyFactory(browser):
    """Call browser handlers if need when a SeleniumElement method is called.
    """

    class  SeleniumElementProxy(object):

        def __init__(self, session, element):
            self.__session = session
            self.__element = element

        def __getattr__(self, name):
            attribute = getattr(self.__element, name)
            if callable(attribute):
                handler = browser.handlers.get('on' + name)
                if handler is not None:

                    def wrapper(*args, **kwargs):
                        value = attribute(*args, **kwargs)
                        return handler(
                            browser, self.__session, self.__element, value)

                    return wrapper

            return attribute

    def __eq__(self, other):
        return self.__element.text == other

    def __ne__(self, other):
        return self.__element.text != other

    return SeleniumElementProxy


class Browser(object):
    implements(IBrowser)

    def __init__(self, app):
        self.options = Options()
        self.inspect = Expressions(lambda f: f(self.__driver))
        self.macros = Macros(self)
        self.handlers = Handlers()
        self.cookies = Cookies(None)
        self.__server = Server(app, self.options)
        self.__driver = None
        self.__user = None
        self.__password = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def url(self):
        if self.__driver is not None:
            return self.__driver.url
        return None

    @property
    def location(self):
        url = self.url
        if url is not None:
            return urlparse.urlparse(url).path
        return None

    @property
    def contents(self):
        if self.__driver is not None:
            return self.__driver.contents
        return None

    @property
    def html(self):
        contents = self.contents
        if contents is not None:
            return lxml.html.document_fromstring(contents)
        return None

    def __verify_driver(self):
        if self.__driver is None:
            self.__driver = DRIVERS.get(
                self.options,
                SeleniumElementProxyFactory(self))
            self.cookies = Cookies(self.__driver)
            self.__server.start()

    def __absolute_url(self, url):
        url_parts = list(urlparse.urlparse(url))
        if not url_parts[0]:
            url_parts[0] = 'http'
        if not url_parts[1]:
            url_parts[1] = ':'.join(
                (self.options.server, str(self.options.port)))
            if self.__user is not None:
                user = self.__user
                if self.__password is not None:
                    user = ':'.join((user, self.__password))
                url_parts[1] = '@'.join((user, url_parts[1]))
        if url_parts[2] and not url_parts[2][0] == '/':
            location = self.location
            if location is not None:
                url_parts[2] = '/'.join((location, url_parts[2]))
        return urlparse.urlunparse(url_parts)

    def login(self, user, password=_marker):
        if user is None:
            self.logout()
        if password is _marker:
            password = user
        if 'login' in self.handlers:
            self.handlers.login.login(self, user, password)
        else:
            self.__user = user
            self.__password = password

    def logout(self):
        if 'login' in self.handlers:
            self.handlers.login.logout(self)
        else:
            self.__user = None
            self.__password = None

    def open(self, url):
        self.__verify_driver()
        self.__driver.open(self.__absolute_url(url))
        if 'open' in self.handlers:
            self.handlers.open(self, self.__driver)

    def reload(self):
        assert self.__driver is not None, u'Nothing loaded to reload'
        self.__driver.refresh()

    def get_form(self, name=None, id=None):
        assert self.__driver is not None, u'Not viewing anything'
        expression = None
        if name is not None:
            expression = '//form[@name="%s"]' % name
        elif id is not None:
            expression = '//form[@id="%s"]' % id
        assert expression is not None, u'Provides an id or a name to get_form'
        elements = self.__driver.get_elements(xpath=expression)
        assert len(elements) == 1, u'No form found'
        return Form(elements[0])

    def get_link(self, content):
        assert self.__driver is not None, u'Not viewing anything'
        elements = self.__driver.get_elements(link=content)
        assert len(elements) == 1, u'No link found'
        return Link(elements[0])

    def close(self):
        if 'close' in self.handlers:
            self.handlers.close(self)
        self.__server.stop()
