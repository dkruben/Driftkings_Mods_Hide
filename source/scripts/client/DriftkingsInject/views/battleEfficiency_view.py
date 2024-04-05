# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class BattleEfficiencyMeta(DriftkingsView):

    def __init__(self, ID):
        super(BattleEfficiencyMeta, self).__init__(ID)

    def as_battleEffS(self, text):
        return self.flashObject.as_battleEff(text) if self._isDAAPIInited() else None
