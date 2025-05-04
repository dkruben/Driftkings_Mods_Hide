# -*- coding: utf-8 -*-
__MOD_CORE__ = '2.9.5'
__CORE_NAME__ = 'Driftkings_Core'
__MOD_DATE__ = '(%(file_compile_date)s)'

import time

import ResMgr

from .config import *
from .utils import *


curCV = ResMgr.openSection('../paths.xml')['Paths'].values()[0].asString


def initialize_core():
    try:
        log_startup_info()
        return True
    except Exception as e:
        logError(__CORE_NAME__, 'Failed to initialize core: {0}', e)
        return False

def log_startup_info():
    separator = '=' * 70
    logInfo(__CORE_NAME__, separator)
    logInfo(__CORE_NAME__, '================[Loading and Started]=================================')
    logInfo(__CORE_NAME__, '================[v.{} - {}]==============================', __MOD_CORE__, __MOD_DATE__)
    logInfo(__CORE_NAME__, separator)
    logInfo(__CORE_NAME__, 'Initialization time: {0}', time.strftime('%Y-%m-%d %H:%M:%S'))
    logInfo(__CORE_NAME__, separator)


initialize_core()
