# -*- coding: utf-8 -*-
from collections import defaultdict

from Event import SafeEvent
from constants import ARENA_GUI_TYPE
from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
from gui.battle_control.controllers.battle_field_ctrl import IBattleFieldListener
from gui.shared.personality import ServicesLocator
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import SimpleConfigInterface, Analytics, calculate_version
from DriftkingsInject import DriftkingsInjector, MainGunMeta, g_events

AS_SWF = 'MainGun.swf'
AS_BATTLE = 'MainGunView'
AS_INJECTOR = 'MainGunInjector'


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.5 (%(file_compile_date)s)'
        self.author = 'DriftKing\'s'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': False,
            'progressBar': False,
            'colors': {
                'ally': '#60CB00',
                'bgColor': '#000000'
            },
            'x': 600,
            'y': 30
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_progressBar_text': 'ProgressBar',
            'UI_setting_progressBar_tooltip': '',
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
                self.tb.createControl('progressBar'),
            ],
            'column2': [
                self.tb.createSlider('x', -2000, 2000, 1, '{{value}}%s' % ' X'),
                self.tb.createSlider('y', -2000, 2000, 1, '{{value}}%s' % ' Y')
            ]
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


class PlayersDamageController(object):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.onPlayerDamaged = SafeEvent()
        self.__damages = defaultdict(int)

    def start(self):
        self.__damages.clear()
        arena = self.sessionProvider.arenaVisitor.getArenaSubscription()
        if arena is not None:
            arena.onVehicleHealthChanged += self.onVehicleHealthChanged

    def stop(self):
        arena = self.sessionProvider.arenaVisitor.getArenaSubscription()
        if arena is not None:
            arena.onVehicleHealthChanged -= self.onVehicleHealthChanged

    def onVehicleHealthChanged(self, _, attackerID, damage):
        self.__damages[attackerID] += damage
        self.onPlayerDamaged(attackerID, self.__damages[attackerID])

    def getPlayerDamage(self, vehicleID):
        return self.__damages[vehicleID]


damage_controller = PlayersDamageController()


class MainGun(MainGunMeta, IBattleFieldListener):

    def __init__(self):
        super(MainGun, self).__init__(config.ID)
        self.settings = config.data
        self.gunScore = 0
        self.gunLeft = 0
        self._warning = False
        self.totalEnemiesHP = 0
        self.playerDamage = 0

    def isRandomBattle(self):
        return self.gui.isRandomBattle() or self.gui.isMapbox()

    def getSettings(self):
        if self.isRandomBattle():
            return self.settings

    def _populate(self):
        super(MainGun, self)._populate()
        damage_controller.onPlayerDamaged += self.onPlayerDamaged
        feedback = self.sessionProvider.shared.feedback
        if feedback is not None:
            feedback.onPlayerFeedbackReceived += self.onPlayerFeedbackReceived
        arena = self._arenaVisitor.getArenaSubscription()
        if arena is not None:
            arena.onVehicleKilled += self.onVehicleKilled

    def _dispose(self):
        damage_controller.onPlayerDamaged -= self.onPlayerDamaged
        feedback = self.sessionProvider.shared.feedback
        if feedback is not None:
            feedback.onPlayerFeedbackReceived -= self.onPlayerFeedbackReceived
        arena = self._arenaVisitor.getArenaSubscription()
        if arena is not None:
            arena.onVehicleKilled -= self.onVehicleKilled
        super(MainGun, self)._dispose()

    def onVehicleKilled(self, targetID, *_, **__):
        if self.playerVehicleID == targetID:
            self._warning = True
            self.updateMainGun()

    def updateTeamHealth(self, _, enemiesHP, __, totalEnemiesHP):
        if not self._warning and enemiesHP < self.gunLeft:
            self._warning = True
            self.updateMainGun()
        if self.totalEnemiesHP != totalEnemiesHP:
            self.totalEnemiesHP = totalEnemiesHP
            self.gunScore = max(1000, totalEnemiesHP / 5)
            self.updateMainGun()

    def updateMainGun(self):
        self.gunLeft = self.gunScore - self.playerDamage
        self.as_gunDataS(self.gunLeft, self.gunScore, self._warning)

    def onPlayerDamaged(self, attackerID, damage):
        if damage > self.gunScore and attackerID != self.playerVehicleID:
            self.gunScore = damage
            self.updateMainGun()

    def onPlayerFeedbackReceived(self, events):
        if self.isPlayerVehicle:
            for event in events:
                if event.getType() == FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY:
                    self.playerDamage += event.getExtra().getDamage()
                    self.updateMainGun()


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, MainGun, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
