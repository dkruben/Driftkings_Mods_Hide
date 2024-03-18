# -*- coding: utf-8 -*-
import functools
import sys
import traceback

__all__ = ('log', 'logDebug', 'logInfo', 'logNote', 'logError', 'logWarning', 'logException', 'logTrace',)


class Logger(object):
    def __init__(self):
        self.log = functools.partial(self.log, '===============Driftkings_mods==============='.upper())
        self.logInfo = functools.partial(self.log, '[INFO]:')
        self.logNote = functools.partial(self.log, '[NOTE]:')
        self.logError = functools.partial(self.log, '[ERROR]:')
        self.logWarning = functools.partial(self.log, '[WARNING]:')

    @staticmethod
    def log(project, *args, **kwargs):
        kwargs = repr(kwargs) if kwargs else ''
        args = ' '.join([unicode(s) for s in args])
        print '%s' % project
        print '%s %s' % (args, kwargs)
        print '=' * 45

    def logDebug(self, isDebug=False, message=str(), *args, **kwargs):
        if isDebug:
            self.log('[DEBUG]:', message.format(*args, **kwargs))

    def logException(self, func):
        def exception(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except StandardError:
                self.logTrace(func)
        return exception

    def logTrace(self, func=None):
        self.log('=' * 79)
        self.log('=' * 20 + ' [Driftkings] - detected error started '.upper() + '=' * 20)
        if func:
            _logging = []
            e_type, value, tb = sys.exc_info()
            co_filename = func.func_code.co_filename.replace('\\', '/')
            filename = co_filename.split('/')[co_filename.count('/')].replace('.pyc', '').replace('.py', '') if co_filename.count('/') else co_filename
            for scriptName in sys.modules.keys():
                if filename in scriptName:
                    scriptDir = str(sys.modules[scriptName]).split('from')[1].replace(' ', '').replace('>', '').replace("'", '')
                    for values in traceback.format_exception(e_type, value, tb):
                        if func.func_code.co_filename in values:
                            values = '  File \'%s\', line %d, in %s\n' % (scriptDir, tb.tb_lineno, func.func_code.co_name)
                        _logging.append(values)
                    count = len(_logging) - 1
                    _logging[count] = _logging[count].replace('\n', '')
                    self.log(''.join(_logging))
        else:
            traceback.print_stack()
        self.log('=' * 20 + ' [Driftkings] - detected error is stop '.upper() + '=' * 20)
        self.log('=' * 79)


log = Logger().log
logInfo = Logger().logInfo
logNote = Logger().logNote
logError = Logger().logError
logWarning = Logger().logWarning
logTrace = Logger().logTrace
logDebug = Logger().logDebug
logException = Logger().logException
