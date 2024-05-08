# -*- coding: utf-8 -*-
import Keys
from PlayerEvents import g_playerEvents
from frameworks.wulf import WindowLayer
from account_helpers.settings_core.settings_constants import GAME, GRAPHICS, ScorePanelStorageKeys as C_BAR
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.shared.gui_items.Vehicle import VEHICLE_CLASS_NAME
from gui.shared.personality import ServicesLocator
from gui.battle_control.controllers.battle_field_ctrl import IBattleFieldListener

from DriftkingsCore import SimpleConfigInterface, Analytics, loadJson
from DriftkingsInject import DriftkingsView, DriftkingsInjector, g_events

USE_PARS = True
AS_SWF = 'TeamsHealth.swf'
AS_BATTLE = 'TeamsHealthView'
AS_INJECTOR = 'TeamsHealthInjector'
TYPE_ICON = {
    VEHICLE_CLASS_NAME.HEAVY_TANK: 'H',
    VEHICLE_CLASS_NAME.MEDIUM_TANK: 'M',
    VEHICLE_CLASS_NAME.AT_SPG: 'J',
    VEHICLE_CLASS_NAME.SPG: 'S',
    VEHICLE_CLASS_NAME.LIGHT_TANK: 'L',
    'unknown': 'U'
}


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        self.markers = False
        self.vehicle_types = {
            'vehicleClassColors': {
                'AT-SPG': '#0094EC',
                'SPG': '#A90400',
                'heavyTank': '#F9B200',
                'lightTank': '#37BC00',
                'mediumTank': '#FDEF6C',
                'unknown': '#FFFFFF'
            },
            'vehicleClassIcon': {
                VEHICLE_CLASS_NAME.AT_SPG: '<font face=\'BattleObserver\' size=\'20\'>{}</font>'.format('J'),
                VEHICLE_CLASS_NAME.SPG: '<font face=\'BattleObserver\' size=\'20\'>{}</font>'.format('S'),
                VEHICLE_CLASS_NAME.HEAVY_TANK: '<font face=\'BattleObserver\' size=\'20\'>{}</font>'.format('H'),
                VEHICLE_CLASS_NAME.LIGHT_TANK: '<font face=\'BattleObserver\' size=\'20\'>{}</font>'.format('L'),
                VEHICLE_CLASS_NAME.MEDIUM_TANK: '<font face=\'BattleObserver\' size=\'20\'>{}</font>'.format('M'),
                'unknown': '<font face=\'BattleObserver\' size=\'20\'>{}</font>'.format('U')
            }
        }
        self.colors = {
            'colors': {
                'ally': '#60CB00',
                'bgColor': '#000000',
                'enemy': '#ED070A',
                'enemyColorBlind': '#6F6CD3'
            }
        }
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'DriftKing\'s'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': False,
            'showAliveCount': False,
            'style': 'league',
            'ally': 10,
            'enemy': 10
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_showAliveCount_text': 'Show Alive Count',
            'UI_setting_showAliveCount_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showAliveCount')
            ],
            'column2': []
        }

    def readCurrentSettings(self, quiet=True):
        self.vehicle_types = loadJson(self.ID, 'vehicle_types', self.vehicle_types, self.configPath)
        loadJson(self.ID, 'vehicle_types', self.vehicle_types, self.configPath, True, quiet=quiet)
        #
        self.colors = loadJson(self.ID, 'colors', self.colors, self.configPath)
        loadJson(self.ID, 'colors', self.colors, self.configPath, True, quiet=quiet)

    @staticmethod
    def onBattleLoaded():
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if not app:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class TeamHealthMeta(DriftkingsView):

    def __init__(self):
        super(TeamHealthMeta, self).__init__(config.ID)

    def as_updateHealthS(self, alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP):
        return self.flashObject.as_updateHealth(alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP) if self._isDAAPIInited() else None

    def as_updateCountersPositionS(self, ally, enemy):
        return self.flashObject.as_updateCountersPosition(ally, enemy) if self._isDAAPIInited() else None

    def as_updateScoreS(self, ally, enemy):
        return self.flashObject.as_updateScore(ally, enemy) if self._isDAAPIInited() else None

    def as_updateCorrelationBarS(self):
        return self.flashObject.as_updateCorrelationBar() if self._isDAAPIInited() else None


class TeamsHP(TeamHealthMeta, IBattleFieldListener):

    def __init__(self):
        super(TeamsHP, self).__init__()
        self.showAliveCount = False
        self.observers = set(vInfo.vehicleID for vInfo in self._arenaDP.getVehiclesInfoIterator() if vInfo.isObserver())

    def getColors(self):
        return config.colors

    def getSettings(self):
        return config.data

    @staticmethod
    def getVehicleClassColors():
        return config.vehicle_types['vehicleClassColors']

    @staticmethod
    def getVehicleClassColor(classTag):
        return config.vehicle_types['vehicleClassColors'][classTag or 'unknown']

    def _populate(self):
        super(TeamsHP, self)._populate()
        is_normal_mode = self.gui.isRandomBattle() or self.gui.isRankedBattle() or self.gui.isTrainingBattle()
        self.showAliveCount = config.data['showAliveCount'] and is_normal_mode
        self.settingsCore.onSettingsApplied += self.onSettingsApplied
        g_playerEvents.onAvatarReady += self.updateCounters

    def updateCounters(self):
        self.settingsCore.applySetting(C_BAR.SHOW_HP_BAR, False)
        self.settingsCore.applySetting(C_BAR.ENABLE_TIER_GROUPING, False)
        self.as_updateCountersPositionS(config.data['ally'], config.data['enemy'])

    def _dispose(self):
        self.settingsCore.onSettingsApplied -= self.onSettingsApplied
        g_playerEvents.onAvatarReady -= self.updateCounters
        super(TeamsHP, self)._dispose()

    def updateTeamHealth(self, alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP):
        self.as_updateHealthS(alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP)

    def updateDeadVehicles(self, aliveAllies, deadAllies, aliveEnemies, deadEnemies):
        if self.showAliveCount:
            self.as_updateScoreS(len(aliveAllies.difference(deadAllies)), len(aliveEnemies.difference(deadEnemies)))
        else:
            if self.observers:
                deadEnemies = deadEnemies.difference(self.observers)
                deadAllies = deadAllies.difference(self.observers)
            self.as_updateScoreS(len(deadEnemies), len(deadAllies))

    def onSettingsApplied(self, diff):
        if GRAPHICS.COLOR_BLIND in diff:
            self.as_colorBlindS(bool(diff[GRAPHICS.COLOR_BLIND]))
        if GAME.SHOW_VEHICLES_COUNTER in diff or C_BAR.SHOW_HP_BAR in diff or C_BAR.ENABLE_TIER_GROUPING in diff:
            self.updateCounters()


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, TeamsHP, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
