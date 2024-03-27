# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class MainGunMeta(DriftkingsView):

    def __init__(self, ID):
        super(MainGunMeta, self).__init__(ID)

    def as_gunDataS(self, value, max_value, warning):
        return self.flashObject.as_gunData(value, max_value, warning) if self._isDAAPIInited() else None
