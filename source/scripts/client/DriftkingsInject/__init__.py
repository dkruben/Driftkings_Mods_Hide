# -*- coding: utf-8 -*-
# Module metadata
__MOD_CORE__ = '1.2.5'
__CORE_NAME__ = 'DriftkingsInject'
__MOD_DATE__ = '(%(file_compile_date)s)'
__AUTHOR__ = 'DriftKings'

from DriftkingsCore import logInfo, logError
try:
    from common import *
    from meta import DriftkingsView
    from utils import *
    from views import *
    logInfo(__CORE_NAME__, 'version {}, is loaded', __MOD_CORE__)
except ImportError as e:
    logError(__CORE_NAME__, "Failed to import required modules for {}: {}", __CORE_NAME__, e)
except Exception as e:
    logError("Failed to initialize {}: {}", __CORE_NAME__, e)
