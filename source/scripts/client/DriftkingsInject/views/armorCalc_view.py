# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class ArmorCalculatorMeta(DriftkingsView):
    def __init__(self, ID):
        super(ArmorCalculatorMeta, self).__init__(ID)

    def as_armorCalculatorS(self, text):
        return self.flashObject.as_armorCalculator(text) if self._isDAAPIInited() else None
