# -*- coding: utf-8 -*-
import BigWorld

__all__ = ('logDebug', 'logInfo', 'logError', 'logWarning', 'logException', 'logTrace',)


class Logger(object):

    def logException(self, func):
        def exception(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except StandardError:
                self.logTrace(func)
        return exception

    @staticmethod
    def logTrace(exc=None):
        print('=============================')
        import traceback
        if exc is not None:
            logError('DriftkingsCore', str(exc))
            traceback.print_exc()
        else:
            traceback.print_stack()
        print('=============================')


logTrace = Logger().logTrace
logException = Logger().logException


def logError(modID, message, *args, **kwargs):
    BigWorld.logError(modID, str(message).format(*args, **kwargs), None)


def logInfo(modID, message):
    BigWorld.logInfo(modID, str(message), None)


def logDebug(modID, isDebug=False, message='', *args, **kwargs):
    if isDebug:
        BigWorld.logDebug(modID, str(message).format(*args, **kwargs), None)


def logWarning(modID, message):
    BigWorld.logWarning(modID, str(message), None)
