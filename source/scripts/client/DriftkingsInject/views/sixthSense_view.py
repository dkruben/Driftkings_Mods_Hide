# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class SixthSenseMeta(DriftkingsView):
    def __init__(self, ID):
        super(SixthSenseMeta, self).__init__(ID)

    def as_showS(self):
        return self.flashObject.as_show() if self._isDAAPIInited() else None

    def as_hideS(self):
        return self.flashObject.as_hide() if self._isDAAPIInited() else None

    def as_updateTimerS(self, text):
        return self.flashObject.as_updateTimer(text) if self._isDAAPIInited() else None
