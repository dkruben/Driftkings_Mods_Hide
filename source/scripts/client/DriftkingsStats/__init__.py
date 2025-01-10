# -*- coding: utf-8 -*-
__MOD_CORE__ = '1.5.0'
__CORE_NAME__ = 'DriftkingsStats'
__MOD_DATE__ = '(%(file_compile_date)s)'

from DriftkingsCore import logInfo
from vehinfo import *
from xvm_stats import *

__all__ = ('getVehicleInfoData', 'calculateXvmScale', 'calculateXTDB', 'calculateXTE', 'xvm_stat',)

logInfo(__CORE_NAME__, 'version: {}, is loaded', __MOD_CORE__)
