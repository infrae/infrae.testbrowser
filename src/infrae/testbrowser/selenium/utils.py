# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import sysconfig

# You can add your platform here.
PLATFORM_MAPPING = {
    'win': 'WIN',
    'win32': 'WIN',
    'linux': 'LINUX',
    'freebsd': 'UNIX',
    'netbsd': 'UNIX',
    'openbsd': 'UNIX',
    'macosx': 'MAC'}


def get_current_platform():
    platform = sysconfig.get_platform()
    system = platform.split('-')[0]
    if system in PLATFORM_MAPPING:
        return PLATFORM_MAPPING[system]
    return 'ANY'

