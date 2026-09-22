# -*- coding: utf-8 -*-
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
        self.version = '1.0.6 (%(file_compile_date)s)'
        self.author = 'DriftKing\'s'
        self.data = {
            'enabled': True,
            'x': 0,
            'y': -55,
            'alignX': 'center',
            'alignY': 'bottom',
            'avgColor': {
                'brightness': 0.9,
                'saturation': 0.7
            },
            'colors': {
                'ally': '#60CB00',
                'bgColor': '#000000',
                'enemy': '#ED070A',
                'enemyColorBlind': '#6F6CD3'
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_x_text': 'Position X',
            'UI_setting_x_tooltip': '',
            'UI_setting_y_text': 'Position Y',
            'UI_setting_y_tooltip': ''
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createSlider('x', -2000, 2000, 1, '{{value}}%s' % ' px'),
                self.tb.createSlider('y', -2000, 2000, 1, '{{value}}%s' % ' px')
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

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)
        _updateOwnHealthUI()


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)
g_own_health = None


class OwnHealth(OwnHealthMeta, IPrebattleSetupsListener):
    def __init__(self):
        super(OwnHealth, self).__init__(config.ID)
        self.is_alive_mode = True
        self.is_battle_period = False
        self.maxHealth = 0
        self.currentHealth = 0
        self.template = '%d - %.2f%%'

    def getSettings(self):
        return config.data

    def updateVehicleParams(self, vehicle, *_):
        if vehicle is None or getattr(vehicle, 'descriptor', None) is None:
            return
        if self.maxHealth != vehicle.descriptor.maxHealth:
            self.maxHealth = vehicle.descriptor.maxHealth
        self._updateHealth(self.maxHealth)

    def _populate(self):
        global g_own_health
        super(OwnHealth, self)._populate()
        g_own_health = self
        self._applySettings()
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
        g_playerEvents.onArenaPeriodChange += self.onArenaPeriodChange
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleControlling += self.__onVehicleControlling
            ctrl.onVehicleStateUpdated += self.__onVehicleStateUpdated
            vehicle = ctrl.getControllingVehicle()
            if vehicle is not None:
                self.__onVehicleControlling(vehicle)
        arena = self._arenaVisitor.getArenaSubscription()
        if arena is not None:
            self.is_battle_period = arena.period == ARENA_PERIOD.BATTLE
        vInfo = self.getVehicleInfo()
        if vInfo is not None:
            self.is_alive_mode = vInfo.isAlive()
        self.as_BarVisibleS(config.data['enabled'] and self.is_battle_period and self.is_alive_mode)

    def onArenaPeriodChange(self, period, *_):
        self.is_battle_period = period == ARENA_PERIOD.BATTLE
        self.as_BarVisibleS(config.data['enabled'] and self.is_battle_period and self.is_alive_mode)

    def _dispose(self):
        global g_own_health
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        g_playerEvents.onArenaPeriodChange -= self.onArenaPeriodChange
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleControlling -= self.__onVehicleControlling
            ctrl.onVehicleStateUpdated -= self.__onVehicleStateUpdated
        if g_own_health is self:
            g_own_health = None
        super(OwnHealth, self)._dispose()

    def _applySettings(self):
        self.as_updateSettingsS()
        self.as_BarVisibleS(config.data['enabled'] and self.is_battle_period and self.is_alive_mode)

    def __onVehicleControlling(self, vehicle):
        if vehicle is None:
            return
        if self.maxHealth != vehicle.maxHealth:
            self.maxHealth = vehicle.maxHealth
        self.is_alive_mode = vehicle.health > 0
        self.as_BarVisibleS(config.data['enabled'] and self.is_battle_period and self.is_alive_mode)
        self._updateHealth(vehicle.health)

    def __onVehicleStateUpdated(self, state, value):
        if state == VEHICLE_VIEW_STATE.HEALTH:
            self.is_alive_mode = value > 0
            self.as_BarVisibleS(config.data['enabled'] and self.is_battle_period and self.is_alive_mode)
            self._updateHealth(value)

    def onCameraChanged(self, ctrlMode, *_, **__):
        self.is_alive_mode = ctrlMode not in {
            CTRL_MODE_NAME.KILL_CAM,
            CTRL_MODE_NAME.POSTMORTEM,
            CTRL_MODE_NAME.DEATH_FREE_CAM,
            CTRL_MODE_NAME.RESPAWN_DEATH,
            CTRL_MODE_NAME.VEHICLES_SELECTION,
            CTRL_MODE_NAME.LOOK_AT_KILLER
        }
        self.as_BarVisibleS(config.data['enabled'] and self.is_battle_period and self.is_alive_mode)

    @staticmethod
    def getAVGColor(percent=1.0):
        return percentToRgb(percent, **config.data['avgColor'])

    def _updateHealth(self, health):
        if not isinstance(health, (int, long, float)) or health < 0:
            return
        self.currentHealth = health
        if health > self.maxHealth:
            self.maxHealth = health
        if self.maxHealth <= 0:
            return
        percent = getHealthPercent(health, self.maxHealth)
        text = self.template % (int(normalizeHealth(health)), percent * 100.0)
        self.as_setOwnHealthS(percent, text, self.getAVGColor(percent))


def _updateOwnHealthUI():
    if g_own_health is None:
        return
    g_own_health._applySettings()
    if g_own_health.currentHealth > 0:
        g_own_health._updateHealth(g_own_health.currentHealth)


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, OwnHealth, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
