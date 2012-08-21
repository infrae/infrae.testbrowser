# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from infrae.testbrowser.form import parse_charset


class UtilsTestCase(unittest.TestCase):

    def test_parse_charset(self):
        self.assertEqual(
            parse_charset('utf-8'),
            ['utf-8'])
        self.assertEqual(
            parse_charset('utf-8,latin-1 ISO-8859-1 , invalid'),
            ['utf-8', 'iso8859-1'])
        self.assertEqual(
            parse_charset('invalid ,, invalid utf8'),
            ['utf-8'])

