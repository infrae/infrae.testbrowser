# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import urlparse
import atexit

from infrae.testbrowser.common import Macros, CustomizableOptions
from infrae.testbrowser.interfaces import IBrowser, _marker
from infrae.testbrowser.interfaces import ISeleniumCustomizableOptions
from infrae.testbrowser.selenium.expressions import Expressions, Link
from infrae.testbrowser.selenium.form import Form
from infrae.testbrowser.selenium.server import Server
from infrae.testbrowser.selenium.utils import get_current_platform

import selenium.webdriver
from zope.interface import implements
from zope.testing.cleanup import addCleanUp


class SeleniumDrivers(object):
    """Manage all active Selenium drivers.
    """

    def __init__(self):
        self.__drivers = {}

    def get(self, options):
        """Return a Selenium driver associated to this set of options.
        """
        command_executor = 'http://%s:%s/wd/hub' % (
            options.selenium_host,
            options.selenium_port)
        driver_key = (command_executor,
                      options.selenium_platform,
                      options.browser)
        if driver_key in self.__drivers:
            return self.__drivers[driver_key]

        driver = selenium.webdriver.Remote(
            command_executor=command_executor,
            desired_capabilities={
                'browserName': options.browser,
                'javascriptEnabled': options.enable_javascript,
                'platform': options.selenium_platform})
        self.__drivers[driver_key] = driver
        return driver

    def all(self):
        for key, driver in self.__drivers.iteritems():
            yield driver

    def clear(self):
        for driver in self.all():
            driver.close()
            driver.stop_client()
        self.__drivers = {}


DRIVERS = SeleniumDrivers()
addCleanUp(DRIVERS.clear)
atexit.register(DRIVERS.clear)


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


class Browser(object):
    implements(IBrowser)

    def __init__(self, app):
        self.options = Options()
        self.inspect = Expressions(lambda f: f(self.__driver))
        self.macros = Macros(self)
        self.__server = Server(app, self.options)
        self.__driver = None
        self.__user = None
        self.__password = None

    @property
    def url(self):
        if self.__driver is not None:
            return self.__driver.current_url
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
            return self.__driver.get_page_source()
        return None

    def __verify_driver(self):
        if self.__driver is None:
            self.__server.start()
            self.__driver = DRIVERS.get(self.options)

    def __absolute_url(self, url):
        url_parts = list(urlparse.urlparse(url))
        if not url_parts[0]:
            url_parts[0] = 'http'
        if not url_parts[1]:
            url_parts[1] = ':'.join((self.options.server, str(self.options.port)))
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
        if password is _marker:
            password = user
        self.__user = user
        self.__password = password

    def logout(self):
        self.__user = None
        self.__password = None

    def open(self, url):
        self.__verify_driver()
        self.__driver.get(self.__absolute_url(url))

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
        elements = self.__driver.find_elements_by_xpath(expression)
        assert len(elements) == 1, u'No form found'
        return Form(elements[0])

    def get_link(self, content):
        assert self.__driver is not None, u'Not viewing anything'
        elements = self.__driver.find_elements_by_link_text(content)
        assert len(elements) == 1, u'No link found'
        return Link(elements[0])

    def close(self):
        self.__server.stop()
