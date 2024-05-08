# -*- coding: utf-8 -*-
import traceback

import BigWorld

__all__ = ('logDebug', 'logInfo', 'logError', 'logWarning', 'logException', 'logTrace',)


def logError(modID, message, *args, **kwargs):
    BigWorld.logError(modID, str(message).format(*args, **kwargs), None)


def logInfo(modID, message):
    BigWorld.logInfo(modID, str(message), None)


def logDebug(modID, isDebug=False, message='', *args, **kwargs):
    if isDebug:
        BigWorld.logDebug(modID, str(message).format(*args, **kwargs), None)


def logWarning(modID, message):
    BigWorld.logWarning(modID, str(message), None)


def logTrace(exc=None):
    print '=' * 45
    if exc is not None:
        logError('DriftkingsCore', exc)
        traceback.print_exc()
    else:
        traceback.print_stack()
    print '=' * 45


def logException(func):
    def exception(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            logTrace(func)
    return exception
