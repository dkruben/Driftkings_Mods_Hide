# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class DispersionTimerMeta(DriftkingsView):
    def __init__(self, ID):
        super(DispersionTimerMeta, self).__init__(ID)

    def as_updateTimerTextS(self, text):
        return self.flashObject.as_upateTimerText(text) if self._isDAAPIInited() else None
