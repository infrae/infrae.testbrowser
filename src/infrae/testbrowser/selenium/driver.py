# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import atexit
import json
import unittest
import urllib2

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
            if error.args[0].errno in [61, 111]:
                # Those are errno for connection refured.
                raise unittest.SkipTest("Selenium unavailable")
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

    def new_session(self, options, proxy=None):
        data = self.__connection.send(
            'POST', '/session', {'desiredCapabilities': options})
        return SeleniumSession(self.__connection, data, proxy)


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
            session = self.__sessions[key]
            # Clear existing cookies
            session.clear_cookies()
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
            except unittest.SkipTest:
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

    def __init__(self, connection, info, proxy=None):
        self.__connection = connection
        self.__path = ''.join(('/session/', info['sessionId']))
        self.__capabilities = info['value']
        self.__proxy = proxy
        self._send('POST', '/timeouts/async_script', {'ms': 120000})

    def _send(self, method, path, data=None):
        return self.__connection.send(
            method, ''.join((self.__path, path)), data)

    def _create_element(self, data):
        # Create a Selenium element out of the data.
        element = SeleniumElement(self.__connection, self.__path, data, self)
        if self.__proxy is not None:
            element = self.__proxy(self, element)
        return element

    @property
    def title(self):
        return self._send('GET', '/title')['value']

    @property
    def url(self):
        return self._send('GET', '/url')['value']

    @property
    def contents(self):
        return self._send('GET', '/source')['value']

    @property
    def cookies(self):
        return self._send('GET', '/cookie')['value']

    def refresh(self):
        self._send('POST', '/refresh')

    def back(self):
        self._send('POST', '/back')

    def forward(self):
        self._send('POST', '/forward')

    def open(self, url):
        self._send('POST', '/url', {'url': url})

    def close(self):
        self._send('DELETE', '/window')

    def execute(self, script, args):
        return self._send(
            'POST', '/execute_async',
            {'script': script, 'args': args})['value']

    def quit(self):
        self._send('DELETE', '')

    def get_active_element(self):
        data = self._send('POST', '/element/active')
        return self._create_element(data['value'])

    def get_element(self, **how):
        data = self._send('POST', '/element', get_element_parameters(how))
        return self._create_element(data['value'])

    def get_elements(self, **how):
        data = self._send('POST', '/elements', get_element_parameters(how))
        return map(lambda d: self._create_element(d), data['value'])

    def set_cookie(self, name, value):
        self._send(
            'POST', '/cookie',
            {'cookie': {'name': name, 'value': value,
                        'secure': False, 'path': '/'}})

    def clear_cookies(self):
        self._send('DELETE', '/cookie')


class SeleniumElement(object):

    def __init__(self, connection, path, info, session):
        self.__connection = connection
        self.__session = session
        self.__path = ''.join((path, '/element/', info['ELEMENT']))

    def _send(self, method, path, data=None):
        return self.__connection.send(
            method, ''.join((self.__path, path)), data)

    def _create_element(self, data):
        return self.__session._create_element(data)

    @property
    def tag(self):
        return self._send('GET', '/name')['value']

    @property
    def text(self):
        return self._send('GET', '/text')['value']

    @property
    def value(self):
        return self._send('GET', '/value')['value']

    @property
    def is_enabled(self):
        return self._send('GET', '/enabled')['value']

    @property
    def is_displayed(self):
        return self._send('GET', '/displayed')['value']

    @property
    def is_selected(self):
        return self._send('GET', '/selected')['value']

    def send_keys(self, keys):
        self._send('POST', '/value', {'value': list(keys)})

    def click(self):
        self._send('POST', '/click')

    def clear(self):
        self._send('POST', '/clear')

    def submit(self):
        self._send('POST', '/submit')

    def get_attribute(self, name):
        return self._send('GET', ''.join(('/attribute/', name)))['value']

    def get_css(self, name):
        return self._send('GET', ''.join(('/css/', name)))['value']

    def get_element(self, **how):
        data = self._send('POST', '/element', get_element_parameters(how))
        return self._create_element(data['value'])

    def get_elements(self, **how):
        data = self._send('POST', '/elements', get_element_parameters(how))
        return map(lambda d: self._create_element(d), data['value'])
