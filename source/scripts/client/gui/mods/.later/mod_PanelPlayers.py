from collections import namedtuple, defaultdict

from Event import SafeEvent
from Keys import KEY_LALT, KEY_LCONTROL, KEY_LSHIFT, KEY_RALT, KEY_RCONTROL, KEY_RSHIFT
from PlayerEvents import g_playerEvents
from account_helpers.settings_core.settings_constants import GRAPHICS
from debug_utils import LOG_CURRENT_EXCEPTION
from frameworks.wulf import WindowLayer
from gui import InputHandler
from gui.Scaleform.daapi.view.battle.shared.formatters import normalizeHealthPercent
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.controllers.battle_field_ctrl import IBattleFieldListener
from gui.shared.personality import ServicesLocator
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import SimpleConfigInterface, Analytics, logDebug, DriftkingsView, DriftkingsInjector, g_events

KeysData = namedtuple('KeysData', ('keys', 'keyFunction'))
KEY_ALIAS_CONTROL = (KEY_LCONTROL, KEY_RCONTROL)
KEY_ALIAS_ALT = (KEY_LALT, KEY_RALT)
KEY_ALIAS_SHIFT = (KEY_LSHIFT, KEY_RSHIFT)

AS_SWF = 'PlayerPanel.swf'
AS_BATTLE = 'PlayerPanelView'
AS_INJECTOR = 'PlayerPanelInjector'


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
            'usePars': True,
            'panelsSpottedSix': True,
            'playersBarsClassColor': True,
            'playersBarsEnabled': True,
            'playersBarsHotkey': [[56]],
            'playersBarsHpText': '%(health)s',
            'playersBarsOnKeyPressed': True,
            'playersBarsSettings': {
                'playersBarsBar': {
                    'height': 20,
                    'outline': True,
                    'width': 70,
                    'x': 10,
                    'y': 2
                },
                "playersBarsText": {
                    'align': 'center',
                    'x': 35,
                    'y': -2
                }
            },
            'playersDamagesEnabled': True,
            'playersDamagesHotkey': [[56]],
            'playersDamagesSettings': {
                'align': 'right',
                'x': -40,
                'y': 0
            },
            'playersDamagesText': '<font color=\'#FFFF00\'>%(damage)s</font>',
            'colors': {
                'ally': '#60CB00',
                'enemy': '#ED070A',
                'enemyColorBlind': '#6F6CD3'
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            # 'UI_setting_progressBar_text': 'ProgressBar',
            # 'UI_setting_progressBar_tooltip': '',
            # 'UI_setting_x_text': 'Position X',
            # 'UI_setting_x_tooltip': '',
            # 'UI_setting_y_text': 'Position Y',
            # 'UI_setting_y_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                # self.tb.createControl('progressBar'),
            ],
            'column2': [
                # self.tb.createSlider('x', -2000, 2000, 1, '{{value}}%s' % ' X'),
                # self.tb.createSlider('y', -2000, 2000, 1, '{{value}}%s' % ' Y')
            ]
        }

    @staticmethod
    def onBattleLoaded():
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if not app:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class KeysListener(object):

    def __init__(self):
        self.keysMap = set()
        self.pressedKeys = set()
        self.usableKeys = set()
        g_playerEvents.onAvatarReady += self.onEnterBattlePage
        g_playerEvents.onAvatarBecomeNonPlayer += self.onExitBattlePage

    def registerComponent(self, keyFunction, keyList=None):
        self.keysMap.add(KeysData(self.normalizeKey(keyList) if keyList else KEY_ALIAS_ALT, keyFunction))

    def clear(self):
        self.keysMap.clear()
        self.usableKeys.clear()
        self.pressedKeys.clear()

    def onEnterBattlePage(self):
        InputHandler.g_instance.onKeyDown += self.onKeyDown
        InputHandler.g_instance.onKeyUp += self.onKeyUp

    def onExitBattlePage(self):
        InputHandler.g_instance.onKeyDown -= self.onKeyDown
        InputHandler.g_instance.onKeyUp -= self.onKeyUp
        self.clear()

    def onKeyUp(self, event):
        if event.key not in self.pressedKeys:
            return
        for keysData in self.keysMap:
            if event.key in keysData.keys:
                try:
                    keysData.keyFunction(False)
                except Exception:
                    LOG_CURRENT_EXCEPTION(config.ID)
        self.pressedKeys.discard(event.key)

    def onKeyDown(self, event):
        if event.key not in self.usableKeys or event.key in self.pressedKeys:
            return
        for keysData in self.keysMap:
            if event.key in keysData.keys:
                try:
                    keysData.keyFunction(True)
                except Exception:
                    LOG_CURRENT_EXCEPTION(config.ID)
        self.pressedKeys.add(event.key)

    def normalizeKey(self, keyList):
        keys = set()
        for key in keyList:
            if isinstance(key, (list, set, tuple)):
                keys.update(key)
            else:
                keys.add(key)
        if config.data['usePars']:
            for key in tuple(keys):
                if key in KEY_ALIAS_CONTROL:
                    keys.update(KEY_ALIAS_CONTROL)
                elif key in KEY_ALIAS_ALT:
                    keys.update(KEY_ALIAS_ALT)
                elif key in KEY_ALIAS_SHIFT:
                    keys.update(KEY_ALIAS_SHIFT)
        self.usableKeys.update(keys)
        return tuple(keys)


