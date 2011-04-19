# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import simplejson
import atexit
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
        data = simplejson.dumps(parameters) if parameters else None
        request = utils.HTTPRequest(url=url, data=data, method=method)
        request.add_header('Accept', 'application/json')
        print method, url, data
        try:
            return self.validate(self.receive(self.open(request)))
        except urllib2.URLError:
            raise AssertionError(u"Could not connect to remote Selenium")

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
                data = simplejson.loads(body)
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

    def new_session(self, **options):
        data = self.__connection.send(
            'POST', '/session', {'desiredCapabilities': options})
        return SeleniumSession(self.__connection, data)


class Seleniums(object):
    """Manage all active Seleniums instances.
    """

    def __init__(self):
        self.__sessions = {}

    def get(self, options):
        """Return a Selenium driver associated to this set of options.
        """
        key = (options.selenium_host,
               options.selenium_port,
               options.selenium_platform,
               options.browser)
        if key in self.__sessions:
            return self.__sessions[key]

        session = Selenium(
            options.selenium_host,
            options.selenium_port).new_session(
            **{'browserName': options.browser,
               'javascriptEnabled': options.enable_javascript,
               'platform': options.selenium_platform})
        self.__sessions[key] = session
        return session

    def all(self):
        return self.__sessions.itervalues()

    def clear(self):
        for session in self.all():
            session.quit()
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

    def __init__(self, connection, info):
        self.__connection = connection
        self.__path = ''.join(('/session/', info['sessionId']))
        self.__capabilities = info['value']

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

    def quit(self):
        self.__send('DELETE', '')

    def __element_factory(self, data):
        return SeleniumElement(self.__connection, self.__path, data)

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
        self.__send('POST', '/value', {'value': keys})

    def select(self):
        self.__send('POST', '/selected')

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
