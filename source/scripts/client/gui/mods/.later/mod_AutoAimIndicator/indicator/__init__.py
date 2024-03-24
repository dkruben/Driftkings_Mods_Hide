# -*- coding: utf-8 -*-
import functools

import Event

from .model import Model

__all__ = 'IndicatorsCtrl'


class IndicatorsCtrl(object):

    def __init__(self, controller, settingsGetter):
        super(IndicatorsCtrl, self).__init__()
        self.controller = controller
        self.onStart = Event.Event()
        self.onStop = Event.Event()
        self.onCreate = Event.Event()
        self.onDestroy = Event.Event()
        self.onShow = Event.Event()
        self.onHide = Event.Event()
        self.model = Model(self, functools.partial(settingsGetter, 'isModel'))

    def __getattribute__(self, name):
        try:
            return super(IndicatorsCtrl, self).__getattribute__(name)
        except AttributeError:
            return getattr(self.controller, name)