g_keysListener = KeysListener()


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


class PlayersPanelsMeta(DriftkingsView):

    def __init__(self):
        super(PlayersPanelsMeta, self).__init__(config.ID)

    def onAddedToStorage(self, vehicleID, isEnemy):
        pass

    def as_AddVehIdToListS(self, vehID, isEnemy):
        return self.flashObject.as_AddVehIdToList(vehID, isEnemy) if self._isDAAPIInited() else None

    def as_addHealthBarS(self, vehID, barColor, settings, visible):
        return self.flashObject.as_addHealthBar(vehID, barColor, settings, visible) if self._isDAAPIInited() else None

    def as_addDamageS(self, vehID, params):
        return self.flashObject.as_addDamage(vehID, params) if self._isDAAPIInited() else None

    def as_updateDamageS(self, vehicleID, text):
        return self.flashObject.as_updateDamage(vehicleID, text) if self._isDAAPIInited() else None

    def as_setVehicleDeadS(self, vehicleID):
        return self.flashObject.as_setVehicleDead(vehicleID) if self._isDAAPIInited() else None

    def as_updateHealthBarS(self, vehicleID, percent, textField):
        return self.flashObject.as_updateHealthBar(vehicleID, percent, textField) if self._isDAAPIInited() else None

    def as_setHealthBarsVisibleS(self, visible):
        return self.flashObject.as_setHealthBarsVisible(visible) if self._isDAAPIInited() else None

    def as_setPlayersDamageVisibleS(self, visible):
        return self.flashObject.as_setPlayersDamageVisible(visible) if self._isDAAPIInited() else None

    def as_colorBlindBarsS(self, color):
        return self.flashObject.as_colorBlindBars(color) if self._isDAAPIInited() else None

    def as_setSpottedPositionS(self, vehicleID):
        return self.flashObject.as_setSpottedPosition(vehicleID) if self._isDAAPIInited() else None


