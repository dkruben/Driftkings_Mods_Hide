# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class SixthSenseMeta(DriftkingsView):
    def __init__(self, ID):
        super(SixthSenseMeta, self).__init__(ID)

    def as_showS(self, seconds):
        return self.flashObject.as_show(seconds) if self._isDAAPIInited() else None

    def as_hideS(self):
        return self.flashObject.as_hide() if self._isDAAPIInited() else None

    def getTimerString(self, timeLeft):
        return "NO TIMER STRING"

    def playSound(self):
        pass
