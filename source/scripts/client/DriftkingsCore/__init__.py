# -*- coding: utf-8 -*-
__MOD_CORE__ = '2.7.0'
__CORE_NAME__ = 'Driftkings_Core'
__MOD_DATE__ = '(%(file_compile_date)s)'

import ResMgr

from .config import *
from .utils import *

curCV = ResMgr.openSection('../paths.xml')['Paths'].values()[0].asString
print('=====[%s]: Load and Started=====' % __CORE_NAME__)
print('===========[v.%s %s]============' % (__MOD_CORE__, __MOD_DATE__))
