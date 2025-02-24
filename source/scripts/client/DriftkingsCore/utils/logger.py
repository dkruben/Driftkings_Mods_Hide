# -*- coding: utf-8 -*-
import traceback
import sys

import BigWorld

__all__ = ('logDebug', 'logInfo', 'logError', 'logWarning', 'logException')  # , 'logTrace',)

SHOW_DEBUG = False

def _formatMessage(message, *args, **kwargs):
    message = unicode(str(message), 'utf-8', 'ignore')
    if args or kwargs:
        return message.format(*args, **kwargs)
    return message


def logError(modID, message, *args, **kwargs):
    BigWorld.logError(modID, _formatMessage(message, *args, **kwargs), None)


def logInfo(modID, message, *args, **kwargs):
    BigWorld.logInfo(modID, _formatMessage(message, *args, **kwargs), None)


def logDebug(modID, isDebug=False, message='', *args, **kwargs):
    if isDebug:
        BigWorld.logDebug(modID, _formatMessage(message, *args, **kwargs), None)


def logWarning(modID, message, *args, **kwargs):
    BigWorld.logWarning(modID, _formatMessage(message, *args, **kwargs), None)


# def logTrace(exc=None):
#    print '=' * 45
#    if exc is not None:
#        logError('DriftkingsCore:', str(exc))
#        traceback.print_exc()
#    else:
#        traceback.print_stack()
#    print '=' * 45


# def logException(func):
#    def exception(*args, **kwargs):
#        try:
#            return func(*args, **kwargs)
#        except Exception as err:
#            logTrace(err)
#    return exception

def logException(func):
    def exception(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            if SHOW_DEBUG:
                msg = 'DEBUG[DriftkingsCore]:\n%s.%s(' % (func.__module__, func.__name__)
                length = len(args)
                for text in args:
                    length -= 1
                    if hasattr(text, '__module__'):
                        text = '%s' % text.__module__
                    if length:
                        msg += '%s, ' % text
                    else:
                        msg += '%s' % text
                msg += ')\n[START:]----------------\n'
                msg += ''.join(traceback.format_exception(*sys.exc_info()))
                msg += '[END:]------------------'
                print msg
                BigWorld.log_mes = func
            return None
    return exception
