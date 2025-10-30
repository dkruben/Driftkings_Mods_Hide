# -*- coding: utf-8 -*-
from collections import namedtuple

from AvatarInputHandler.DynamicCameras.ArcadeCamera import ArcadeCamera
from AvatarInputHandler.DynamicCameras.ArtyCamera import ArtyCamera
from AvatarInputHandler.DynamicCameras.StrategicCamera import StrategicCamera
from AvatarInputHandler.control_modes import PostMortemControlMode
from debug_utils import LOG_CURRENT_EXCEPTION

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, calculate_version, logError


MinMax = namedtuple('MinMax', ('min', 'max'))


MIN_ZOOM = 4.0
MAX_ZOOM = 450.0
DEFAULT_MIN_ZOOM = 4.0
DEFAULT_MAX_ZOOM = 160.0
DEFAULT_SCROLL_SENSITIVITY = 6.0
DEFAULT_START_DEAD_DIST = 20.0


class ConfigsInterface(DriftkingsConfigInterface):

    def __init__(self):
        self.camCache = {}
        super(ConfigsInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.1.0 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.data = {
            'enabled': False,
            'max': DEFAULT_MAX_ZOOM,
            'min': DEFAULT_MIN_ZOOM,
            'scrollSensitivity': DEFAULT_SCROLL_SENSITIVITY,
            'startDeadDist': DEFAULT_START_DEAD_DIST
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_min_text': 'Min Zoom Out',
            'UI_setting_min_tooltip': 'Minimum camera distance from vehicle',
            'UI_setting_max_text': 'Max Zoom Out',
            'UI_setting_max_tooltip': 'Maximum camera distance from vehicle',
            'UI_setting_scrollSensitivity_text': 'Scroll Sensitivity',
            'UI_setting_scrollSensitivity_tooltip': 'Adjust mouse wheel zoom sensitivity',
            'UI_setting_startDeadDist_text': 'Start Dead Distance',
            'UI_setting_startDeadDist_tooltip': 'Initial camera distance in post-mortem mode'
        }
        super(ConfigsInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createSlider('scrollSensitivity', 1.0, 100.0, 1.0, '{{value}} %'),
                self.tb.createSlider('min', 1.0, MAX_ZOOM, 1.0, '{{value}} m'),
            ],
            'column2': [
                self.tb.createSlider('startDeadDist', 10.0, 100.0, 5.0, '{{value}} %'),
                self.tb.createSlider('max', 10.0, MAX_ZOOM, 10.0, '{{value}} m')
            ]
        }


config = ConfigsInterface()
analytics = Analytics(config.ID, config.version)


@override(ArcadeCamera, '_readConfigs')
@override(StrategicCamera, '_readConfigs')
@override(ArtyCamera, '_readConfigs')
def new_read_configs(func, self, dataSection):
    try:
        if config.camCache.setdefault(self.__class__.__name__, True):
            self._baseCfg.clear()
            self._userCfg.clear()
            self._cfg.clear()
            config.camCache[self.__class__.__name__] = False
    except Exception as e:
        logError(config.ID, "Error in new_read_configs: {}", e)
        LOG_CURRENT_EXCEPTION()
    finally:
        return func(self, dataSection)


@override(ArcadeCamera, '_readBaseCfg')
def new_read_arcade_base_cfg(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if config.data['enabled']:
        cfg = self._baseCfg
        cfg['distRange'] = MinMax(config.data['min'], config.data['max'])
        cfg['scrollSensitivity'] = config.data['scrollSensitivity']


@override(ArcadeCamera, '_readUserCfg')
def new_read_arcade_user_cfg(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if config.data['enabled']:
        cfg = self._userCfg
        cfg['startDist'] = config.data['startDeadDist']


@override(ArcadeCamera, '_updateProperties')
def new_update_arcade_properties(func, self, state=None):
    try:
        if config.data['enabled'] and state is not None:
            dist_range = MinMax(config.data['min'], config.data['max'])
            scroll_sensitivity = config.data['scrollSensitivity']
            state = state._replace(distRange=dist_range, scrollSensitivity=scroll_sensitivity)
    except Exception as e:
        logError(config.ID, 'Error in new_update_arcade_properties: {}', e)
        LOG_CURRENT_EXCEPTION()
    finally:
        return func(self, state=state)


@override(StrategicCamera, '_readBaseCfg')
def new_read_strategic_base_cfg(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if config.data['enabled']:
        cfg = self._baseCfg
        cfg['distRange'] = (config.data['min'], config.data['max'])
        cfg['scrollSensitivity'] = config.data['scrollSensitivity']


@override(ArtyCamera, '_readBaseCfg')
def new_read_arty_base_cfg(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if config.data['enabled']:
        cfg = self._baseCfg
        cfg['distRange'] = (config.data['min'], config.data['max'])
        cfg['scrollSensitivity'] = config.data['scrollSensitivity']


@override(PostMortemControlMode, 'enable')
def new_enable_post_mortem(func, self, **kwargs):
    if config.data['enabled']:
        if 'postmortemParams' in kwargs:
            kwargs['postmortemParams'] = (self.camera.angles, config.data['startDeadDist'])
            kwargs.setdefault('transitionDuration', 1.0)
    return func(self, **kwargs)
