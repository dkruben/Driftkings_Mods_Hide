# -*- coding:utf-8 -*-
from PlayerEvents import g_playerEvents
from aih_constants import CTRL_MODE_NAME
from constants import ARENA_PERIOD
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.battle.shared.formatters import getHealthPercent, normalizeHealth
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control import avatar_getter
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
from gui.battle_control.controllers.prebattle_setups_ctrl import IPrebattleSetupsListener
from gui.shared.personality import ServicesLocator

from DriftkingsCore import DriftkingsConfigInterface, Analytics, percentToRgb, calculate_version
from DriftkingsInject import DriftkingsInjector, OwnHealthMeta, g_events

AS_SWF = 'OwnHealth.swf'
AS_BATTLE = 'OwnHealthView'
AS_INJECTOR = 'OwnHealthInjector'


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.5 (%(file_compile_date)s)'
        self.author = 'DriftKing\'s'
        self.data = {
            'enabled': True,
            'x': 0,
            'y': 400,
            'avgColor': {
                'brightness': 0.9,
                'saturation': 0.7
            },
            'colors': {
                'ally': '#60CB00',
                'bgColor': '#000000',
                'enemy': '#ED070A',
                'enemyColorBlind': "#6F6CD3"
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_x_text': 'Position X',
            'UI_setting_x_tooltip': '',
            'UI_setting_y_text': 'Position Y',
            'UI_setting_y_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createSlider('x', -2000, 2000, 1, '{{value}}%s' % ' X'),
                self.tb.createSlider('y', -2000, 2000, 1, '{{value}}%s' % ' Y')
            ],
            'column2': []
        }

    def onBattleLoaded(self):
        if not self.data['enabled']:
            return
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class OwnHealth(OwnHealthMeta, IPrebattleSetupsListener):
    def __init__(self):
        super(OwnHealth, self).__init__(config.ID)
        self.is_alive_mode = True
        self.is_battle_period = False
        self.maxHealth = 0
        self.template = '{} • {:.2%}'

    def getSettings(self):
        return config.data

    def updateVehicleParams(self, vehicle, *_):
        if self.maxHealth != vehicle.descriptor.maxHealth:
            self.maxHealth = vehicle.descriptor.maxHealth
            self._updateHealth(self.maxHealth)

    def _populate(self):
        super(OwnHealth, self)._populate()
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
        g_playerEvents.onArenaPeriodChange += self.onArenaPeriodChange
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleControlling += self.__onVehicleControlling
            ctrl.onVehicleStateUpdated += self.__onVehicleStateUpdated
        arena = self._arenaVisitor.getArenaSubscription()
        if arena is not None:
            self.is_battle_period = arena.period == ARENA_PERIOD.BATTLE
            self.is_alive_mode = self.getVehicleInfo().isAlive()
            self.as_BarVisibleS(self.is_battle_period and self.is_alive_mode)

    def onArenaPeriodChange(self, period, *_):
        self.is_battle_period = period == ARENA_PERIOD.BATTLE
        self.as_BarVisibleS(self.is_battle_period and self.is_alive_mode)

    def _dispose(self):
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        g_playerEvents.onArenaPeriodChange -= self.onArenaPeriodChange
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleControlling -= self.__onVehicleControlling
            ctrl.onVehicleStateUpdated -= self.__onVehicleStateUpdated
        super(OwnHealth, self)._dispose()

    def __onVehicleControlling(self, vehicle):
        if self.maxHealth != vehicle.maxHealth:
            self.maxHealth = vehicle.maxHealth
        self._updateHealth(vehicle.health)

    def __onVehicleStateUpdated(self, state, value):
        if state == VEHICLE_VIEW_STATE.HEALTH:
            self._updateHealth(value)

    def onCameraChanged(self, ctrlMode, *_, **__):
        self.is_alive_mode = ctrlMode not in {CTRL_MODE_NAME.KILL_CAM, CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM, CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION, CTRL_MODE_NAME.LOOK_AT_KILLER}
        self.as_BarVisibleS(self.is_battle_period and self.is_alive_mode)

    @staticmethod
    def getAVGColor(percent=1.0):
        return percentToRgb(percent, **config.data['avgColor'])

    def _updateHealth(self, health):
        if health > self.maxHealth:
            self.maxHealth = health
        if self.maxHealth <= 0:
            return
        percent = getHealthPercent(health, self.maxHealth)
        text = self.template.format(int(normalizeHealth(health)), percent)
        self.as_setOwnHealthS(percent, text, self.getAVGColor(percent))


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, OwnHealth, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
