# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from infrae.testbrowser.selenium.browser import Browser
from infrae.testbrowser.tests import form


class FormTestCase(form.FormSupportTestCase):

    def Browser(self, app):
        return Browser(app)
