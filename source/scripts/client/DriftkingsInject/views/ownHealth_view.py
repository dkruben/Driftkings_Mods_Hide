# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class OwnHealthMeta(DriftkingsView):

    def __init__(self, ID):
        super(OwnHealthMeta, self).__init__(ID)

    def as_setOwnHealthS(self, scale, text, color):
        return self.flashObject.as_setOwnHealth(scale, text, color) if self._isDAAPIInited() else None

    def as_BarVisibleS(self, visible):
        return self.flashObject.as_BarVisible(visible) if self._isDAAPIInited() else None
