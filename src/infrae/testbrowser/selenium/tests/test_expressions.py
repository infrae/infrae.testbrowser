# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from infrae.testbrowser.tests import app, expressions
from infrae.testbrowser.selenium.browser import Browser


class ExpressionsTestCase(expressions.ExpressionsTestCase):

    def Browser(self, app):
        return Browser(app)
