# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class TotalLogMeta(DriftkingsView):

    def __init__(self, ID):
        super(TotalLogMeta, self).__init__(ID)

    def as_createTopLogS(self, settings):
        return self.flashObject.as_createTopLog(settings) if self._isDAAPIInited() else None

    def as_updateTopLogS(self, text):
        return self.flashObject.as_updateTopLog(text) if self._isDAAPIInited() else None
