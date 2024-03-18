# -*- coding: utf-8 -*-
import importlib
import string
from functools import partial

import BigWorld
import ResMgr
from BattleReplay import isPlaying, isLoading, g_replayCtrl
from gui.battle_control import avatar_getter
from constants import ARENA_GUI_TYPE
from gui.shared.utils import getPlayerDatabaseID

__all__ = ('g_macro', 'SafeDict', 'getPlayer', 'getTarget', 'getEntity', 'getDistanceTo', 'distanceToEntityVehicle', 'getVehCD',
           'getRegion', 'callback', 'cancelCallback', 'hex_to_decimal', 'isReplay', 'getColor', 'isDisabledByBattleType', 'getAccountDBID', 'checkNamesList',)


DEFAULT_EXCLUDED_GUI_TYPES = {
    ARENA_GUI_TYPE.EPIC_RANDOM,
    ARENA_GUI_TYPE.EPIC_BATTLE,
    ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING,
    ARENA_GUI_TYPE.EPIC_TRAINING,
    ARENA_GUI_TYPE.EVENT_BATTLES,
    ARENA_GUI_TYPE.UNKNOWN
}


class SafeFormatter(string.Formatter):
    def get_value(self, key, *args, **kwargs):
        try:
            return super(SafeFormatter, self).get_value(key, *args, **kwargs)
        except KeyError:
            return '{%s}' % key


g_macro = SafeFormatter()


class SafeDict(dict):
    def __missing__(self, args):
        return '%({macro})s'.format(macro=args)


class Utils(object):
    def __init__(self):
        self.getAccountDBID = self._getAccountDBID
        self.isReplay = self._isReplay
        self.getPlayer = self._getPlayer
        self.getTarget = self._getTarget
        self.getEntity = self._getEntity
        self.getDistanceTo = self._getDistanceTo
        self.distanceToEntityVehicle = self._distanceToEntityVehicle
        self.getVehCD = self._getVehCD
        self.getRegion = self._getRegion
        self.callback = self._callback
        self.cancelCallback = self._cancelCallback
        self.hex_to_decimal = self._hex_to_decimal
        self.getColor = self._getColor
        self.isDisabledByBattleType = self._isDisabledByBattleType

    @staticmethod
    def _getAccountDBID():
        return getPlayerDatabaseID()

    @staticmethod
    def _isReplay():
        return isPlaying() or isLoading()

    @staticmethod
    def _getPlayer():
        return BigWorld.player()

    @staticmethod
    def _getTarget():
        return BigWorld.target()

    @staticmethod
    def _getEntity(entity_id):
        return BigWorld.entity(entity_id)

    def _getDistanceTo(self, targetPos):
        return self.getPlayer().position.distTo(targetPos)

    def _distanceToEntityVehicle(self, entityID):
        entity_vehicle = self.getEntity(entityID)
        if entity_vehicle is not None:
            return self.getDistanceTo(entity_vehicle.position)
        return 0.0

    @staticmethod
    def _getVehCD(vID):
        return avatar_getter.getArena().vehicles[vID]['vehicleType'].type.compactDescr

    # noinspection PyUnresolvedReferences
    @staticmethod
    def _getRegion():
        return importlib.import_module('constants').AUTH_REALM

    @staticmethod
    def _callback(delay, callMethod, *args, **kwargs):
        return BigWorld.callback(delay, partial(callMethod, *args, **kwargs) if args or kwargs else callMethod)

    @staticmethod
    def _cancelCallback(callbackID):
        return BigWorld.cancelCallback(callbackID)

    @staticmethod
    def _hex_to_decimal(*args):
        hex_decimal_conversion = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                                  'A': 10, 'a': 10, 'B': 11, 'b': 11, 'C': 12, 'c': 12, 'D': 13, 'd': 13, 'E': 14, 'e': 14, 'F': 15, 'f': 15}
        p = len(args[0]) - 1
        decimal = 0
        for color in args[0]:
            decimal += hex_decimal_conversion[color] * (16 ** p)
            p -= 1
        return decimal

    @staticmethod
    def checkNamesList(directory):
        folder = ResMgr.openSection(directory)
        return sorted(folder.keys())

    @staticmethod
    def _getColor(linkage, *args, **kwargs):
        _var = linkage[args[0]]
        if args[1] is not None and _var is not None:
            for val in _var:
                if val['value'] > args[1]:
                    return '#' + val['color'][2:] if val['color'][:2] == '0x' else val['color']

        elif kwargs is not None:
            colors_x = linkage['x']
            for val in colors_x:
                if val['value'] > kwargs:
                    return '#' + val['color'][2:] if val['color'][:2] == '0x' else val['color']

    def _isDisabledByBattleType(self, exclude=None, include=tuple()):
        """
        In mod use (false)
        Example: config.data['enabled'] and not isDisabledByBattleType(include=(BATTLE ARENA)))
        param exclude: remove battle arena
        param include: battle arena type (excluded battle arena)
        """
        if not exclude:
            exclude = DEFAULT_EXCLUDED_GUI_TYPES
        if not hasattr(self.getPlayer(), 'arena') or self.getPlayer().arena is None:
            return False
        else:
            return True if self.getPlayer().arena.guiType in exclude and self.getPlayer().arena.guiType not in include else False


getAccountDBID = Utils()._getAccountDBID
isReplay = Utils()._isReplay
getPlayer = Utils()._getPlayer
getTarget = Utils()._getTarget
getEntity = Utils()._getEntity
getDistanceTo = Utils()._getDistanceTo
distanceToEntityVehicle = Utils()._distanceToEntityVehicle
getVehCD = Utils()._getVehCD
getRegion = Utils()._getRegion
callback = Utils()._callback
cancelCallback = Utils()._cancelCallback
hex_to_decimal = Utils()._hex_to_decimal
getColor = Utils()._getColor
isDisabledByBattleType = Utils()._isDisabledByBattleType
checkNamesList = Utils().checkNamesList
