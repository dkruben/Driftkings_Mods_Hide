# -*- coding: utf-8 -*-
from collections import namedtuple

from AvatarInputHandler.control_modes import PostMortemControlMode
from AvatarInputHandler.DynamicCameras.ArcadeCamera import ArcadeCamera
from AvatarInputHandler.DynamicCameras.ArtyCamera import ArtyCamera
from AvatarInputHandler.DynamicCameras.StrategicCamera import StrategicCamera
from debug_utils import LOG_CURRENT_EXCEPTION

from DriftkingsCore import SimpleConfigInterface, Analytics, override, callback

MinMax = namedtuple('MinMax', ('min', 'max'))


class PostmortemDelay(object):

    def destroy(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def handleMouseEvent(self, *args):
        pass


class ConfigsInterface(SimpleConfigInterface):
    def __init__(self):
        self.camCache = {}
        super(ConfigsInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': False,
            'max': 160.0,
            'min': 4.0,
            'scrollSensitivity': 6.0,
            'startDeadDist': 20.0
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_min_text': 'Min Zoom Out',
            'UI_setting_min_tooltip': '',
            'UI_setting_max_text': 'Max Zoom Out',
            'UI_setting_max_tooltip': '',
            'UI_setting_scrollSensitivity_text': 'Scroll Sensitivity',
            'UI_setting_scrollSensitivity_tooltip': '',
            'UI_setting_startDeadDist_text': 'Start Dead Distance',
            'UI_setting_startDeadDist_tooltip': ''
        }
        super(ConfigsInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createSlider('scrollSensitivity', 1.0, 100.0, 1.0, '{{value}} %'),
                self.tb.createSlider('min', 10.0, 450.0, 10.0, '{{value}} X'),
            ],
            'column2': [
                self.tb.createSlider('startDeadDist', 10.0, 100.0, 10.0, '{{value}} %'),
                self.tb.createSlider('max', 10.0, 450.0, 10.0, '{{value}} X')
            ]
        }


config = ConfigsInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


# ARCADE
@override(ArcadeCamera, '_readConfigs')
@override(StrategicCamera, '_readConfigs')
@override(ArtyCamera, '_readConfigs')
def new__configs(func, self, dataSection):
    try:
        if config.camCache.setdefault(self.__class__.__name__, True):
            self._baseCfg.clear()
            self._userCfg.clear()
            self._cfg.clear()
            config.camCache[self.__class__.__name__] = False
    except Exception:
        LOG_CURRENT_EXCEPTION()
    finally:
        return func(self, dataSection)


@override(ArcadeCamera, '_readBaseCfg')
@override(ArcadeCamera, '_readUserCfg')
def new__readConfigs(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if config.data['enabled']:
        if func.__name__ == '_readBaseCfg':
            cfg = self._baseCfg
            cfg['distRange'] = MinMax(config.data['min'], config.data['max'])
            cfg['scrollSensitivity'] = config.data['scrollSensitivity']
        elif func.__name__ == '_readUserCfg':
            cfg = self._userCfg
            cfg['startDist'] = config.data['startDeadDist']


@override(ArcadeCamera, '_updateProperties')
def new__updateProperties(func, self, state=None):
    try:
        if config.data['enabled'] and state is not None:
            distRange = MinMax(config.data['min'], config.data['max'])
            scrollSensitivity = config.data['scrollSensitivity']
            state = state._replace(distRange=distRange, scrollSensitivity=scrollSensitivity)
    except Exception:
        LOG_CURRENT_EXCEPTION()
    finally:
        return func(self, state=state)


@override(StrategicCamera, '_readBaseCfg')
@override(ArtyCamera, '_readBaseCfg')
def new__readConfigs(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if config.data['enabled']:
        cfg = self._baseCfg
        cfg['distRange'] = (config.data['min'], config.data['max'])
        cfg['scrollSensitivity'] = config.data['scrollSensitivity']


@override(PostMortemControlMode, 'enable')
def new__enablePostMortem(func, self, **kwargs):
    if 'postmortemParams' in kwargs:
        kwargs['postmortemParams'] = (self.camera.angles, config.data['startDeadDist'])
    kwargs['camMatrix'] = self.camera.camera.matrix
    kwargs['transitionDuration'] = 1.0
    respawn = bool(kwargs.get('respawn', False))
    bPostmortemDelay = bool(kwargs.get('bPostmortemDelay', False))
    if not ((self._isPostmortemDelayEnabled() or respawn) and bPostmortemDelay):
        self._PostMortemControlMode__postmortemDelay = PostmortemDelay()

        def setDelayDisabled():
            self._PostMortemControlMode__postmortemDelay = None

        callback(1.0, setDelayDisabled)
    return func(self, **kwargs)
