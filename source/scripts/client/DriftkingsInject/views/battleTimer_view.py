# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class DateTimesMeta(DriftkingsView):

    def __init__(self, ID):
        super(DateTimesMeta, self).__init__(ID)

    def as_setDateTimeS(self, text):
        return self.flashObject.as_setDateTime(text) if self._isDAAPIInited() else None
