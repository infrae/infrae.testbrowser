# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import json
import atexit
import urllib2
from unittest import SkipTest

from zope.testing.cleanup import addCleanUp

from infrae.testbrowser.selenium import utils
from infrae.testbrowser.selenium import errors


class Connection(object):
    """Connection to the Selenium server that is able to send commands
    and read results.
    """

    def __init__(self, url):
        self.url = url
        self.open = utils.create_http_opener().open

    def send(self, method, path, parameters):
        """Send a query to Selenium.
        """
        url = ''.join((self.url, path))
        data = json.dumps(parameters) if parameters else None
        request = utils.HTTPRequest(url=url, data=data, method=method)
        request.add_header('Accept', 'application/json')
        try:
            return self.validate(self.receive(self.open(request)))
        except urllib2.URLError as error:
            if error.args[0].errno == 61:
                raise SkipTest("Selenium unavailable")
            raise errors.SelectionConnectionError({'message': str(error)})

    def receive(self, response):
        """Receive and decrypt Selenium response.
        """
        try:
            if response.code > 399 and response.code < 500:
                return {'status': response.code,
                        'value': response.read()}

            body = response.read().replace('\x00', '').strip()
            content_type = response.info().getheader('Content-Type') or []
            if 'application/json' in content_type:
                data = json.loads(body)
                assert type(data) is dict, 'Invalid server response'
                assert 'status' in data, 'Invalid server response'
                if 'value' not in data:
                    data['value'] = None
                return data
            elif 'image/png' in content_type:
                data = {'status': 0,
                        'value': body.strip()}
                return data
            # 204 is a standart POST no data result. It is a success!
            return {'status': 0}
        finally:
            response.close()

    def validate(self, data):
        """Validate received data against Selenium error.
        """
        if data['status']:
            error = errors.CODE_TO_EXCEPTION.get(data['status'])
            if error is None:
                error = errors.SeleniumUnknownError
            raise error(data['value'])
        return data


class Selenium(object):
    """Connection to the Selenium server.
    """

    def __init__(self, host, port):
        self.__connection = Connection(
            'http://%s:%s/wd/hub' % (host, port))

    def new_session(self, options, element_proxy=None):
        data = self.__connection.send(
            'POST', '/session', {'desiredCapabilities': options})
        return SeleniumSession(
            self.__connection, data, element_proxy)


class Seleniums(object):
    """Manage all active Seleniums instances.
    """

    def __init__(self):
        self.__sessions = {}

    def get(self, connection_options, element_proxy=None):
        """Return a Selenium driver associated to this set of options.
        """
        key = (connection_options.selenium_host,
               connection_options.selenium_port,
               connection_options.selenium_platform,
               connection_options.browser)
        if key in self.__sessions:
            return self.__sessions[key]

        session = Selenium(
            connection_options.selenium_host,
            connection_options.selenium_port).new_session(
            {'browserName': connection_options.browser,
             'javascriptEnabled': connection_options.enable_javascript,
             'platform': connection_options.selenium_platform},
            element_proxy)
        self.__sessions[key] = session
        return session

    def all(self):
        return self.__sessions.itervalues()

    def clear(self):
        for session in self.all():
            try:
                session.quit()
            except SkipTest:
                pass
        self.__sessions = {}


DRIVERS = Seleniums()
addCleanUp(DRIVERS.clear)
atexit.register(DRIVERS.clear)

ELEMENT_PARAMETERS = {
    'css': 'css selector',
    'id': 'id',
    'name': 'name',
    'link': 'link text',
    'partial_link': 'partial link text',
    'tag': 'tag name',
    'xpath': 'xpath'}


def get_element_parameters(how):
    assert len(how) == 1, u'Can only specify one way to retrieve an element'
    key = how.keys()[0]
    assert key in ELEMENT_PARAMETERS, 'Invalid way to retrieve an element'
    return {'using': ELEMENT_PARAMETERS[key],
            'value': how[key]}


class SeleniumSession(object):
    """A selenium session.
    """

    def __init__(self, connection, info, element_proxy=None):
        self.__connection = connection
        self.__path = ''.join(('/session/', info['sessionId']))
        self.__capabilities = info['value']
        self.__element_proxy = element_proxy
        self.__send('POST', '/timeouts/async_script', {'ms': 120000})

    def __send(self, method, path, data=None):
        return self.__connection.send(
            method, ''.join((self.__path, path)), data)

    @property
    def title(self):
        return self.__send('GET', '/title')['value']

    @property
    def url(self):
        return self.__send('GET', '/url')['value']

    @property
    def contents(self):
        return self.__send('GET', '/source')['value']

    def refresh(self):
        self.__send('POST', '/refresh')

    def back(self):
        self.__send('POST', '/back')

    def forward(self):
        self.__send('POST', '/forward')

    def open(self, url):
        self.__send('POST', '/url', {'url': url})

    def close(self):
        self.__send('DELETE', '/window')

    def execute(self, script, args):
        return self.__send(
            'POST', '/execute_async',
            {'script': script, 'args': args})['value']

    def quit(self):
        self.__send('DELETE', '')

    def __element_factory(self, data):
        element = SeleniumElement(self.__connection, self.__path, data)
        if self.__element_proxy is not None:
            element = self.__element_proxy(self, element)
        return element

    def get_active_element(self):
        data = self.__send('POST', '/element/active')
        return self.__element_factory(data['value'])

    def get_element(self, **how):
        data = self.__send('POST', '/element', get_element_parameters(how))
        return self.__element_factory(data['value'])

    def get_elements(self, **how):
        data = self.__send('POST', '/elements', get_element_parameters(how))
        return map(lambda d: self.__element_factory(d), data['value'])


class SeleniumElement(object):

    def __init__(self, connection, session_path, info):
        self.__connection = connection
        self.__session_path = session_path
        self.__path = ''.join((session_path, '/element/', info['ELEMENT']))

    def __send(self, method, path, data=None):
        return self.__connection.send(
            method, ''.join((self.__path, path)), data)

    @property
    def tag(self):
        return self.__send('GET', '/name')['value']

    @property
    def text(self):
        return self.__send('GET', '/text')['value']

    @property
    def value(self):
        return self.__send('GET', '/value')['value']

    @property
    def is_enabled(self):
        return self.__send('GET', '/enabled')['value']

    @property
    def is_displayed(self):
        return self.__send('GET', '/displayed')['value']

    @property
    def is_selected(self):
        return self.__send('GET', '/selected')['value']

    def send_keys(self, keys):
        self.__send('POST', '/value', {'value': list(keys)})

    def click(self):
        self.__send('POST', '/click')

    def clear(self):
        self.__send('POST', '/clear')

    def submit(self):
        self.__send('POST', '/submit')

    def get_attribute(self, name):
        return self.__send('GET', ''.join(('/attribute/', name)))['value']

    def get_css(self, name):
        return self.__send('GET', ''.join(('/css/', name)))['value']

    def __element_factory(self, data):
        return self.__class__(self.__connection, self.__session_path, data)

    def get_element(self, **how):
        data = self.__send('POST', '/element', get_element_parameters(how))
        return self.__element_factory(data['value'])

    def get_elements(self, **how):
        data = self.__send('POST', '/elements', get_element_parameters(how))
        return map(lambda d: self.__element_factory(d), data['value'])
