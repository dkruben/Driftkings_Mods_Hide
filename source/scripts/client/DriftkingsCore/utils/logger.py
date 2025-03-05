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


def logException(func):
    def exception(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            if SHOW_DEBUG:
                msg = '[DEBUG][DriftkingsCore] %s.%s(' % (func.__module__, func.__name__)
                formatted_args = []
                for arg in args:
                    if hasattr(arg, '__module__'):
                        formatted_args.append(arg.__module__)
                    else:
                        formatted_args.append(str(arg))
                msg += ', '.join(formatted_args)
                if kwargs:
                    if args:
                        msg += ', '
                    msg += ', '.join('%s=%s' % (k, v) for k, v in kwargs.items())
                msg += ')\n[START]' + '=' * 22 + '\n'
                msg += ''.join(traceback.format_exception(*sys.exc_info()))
                msg += '[END]' + '=' * 22
                logError('DriftkingsCore', msg)
                BigWorld.log_mes = func
            return None
    return exception