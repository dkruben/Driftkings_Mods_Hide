# -*- coding: utf-8 -*-
__MOD_CORE__ = '1.0.0'
__CORE_NAME__ = 'Driftkings_Core'
__MOD_DATE__ = '(%(file_compile_date)s)'


from DriftkingsCore import logInfo
from meta import *
from views import *
from common import *


logInfo('%s inject flash, version %s, is loaded' % (__CORE_NAME__, __MOD_CORE__))
