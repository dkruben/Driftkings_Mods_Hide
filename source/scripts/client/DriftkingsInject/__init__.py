# -*- coding: utf-8 -*-
__MOD_CORE__ = '1.3.0'
__CORE_NAME__ = 'DriftkingsInject'
__MOD_DATE__ = '(%(file_compile_date)s)'
__AUTHOR__ = 'DriftKings'


from DriftkingsCore import logInfo, logError
separator = '=' * 70
try:
    from common import *
    from meta import DriftkingsView
    from utils import *
    from views import *
    logInfo(__CORE_NAME__, separator)
    logInfo(__CORE_NAME__, 'version {}, is loaded', __MOD_CORE__)
    logInfo(__CORE_NAME__, separator)
except ImportError as e:
    logInfo(__CORE_NAME__, separator)
    logError(__CORE_NAME__, "Failed to import required modules for {}: {}", __CORE_NAME__, e)
    logInfo(__CORE_NAME__, separator)
