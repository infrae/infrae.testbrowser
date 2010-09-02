# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.interface import Interface, Attribute


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
