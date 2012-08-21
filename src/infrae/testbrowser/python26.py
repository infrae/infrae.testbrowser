# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt
"""python 2.6 compatibility"""

import collections
if not hasattr(collections, 'OrderedDict'):
    try:
        import ordereddict
    except ImportError:
        raise Exception(
                    'If you are using Python 2.6, please install ordereddict')
    # shamelessly patch
    collections.OrderedDict = ordereddict.OrderedDict


import unittest
if not hasattr(unittest, 'SkipTest'):
    class SkipTest(Exception):
        pass

    unittest.SkipTest = SkipTest


# sysconfig.get_platform
try:
    import sysconfig
except ImportError:
    # python 2.6 compat
    import os
    import sys
    import imp

    def get_platform():
        """get_platform poor replacement"""
        if os.name == 'posix' and hasattr(os, 'uname'):
            return os.uname()[0].replace('/', '-')
        else:
            return sys.platform

    sysconfig = imp.new_module('sysconfig')
    sysconfig.get_platform = get_platform
    sys.modules['sysconfig'] = sysconfig
