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

from DriftkingsCore import DriftkingsConfigInterface, Analytics, checkKeys, override, logWarning, getEntity, getPlayer, calculate_version


class PlayersPanelController(DriftkingsConfigInterface):
    vCache = property(lambda self: self.__vCache)
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.__hpCache = {}
        self.__vCache = set()
        self.displayed = True
        super(PlayersPanelController, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.6.0 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben__EU'
        self.defaultKeys = {'toggle_key': [[Keys.KEY_LALT, Keys.KEY_RALT]]}
        self.data = {
            'enabled': True,
            'textFields': {},
            'mode': 0,
            'toggle_key': self.defaultKeys['toggle_key']
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_mode_text': 'Displaying mode',
            'UI_setting_mode_tooltip': (
                ' • <b>Always</b> - HP markers will always be displayed.\n'
                ' • <b>Toggle</b> - HP markers will be toggled on/off upon toggle key press.\n'
                ' • <b>Holding</b> - HP markers will only be displayed <b>while</b> the toggle key is pressed.'),
            'UI_setting_mode_always': 'Always',
            'UI_setting_mode_toggle': 'Toggle',
            'UI_setting_mode_holding': 'Holding',
            'UI_setting_toggle_key_text': 'Toggle hotkey',
            'UI_setting_toggle_key_tooltip': 'Pressing this button in-battle toggles HP markers displaying.'
        }
        try:
            g_driftkingsPlayersPanels.events.onUIReady += self.onStartBattle
        except Exception:
            traceback.print_exc()
        super(PlayersPanelController, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createOptions('mode', [self.i18n['UI_setting_mode_' + x] for x in ('always', 'toggle', 'holding')])
            ],
            'column2': [
                self.tb.createHotKey('toggle_key')
            ]
        }

    def readData(self, quiet=True):
        for fieldName in self.data['textFields']:
            try:
                g_driftkingsPlayersPanels.delete(self.ID + fieldName)
            except Exception:
                traceback.print_exc()
        super(PlayersPanelController, self).readCurrentSettings(quiet)
        self.data['textFields'].update(self.loadDataJson().get('textFields', {}))
        self.displayed = not self.data['mode']
        for fieldName, fieldData in self.data['textFields'].items():
            try:
                g_driftkingsPlayersPanels.create(self.ID + fieldName, fieldData)
            except Exception:
                traceback.print_exc()

    def onApplySettings(self, settings):
        super(PlayersPanelController, self).onApplySettings(settings)
        self.displayed = not settings['mode']

    @staticmethod
    def getVehicleHealth(vehicleID):
        try:
            vehicle = getEntity(vehicleID)
            if vehicle and hasattr(vehicle, 'health') and hasattr(vehicle, 'isCrewActive'):
                return vehicle.health if vehicle.isCrewActive and vehicle.health >= 0 else 0
            player = getPlayer()
            if player and hasattr(player, 'arena'):
                vehicle = player.arena.vehicles.get(vehicleID)
                if vehicle and vehicle.get('vehicleType'):
                    return vehicle['vehicleType'].maxHealth
        except Exception:
            traceback.print_exc()
        return 0

    def onStartBattle(self):
        try:
            player = getPlayer()
            if player and hasattr(player, 'arena'):
                player.arena.onVehicleKilled += self.onVehicleKilled
                collection = vos_collections.VehiclesInfoCollection().iterator(self.sessionProvider.getArenaDP())
                for vInfoVO in collection:
                    vehicleID = vInfoVO.vehicleID
                    self.__hpCache[vehicleID] = {'current': self.getVehicleHealth(vehicleID), 'max': vInfoVO.vehicleType.maxHealth}
                    self.setHPField(vehicleID)
        except Exception:
            traceback.print_exc()

    def setHPField(self, vehicleID):
        try:
            player = getPlayer()
            if not player or not hasattr(player, 'arena') or not hasattr(player, 'team'):
                return
            if player.arena.guiType in (ARENA_GUI_TYPE.EPIC_RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING):
                return
            if vehicleID not in player.arena.vehicles:
                return
            team = player.arena.vehicles[vehicleID]['team']
            panelSide = 'left' if player.team == team else 'right'
            if vehicleID not in self.__hpCache:
                return
            currentHP = max(0, self.__hpCache[vehicleID]['current'])
            maxHP = max(1, self.__hpCache[vehicleID]['max'])
            for fieldName, fieldData in sorted(self.data['textFields'].items()):
                if panelSide not in fieldData:
                    continue
                barWidth = 0
                if 'width' in fieldData[panelSide]:
                    barWidth = int(math.ceil(fieldData[panelSide]['width'] * (float(currentHP) / maxHP)))
                text = ''
                if self.displayed and (not fieldData.get('hideIfDead', False) or currentHP > 0):
                    try:
                        text = fieldData[panelSide]['text'] % {'curHealth': currentHP, 'maxHealth': maxHP, 'barWidth': barWidth}
                    except (KeyError, TypeError):
                        text = str(currentHP)
                g_driftkingsPlayersPanels.update(self.ID + fieldName, {'vehicleID': vehicleID, 'text': text})
        except Exception:
            traceback.print_exc()

    def onEndBattle(self):
        try:
            player = getPlayer()
            if player and hasattr(player, 'arena'):
                player.arena.onVehicleKilled -= self.onVehicleKilled
            self.displayed = not self.data['mode']
            self.__hpCache.clear()
            self.__vCache.clear()
        except Exception:
            traceback.print_exc()

    def onVehicleKilled(self, targetID, *_):
        try:
            if targetID in self.__hpCache:
                self.__hpCache[targetID]['current'] = 0
                self.setHPField(targetID)
        except Exception:
            traceback.print_exc()

    def updateHealth(self, vehicleID, newHealth=-1, *_, **__):
        try:
            if vehicleID not in self.__hpCache or newHealth == -1:
                player = getPlayer()
                if not player or not hasattr(player, 'arena'):
                    return
                vehicle = player.arena.vehicles.get(vehicleID)
                if not vehicle:
                    return
                maxHealth = vehicle.get('vehicleType', {}).maxHealth if vehicle and vehicle.get('vehicleType') else -1
                if maxHealth == -1:
                    return
                self.__hpCache[vehicleID] = {'current': self.getVehicleHealth(vehicleID), 'max': maxHealth}
            else:
                health = max(newHealth, 0)
                self.__hpCache[vehicleID]['current'] = health
            self.setHPField(vehicleID)
        except Exception:
            traceback.print_exc()

    def validateCache(self, vehicleID):
        try:
            if vehicleID is not None and isinstance(vehicleID, int):
                self.__vCache.add(vehicleID)
        except Exception:
            traceback.print_exc()

    def onHotkeyPressed(self, event):
        try:
            player = getPlayer()
            if not player or not hasattr(player, 'arena') or not self.data['enabled'] or not self.data['mode']:
                return
            if self.data['mode'] == 1 and checkKeys(self.data['toggle_key'], event.key) and event.isKeyDown():
                self.displayed = not self.displayed
            elif self.data['mode'] == 2:
                self.displayed = checkKeys(self.data['toggle_key'])
            for vehicleID in self.__hpCache:
                self.setHPField(vehicleID)
        except Exception:
            traceback.print_exc()


