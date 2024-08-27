# -*- coding: utf-8 -*-
from ..meta import DriftkingsView


class FlightTimeMeta(DriftkingsView):
    def __init__(self, ID):
        super(FlightTimeMeta, self).__init__(ID)

    def as_flightTimeS(self, text):
        return self.flashObject.as_flightTime(text) if self._isDAAPIInited() else None
