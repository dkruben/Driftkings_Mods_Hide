# -*- coding: utf-8 -*-
import BigWorld

from . import events
from .abstract import *
from .analytics import *
from .chat import *
from .colorRatting import *
from .game import *
from .iter import *
from .logger import *
from .monkeypatch import *
from .wgUtils import *


def __import_delayed():
    from . import delayed
    import DriftkingsCore
    import sys
    globals()['delayed'] = sys.modules['DriftkingsCore.delayed'] = DriftkingsCore.delayed = delayed


def initializeDelayedImports():
    # Called by the root package after its public functions are available.
    BigWorld.callback(0, __import_delayed)