config = None
try:
    from DriftkingsPlayersPanelAPI import g_driftkingsPlayersPanels

    config = PlayersPanelController()
    statistic_mod = Analytics(config.ID, config.version)
except ImportError:
    try:
        logWarning('PlayersPanelHP', 'Battle Flash API not found.')
    except Exception:
        print('PlayersPanelHP: Battle Flash API not found.')
except Exception:
    traceback.print_exc()
else:
    @override(ArenaVehiclesPlugin, '_setInAoI')
    def new__setInAoI(func, self, entry, isInAoI, *args, **kwargs):
        result = func(self, entry, isInAoI, *args, **kwargs)
        try:
            if hasattr(self, '_entries'):
                for vehicleID, entry2 in self._entries.items():
                    if entry == entry2 and isInAoI:
                        if vehicleID in config.vCache:
                            break
                        config.updateHealth(vehicleID)
        except Exception:
            traceback.print_exc()
        finally:
            return result

    @override(PlayerAvatar, 'vehicle_onAppearanceReady')
    def new__onEnterWorld(func, self, vehicle, *args, **kwargs):
        result = func(self, vehicle, *args, **kwargs)
        try:
            if vehicle and hasattr(vehicle, 'id'):
                vehicleID = vehicle.id
                config.validateCache(vehicleID)
                config.updateHealth(vehicleID)
        except Exception:
            traceback.print_exc()
        finally:
            return result

    @override(Vehicle, 'onHealthChanged')
    def new_vehicle_onHealthChanged(func, self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
        result = func(self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs)
        try:
            if hasattr(self, 'id'):
                config.updateHealth(self.id, newHealth)
        except Exception:
            traceback.print_exc()
        finally:
            return result

    @override(PlayersPanelMeta, 'as_setPanelHPBarVisibilityStateS')
    def new__setPanelHPBarVisibilityStateS(func, self, value):
        try:
            if config and config.data and config.data['enabled']:
                return
            func(self, value)
        except Exception:
            traceback.print_exc()
            return func(self, value)
