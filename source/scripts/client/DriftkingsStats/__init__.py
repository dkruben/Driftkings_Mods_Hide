# -*- coding: utf-8 -*-
"""
DriftkingsStats - XVM statistics and vehicle information module
This module provides vehicle data and statistics calculations for World of Tanks.
It handles loading vehicle information, XVM statistics, and calculation of various
performance metrics like XTE, XTDB, and XVM scale ratings.
"""

__MOD_CORE__ = '1.6.0'
__CORE_NAME__ = 'DriftkingsStats'
__MOD_DATE__ = '(%(file_compile_date)s)'
__AUTHOR__ = 'DriftKings'
__VERSION__ = "{} {}".format(__MOD_CORE__, __MOD_DATE__)


__all__ = ('getVehicleInfoData', 'calculateXvmScale', 'calculateXTDB', 'calculateXTE', 'xvm_stat',)

from DriftkingsCore import logInfo, logError, logDebug

separator = '=' * 70

try:
    # Import module components
    from .vehinfo import getVehicleInfoData, calculateXvmScale, calculateXTDB, calculateXTE, scaleValuesInstance
    from .xvm_stats import xvm_stat
    # Log successful initialization
    logInfo(__CORE_NAME__, separator)
    logInfo(__CORE_NAME__, 'Version: {}, is loaded successfully', __MOD_CORE__)
    # Log additional module information
    logDebug(__CORE_NAME__, 'Vehicle data loaded: {} vehicles', len(scaleValuesInstance.getVehicleInfoDataArray()) if hasattr(scaleValuesInstance, 'getVehicleInfoDataArray') else 'unknown')
    logInfo(__CORE_NAME__, separator)
except ImportError as e:
    logInfo(__CORE_NAME__, separator)
    logError(__CORE_NAME__, 'Failed to import module: {}', str(e))
    logError(__CORE_NAME__, 'Module initialization failed')
    logInfo(__CORE_NAME__, separator)
    raise
except Exception as e:
    logInfo(__CORE_NAME__, separator)
    logError(__CORE_NAME__, 'Unexpected error during initialization: {}', str(e))
    import traceback
    logError(__CORE_NAME__, 'Traceback: {}', traceback.format_exc())
    logInfo(__CORE_NAME__, separator)
    raise
