from .Simple import ConfigInterface, ConfBlockInterface

__all__ = ('DriftkingsConfigInterface', 'DriftkingsBlockInterface',)


class DriftkingsBase(object):
    def __init__(self):
        self.author = ''
        self.modsGroup = ''
        self.modSettingsID = ''

    def init(self):
        self.author = 'by Driftkings'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'


class DriftkingsConfigInterface(DriftkingsBase, ConfigInterface):
    def __init__(self):
        DriftkingsBase.__init__(self)
        ConfigInterface.__init__(self)

    def init(self):
        DriftkingsBase.init(self)
        ConfigInterface.init(self)

    def createTemplate(self):
        raise NotImplementedError


class DriftkingsBlockInterface(DriftkingsBase, ConfBlockInterface):
    def __init__(self):
        DriftkingsBase.__init__(self)
        ConfBlockInterface.__init__(self)

    def init(self):
        DriftkingsBase.init(self)
        ConfBlockInterface.init(self)

    def createTemplate(self, blockID=None):
        raise NotImplementedError('Template for block %s is not created' % blockID)
