# -*- coding: utf-8 -*-
__MOD_CORE__ = '3.1.0'  # Updated version number
__CORE_NAME__ = 'Driftkings_Core'
__MOD_DATE__ = '(%(file_compile_date)s)'

import time
import sys
import traceback

import ResMgr

from .config import *
from .utils import *

curCV = ResMgr.openSection('../paths.xml')['Paths'].values()[0].asString


def initializeCore():
    try:
        logStartupInfo()
        initializeSubsystems()
        return True
    except Exception as e:
        logError(__CORE_NAME__, 'Failed to initialize core: {0}', e)
        if getattr(sys, 'DEBUG', False):
            logError(__CORE_NAME__, 'Traceback: {0}', ''.join(traceback.format_exception(*sys.exc_info())))
        return False


def logStartupInfo():
    separator = '=' * 70
    logInfo(__CORE_NAME__, separator)
    logInfo(__CORE_NAME__, '================[Loading and Started]=================================')
    logInfo(__CORE_NAME__, '================[v.{} - {}]==============================', __MOD_CORE__, __MOD_DATE__)
    logInfo(__CORE_NAME__, separator)
    logInfo(__CORE_NAME__, 'Initialization time: {0}', time.strftime('%Y-%m-%d %H:%M:%S'))
    logInfo(__CORE_NAME__, 'Current client version: {0}', curCV)
    logInfo(__CORE_NAME__, separator)


def initializeSubsystems():
    logInfo(__CORE_NAME__, 'Initializing subsystems...')
    logInfo(__CORE_NAME__, 'Subsystems initialized successfully')


# Initialize the core when the module is imported
initializeCore()