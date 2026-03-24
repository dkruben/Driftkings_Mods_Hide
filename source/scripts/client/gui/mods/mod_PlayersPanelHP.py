# -*- coding: utf-8 -*-
import math
import traceback

import Keys
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from constants import ARENA_GUI_TYPE
from gui.Scaleform.daapi.view.battle.shared.minimap.plugins import ArenaVehiclesPlugin
from gui.Scaleform.daapi.view.meta.PlayersPanelMeta import PlayersPanelMeta
from gui.battle_control.arena_info import vos_collections
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, checkKeys, calculate_version, logWarning, getPlayer, getEntity


class PlayersPanelController(DriftkingsConfigInterface):
    vCache = property(lambda self: self.__vCache)
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.__hpCache = {}
        self.__vCache = set()
        self.__battleStarted = False
        self.displayed = True
        super(PlayersPanelController, self).__init__()
        g_driftkingsPlayersPanels.onUIReady += self.onPlayersPanelReady
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.new__destroyGUI)
        override(PlayerAvatar, '_PlayerAvatar__startGUI', self.new__startGUI)
        override(ArenaVehiclesPlugin, '_setInAoI', self.new__setInAoI)
        override(PlayerAvatar, 'vehicle_onAppearanceReady', self.new__onAppearanceReady)
        override(Vehicle, 'onHealthChanged', self.new__onHealthChanged)
        override(PlayersPanelMeta, 'as_setPanelHPBarVisibilityStateS', self.new__setPanelHPBarVisibilityStateS)

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.9.1 (%(file_compile_date)s)'
        self.author = 'Re-Coded by DriftKing\'s'
        self.defaultKeys = {'toggleKey': [[Keys.KEY_LALT, Keys.KEY_RALT]]}
        self.data = {'enabled': True, 'textFields': {}, 'mode': 0, 'toggleKey': self.defaultKeys['toggleKey']}
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_mode_text': 'Choose your option',
            'UI_setting_mode_tooltip': (
                ' • <b>Always</b> - HP markers will always be displayed.\n'
                ' • <b>Toggle</b> - HP markers will be toggled on/off upon toggle key press.\n'
                ' • <b>Holding</b> - HP markers will only be displayed <b>while</b> the toggle key is pressed.'
            ),
            'UI_setting_mode_always': 'Always',
            'UI_setting_mode_toggle': 'Toggle',
            'UI_setting_mode_holding': 'Holding',
            'UI_setting_toggleKey_text': 'Toggle hotkey',
            'UI_setting_toggleKey_tooltip': 'Pressing this button in-battle toggles HP markers displaying.'
        }
        super(PlayersPanelController, self).init()

    @staticmethod
    def _getArena():
        player = getPlayer()
        return player.arena if player is not None and hasattr(player, 'arena') else None

    def _isSupportedBattle(self):
        arena = self._getArena()
        return arena is not None and arena.guiType not in (ARENA_GUI_TYPE.EPIC_RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING)

    @staticmethod
    def _normalizeHealthValue(value, default=0):
        if value in (None, ''):
            return default
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return default

    def _clearDisplayedFields(self):
        if not g_driftkingsPlayersPanels.viewLoad:
            return
        for vehicleID in self.__hpCache:
            for fieldName in self.data['textFields']:
                g_driftkingsPlayersPanels.update(self.ID + fieldName, {'vehicleID': vehicleID, 'text': ''})

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [self.tb.createOptions('mode', [self.i18n['UI_setting_mode_' + x] for x in ('always', 'toggle', 'holding')])],
            'column2': [self.tb.createHotKey('toggleKey')]
        }

    def onApplySettings(self, settings):
        super(PlayersPanelController, self).onApplySettings(settings)
        self.displayed = not settings['mode']
        for vehicleID in self.__hpCache:
            self.setHPField(vehicleID)

    @staticmethod
    def getVehicleHealth(vehicleID):
        if hasattr(getEntity(vehicleID), 'health'):
            vehicle = getEntity(vehicleID)
            return vehicle.health if vehicle.isCrewActive and vehicle.health >= 0 else 0
        arena = PlayersPanelController._getArena()
        if arena is None:
            return 0
        vehicle = arena.vehicles.get(vehicleID)
        if vehicle is not None and vehicle['vehicleType'] is not None:
            return vehicle['vehicleType'].maxHealth
        return 0

    def hasOwnProperty(self):
        self.data['textFields'].update(self.loadDataJson().get('textFields', {}))
        self.displayed = not self.data['mode']
        for fieldName, fieldData in self.data['textFields'].iteritems():
            if not g_driftkingsPlayersPanels.hasOwnProperty(self.ID + fieldName):
                g_driftkingsPlayersPanels.create(self.ID + fieldName, fieldData)

    def onPlayersPanelReady(self, *_):
        self.hasOwnProperty()
        self.onStartBattle()

    def onStartBattle(self):
        arena = self._getArena()
        if not g_driftkingsPlayersPanels.viewLoad or arena is None or not self._isSupportedBattle() or self.__battleStarted:
            return
        self.__battleStarted = True
        arena.onVehicleKilled += self.onVehicleKilled
        collection = vos_collections.VehiclesInfoCollection().iterator(self.sessionProvider.getArenaDP())
        for vInfoVO in collection:
            vehicleID = vInfoVO.vehicleID
            self.__hpCache[vehicleID] = {
                'current': self.getVehicleHealth(vehicleID),
                'max': vInfoVO.vehicleType.maxHealth
            }
            self.setHPField(vehicleID)

    def setHPField(self, vehicleID):
        arena = self._getArena()
        if arena is None or not self._isSupportedBattle() or vehicleID not in self.__hpCache or vehicleID not in arena.vehicles:
            return
        player = getPlayer()
        team = arena.vehicles[vehicleID]['team']
        panelSide = 'left' if player.team == team else 'right'
        currentHP = self._normalizeHealthValue(self.__hpCache[vehicleID]['current'])
        maxHP = self._normalizeHealthValue(self.__hpCache[vehicleID]['max'])
        self.__hpCache[vehicleID]['current'] = currentHP
        self.__hpCache[vehicleID]['max'] = maxHP
        for fieldName, fieldData in sorted(self.data['textFields'].iteritems()):
            barWidth = currentHP
            if 'width' in fieldData[panelSide]:
                try:
                    barWidth = int(math.ceil(fieldData[panelSide]['width'] * (float(currentHP) / float(maxHP)))) if maxHP > 0 else 0
                except (TypeError, ValueError, ZeroDivisionError):
                    barWidth = 0
            if g_driftkingsPlayersPanels.viewLoad:
                text = ''
                if self.displayed and (not fieldData.get('hideIfDead', False) or barWidth):
                    text = fieldData[panelSide]['text'] % {'curHealth': currentHP, 'maxHealth': maxHP, 'barWidth': barWidth}
                g_driftkingsPlayersPanels.update(self.ID + fieldName, {'vehicleID': vehicleID, 'text': text})

    def onEndBattle(self):
        arena = self._getArena()
        if self.__battleStarted and arena is not None:
            arena.onVehicleKilled -= self.onVehicleKilled
        self.__battleStarted = False
        self.displayed = not self.data['mode']
        self._clearDisplayedFields()
        self.__hpCache.clear()
        self.__vCache.clear()

    def onVehicleKilled(self, targetID, *_):
        if targetID in self.__hpCache:
            self.__hpCache[targetID]['current'] = 0
            self.setHPField(targetID)

    def updateHealth(self, vehicleID, newHealth=-1, *_, **__):
        arena = self._getArena()
        if not g_driftkingsPlayersPanels.viewLoad or arena is None or vehicleID not in arena.vehicles:
            return
        if vehicleID not in self.__hpCache or newHealth == -1:
            vehicle = arena.vehicles.get(vehicleID)
            maxHealth = vehicle['vehicleType'].maxHealth if vehicle and vehicle['vehicleType'] else 0
            self.__hpCache[vehicleID] = {'current': self.getVehicleHealth(vehicleID), 'max': maxHealth}
        else:
            health = self._normalizeHealthValue(newHealth)
            self.__hpCache[vehicleID]['current'] = health if vehicleID in self.__vCache else self.__hpCache[vehicleID]['max']
        self.setHPField(vehicleID)

    def validateCache(self, vehicleID):
        if vehicleID not in self.__vCache:
            self.__vCache.add(vehicleID)

    def onHotkeyPressed(self, event):
        if not hasattr(getPlayer(), 'arena') or not self.data['enabled'] or not self.data['mode']:
            return
        if self.data['mode'] == 1 and checkKeys(self.data['toggleKey'], event.key) and event.isKeyDown():
            self.displayed = not self.displayed
        elif self.data['mode'] == 2:
            self.displayed = checkKeys(self.data['toggleKey'])
        for vehicleID in self.__hpCache:
            self.setHPField(vehicleID)

    def new__destroyGUI(self, func, *args):
        func(*args)
        self.onEndBattle()

    def new__startGUI(self, func, *args):
        func(*args)
        self.hasOwnProperty()
        self.onStartBattle()

    def new__setInAoI(self, func, orig, entry, isInAoI, *args, **kwargs):
        result = func(orig, entry, isInAoI, *args, **kwargs)
        try:
            for vehicleID, entry2 in orig._entries.iteritems():
                if entry == entry2 and isInAoI:
                    if vehicleID in self.__vCache:
                        break
                    self.updateHealth(vehicleID)
        except Exception:
            traceback.print_exc()
        return result

    def new__onAppearanceReady(self, func, orig, vehicle, *args, **kwargs):
        result = func(orig, vehicle, *args, **kwargs)
        try:
            vehicleID = vehicle.id
            self.validateCache(vehicleID)
            self.updateHealth(vehicleID)
        except Exception:
            traceback.print_exc()
        return result

    def new__onHealthChanged(self, func, orig, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
        result = func(orig, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs)
        try:
            self.updateHealth(orig.id, newHealth)
        except Exception:
            traceback.print_exc()
        return result

    def new__setPanelHPBarVisibilityStateS(self, func, orig, value):
        if self.data['enabled']:
            return
        func(orig, value)


g_config = None
try:
    from DriftkingsPlayersPanelAPI import g_driftkingsPlayersPanels
    g_config = PlayersPanelController()
    statistic_mod = Analytics(g_config.ID, g_config.version)
except ImportError:
    logWarning('[PlayersPanelHP]:', 'Battle Flash API not found.')
