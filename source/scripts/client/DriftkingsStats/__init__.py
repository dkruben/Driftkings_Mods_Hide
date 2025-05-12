# -*- coding: utf-8 -*-
__MOD_CORE__ = '1.6.0'
__CORE_NAME__ = 'DriftkingsStats'
__MOD_DATE__ = '(%(file_compile_date)s)'
__AUTHOR__ = 'DriftKings'


__all__ = ('getVehicleInfoData', 'calculateXvmScale', 'calculateXTDB', 'calculateXTE', 'xvm_stat',)


from DriftkingsCore import logInfo, logError
separator = '=' * 70
try:
    from vehinfo import *
    from xvm_stats import *
    logInfo(__CORE_NAME__, separator)
    logInfo(__CORE_NAME__, 'version: {}, is loaded', __MOD_CORE__)
    logInfo(__CORE_NAME__, separator)
except ImportError as e:
    logInfo(__CORE_NAME__, separator)
    logError(__CORE_NAME__, 'Failed to import module: {}', str(e))
    logInfo(__CORE_NAME__, separator)
