from ..meta import DriftkingsView


class DistanceMeta(DriftkingsView):

    def __init__(self, ID):
        super(DistanceMeta, self).__init__(ID)

    def as_setDistanceS(self, text):
        return self.flashObject.as_setDistance(text) if self._isDAAPIInited() else None
