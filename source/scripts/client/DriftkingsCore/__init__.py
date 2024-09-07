# -*- coding: utf-8 -*-
__MOD_CORE__ = '2.8.5'
__CORE_NAME__ = 'Driftkings_Core'
__MOD_DATE__ = '(%(file_compile_date)s)'

import ResMgr

from .config import *
from .utils import *

curCV = ResMgr.openSection('../paths.xml')['Paths'].values()[0].asString
logInfo(__CORE_NAME__, '===========[Loading and Started]================')
logInfo(__CORE_NAME__, '===========[v.{} - {}]============', __MOD_CORE__, __MOD_DATE__)
