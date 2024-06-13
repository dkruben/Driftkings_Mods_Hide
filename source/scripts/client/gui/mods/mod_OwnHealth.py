# -*- coding:utf-8 -*-
from PlayerEvents import g_playerEvents
from aih_constants import CTRL_MODE_NAME
from constants import ARENA_GUI_TYPE
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

from DriftkingsCore import SimpleConfigInterface, Analytics, percentToRGB, isDisabledByBattleType
from DriftkingsInject import DriftkingsInjector, OwnHealthMeta, g_events

AS_SWF = 'OwnHealth.swf'
AS_BATTLE = 'OwnHealthView'
AS_INJECTOR = 'OwnHealthInjector'


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'DriftKing\'s'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
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
            'UI_version': sum(int(x) * (10 ** i) for i, x in enumerate(reversed(self.version.split(' ')[0].split('.')))),
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

    def isEnabled(self):
        return self.data['enabled'] and not isDisabledByBattleType(include=(ARENA_GUI_TYPE.EPIC_RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING, ARENA_GUI_TYPE.EPIC_TRAINING))

    def onBattleLoaded(self):
        if not self.isEnabled:
            return
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if not app:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class OwnHealth(OwnHealthMeta, IPrebattleSetupsListener):
    def __init__(self):
        super(OwnHealth, self).__init__(config.ID)
        self.isAliveMode = True
        self.isBattlePeriod = False
        self.__maxHealth = 0
        self.__template = '{} • {:.2%}'

    def getSettings(self):
        return config.data

    def updateVehicleParams(self, vehicle, *_):
        if self.__maxHealth != vehicle.descriptor.maxHealth:
            self.__maxHealth = vehicle.descriptor.maxHealth
            self._updateHealth(self.__maxHealth)

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
            self.isBattlePeriod = arena.period == ARENA_PERIOD.BATTLE
            self.isAliveMode = self.getVehicleInfo().isAlive()
            self.as_BarVisibleS(self.isBattlePeriod and self.isAliveMode)

    def onArenaPeriodChange(self, period, *_):
        self.isBattlePeriod = period == ARENA_PERIOD.BATTLE
        self.as_BarVisibleS(self.isBattlePeriod and self.isAliveMode)

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
        if self.__maxHealth != vehicle.maxHealth:
            self.__maxHealth = vehicle.maxHealth
        self._updateHealth(vehicle.health)

    def __onVehicleStateUpdated(self, state, value):
        if state == VEHICLE_VIEW_STATE.HEALTH:
            self._updateHealth(value)

    def onCameraChanged(self, ctrlMode, *_, **__):
        self.isAliveMode = ctrlMode not in {CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM, CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION}
        self.as_BarVisibleS(self.isBattlePeriod and self.isAliveMode)

    @staticmethod
    def getAVGColor(percent=1.0):
        return percentToRGB(percent, **config.data['avgColor'])

    def _updateHealth(self, health):
        if health > self.__maxHealth:
            self.__maxHealth = health
        if self.__maxHealth <= 0:
            return
        percent = getHealthPercent(health, self.__maxHealth)
        text = self.__template.format(int(normalizeHealth(health)), percent)
        self.as_setOwnHealthS(percent, text, self.getAVGColor(percent))


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, OwnHealth, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
