# -*- coding: utf-8 -*-
import BigWorld

from . import events
from .abstract import *
from .analytics import *
from .chat import *
from .game import *
from .iter import *
from .logger import *
from .monkeypatch import *
from .wgUtils import *
from .colorRatting import *


def __import_delayed():
    from . import delayed
    import DriftkingsCore
    import sys
    globals()['delayed'] = sys.modules['DriftkingsCore.delayed'] = DriftkingsCore.delayed = delayed


BigWorld.callback(0, __import_delayed)
del __import_delayed
