# -*- coding: utf-8 -*-
__MOD_CORE__ = '1.5.5'
__CORE_NAME__ = 'DriftkingsStats'
__MOD_DATE__ = '(%(file_compile_date)s)'
__AUTHOR__ = 'Driftkings'

from DriftkingsCore import logInfo, logError
try:
    from vehinfo import *
    from xvm_stats import *
except ImportError as e:
    logError(__CORE_NAME__, 'Failed to import module: {}', str(e))

__all__ = ('getVehicleInfoData', 'calculateXvmScale', 'calculateXTDB', 'calculateXTE', 'xvm_stat',)

logInfo(__CORE_NAME__, 'version: {}, is loaded', __MOD_CORE__)