class PlayersPanels(PlayersPanelsMeta, IBattleFieldListener):

    def __init__(self):
        super(PlayersPanels, self).__init__()
        self.hpBarsEnable = False
        self.damagesEnable = False

    def getSettings(self):
        return config.data

    def _populate(self):
        super(PlayersPanels, self)._populate()
        self.hpBarsEnable = config.data['playersBarsEnabled']
        self.damagesEnable = config.data['playersDamagesEnabled']
        if self.hpBarsEnable:
            if not config.data['playersBarsClassColor']:
                self.settingsCore.onSettingsApplied += self.onSettingsApplied
            if config.data['playersBarsOnKeyPressed']:
                g_keysListener.registerComponent(self.as_setHealthBarsVisibleS, keyList=config.data['playersBarsHotkey'])
        if self.damagesEnable:
            damage_controller.onPlayerDamaged += self.onPlayerDamaged
            g_keysListener.registerComponent(self.as_setPlayersDamageVisibleS, keyList=config.data['playersDamagesHotkey'])

    def _dispose(self):
        self.flashObject.as_clearStorage()
        if self.hpBarsEnable and not config.data['playersBarsClassColor']:
            self.settingsCore.onSettingsApplied -= self.onSettingsApplied
        if self.damagesEnable:
            damage_controller.onPlayerDamaged -= self.onPlayerDamaged
        super(PlayersPanels, self)._dispose()

    def onSettingsApplied(self, diff):
        if GRAPHICS.COLOR_BLIND in diff:
            barColor = self.getBarColor(True, diff[GRAPHICS.COLOR_BLIND])
            self.as_colorBlindBarsS(barColor)

    def getBarColor(self, isEnemy, isColorBlind=None):
        colors = config.data['colors']
        if isEnemy:
            if isColorBlind is None:
                isColorBlind = self.isColorBlind()
            return colors['enemyColorBlind' if isColorBlind else 'enemy']
        return colors['ally']

    def createHealthBar(self, vehicleID, vInfoVO, isEnemy):
        max_health = vInfoVO.vehicleType.maxHealth
        if config.data['playersBarsClassColor']:
            color = self.getVehicleClassColor(vInfoVO.vehicleType.classTag)
        else:
            color = self.getBarColor(isEnemy)
        visible = not config.data['playersBarsOnKeyPressed']
        vehicle_data = {'health': max_health, 'maxHealth': max_health, 'percent': 100}
        self.as_addHealthBarS(vehicleID, color, config.data['playersBarsText'], visible)
        self.as_updateHealthBarS(vehicleID, 100, config.data['playersBarsHpText'] % vehicle_data)

    def onAddedToStorage(self, vehicleID, isEnemy):
        """Called from flash after creation in as_AddVehIdToListS"""
        vInfoVO = self.getVehicleInfo(vehicleID)
        if vInfoVO.isObserver():
            return
        if self.hpBarsEnable and vInfoVO.isAlive():
            self.createHealthBar(vehicleID, vInfoVO, isEnemy)
        if isEnemy and config.data['panelsSpottedFix']:
            self.as_setSpottedPositionS(vehicleID)
        if self.damagesEnable:
            self.as_addDamageS(vehicleID, config.data['playersDamagesSettings'])
        logDebug(True, 'PlayersPanels onAddedToStorage: id={} enemy={}', vehicleID, isEnemy)

    def updateDeadVehicles(self, aliveAllies, deadAllies, aliveEnemies, deadEnemies):
        for vehicleID in aliveAllies.union(aliveEnemies):
            self.as_AddVehIdToListS(vehicleID, vehicleID in aliveEnemies)
        for vehicleID in deadAllies.union(deadEnemies):
            self.as_setVehicleDeadS(vehicleID)

    def updateVehicleHealth(self, vehicleID, newHealth, maxHealth):
        if self.hpBarsEnable:
            if newHealth > maxHealth:
                maxHealth = newHealth
            health_percent = normalizeHealthPercent(newHealth, maxHealth)
            vehicle_data = {'health': max(0, newHealth), 'maxHealth': maxHealth, 'percent': health_percent}
            self.as_updateHealthBarS(vehicleID, health_percent, config.data["playersBarsHpText"] % vehicle_data)

    def onPlayerDamaged(self, attackerID, damage):
        damage_text = config.data['playersDamagesText'] % {'damage': damage}
        self.as_updateDamageS(attackerID, damage_text)


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, PlayersPanels, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
