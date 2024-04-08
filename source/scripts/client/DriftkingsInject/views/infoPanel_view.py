# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class InfoPanelMeta(DriftkingsView):

    def __init__(self, ID):
        super(InfoPanelMeta, self).__init__(ID)

    def as_showS(self, delay):
        return self.flashObject.as_show(delay) if self._isDAAPIInited() else None

    def as_hideS(self):
        return self.flashObject.as_hide() if self._isDAAPIInited() else None

    def as_infoPanelS(self, text):
        return self.flashObject.as_infoPanel(text) if self._isDAAPIInited() else None
