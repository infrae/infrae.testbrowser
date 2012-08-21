# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt


class SeleniumError(AssertionError):
    """Selenium error.
    """

    def __str__(self):
        message = self.__doc__
        if self.args:
            info = self.args[0]
            if 'class' in info:
                message += 'Selenium error: ' + info['class'] + ':\n'
            if 'message' in info:
                message += info['message']
        return message


class SelectionConnectionError(SeleniumError):
    """Could not connect to remote Selenium
    """

class SeleniumTimeout(SeleniumError):
    """Operation timeout
    """

class SeleniumFrameNotFound(SeleniumError):
    """Requested frame was not found
    """

class SeleniumUnknownCommand(SeleniumError):
    """Unknown Selenium command
    """

class SeleniumElementNotFound(SeleniumError):
    """Requested element was not found
    """

class SeleniumStaleElementError(SeleniumError):
    """Requested element no longer exists
    """

class SeleniumElementNotVisible(SeleniumError):
    """Requested element is not visible
    """

class SeleniumElementIsNotSelectable(SeleniumError):
    """Requested element is not selectable
    """

class SeleniumInvalidElementState(SeleniumError):
    """Invalid element state
    """

class SeleniumUnknownError(SeleniumError):
    """Unknown Selenium error
    """

class SeleniumJavascriptError(SeleniumError):
    """Javascript error
    """

class SeleniumXPATHLookupError(SeleniumError):
    """XPATH lookup error
    """

class SeleniumWindowNotFound(SeleniumError):
    """Requested window doesn't exist
    """

class SeleniumInvalidCookieDomain(SeleniumError):
    """Invalid cookie domain
    """

class SeleniumUnableToSetCookie(SeleniumError):
    """Unable to set cookie
    """


CODE_TO_EXCEPTION = {
    1: SeleniumUnknownError,
    7: SeleniumElementNotFound,
    8: SeleniumFrameNotFound,
    9: SeleniumUnknownCommand,
    10: SeleniumStaleElementError,
    11: SeleniumElementNotVisible,
    12: SeleniumInvalidElementState,
    13: SeleniumUnknownCommand,
    15: SeleniumElementIsNotSelectable,
    17: SeleniumJavascriptError,
    19: SeleniumXPATHLookupError,
    23: SeleniumWindowNotFound,
    24: SeleniumInvalidCookieDomain,
    25: SeleniumUnableToSetCookie,
    28: SeleniumTimeout}
