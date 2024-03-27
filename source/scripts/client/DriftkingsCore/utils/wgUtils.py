# -*- coding: utf-8 -*-
import importlib
import math
from functools import partial
from colorsys import hsv_to_rgb

import BigWorld
import ResMgr
from BattleReplay import isPlaying, isLoading, g_replayCtrl
from gui.battle_control import avatar_getter
from constants import ARENA_GUI_TYPE
from gui.shared.utils import getPlayerDatabaseID

__all__ = ('getPlayer', 'getTarget', 'getEntity', 'getDistanceTo', 'distanceToEntityVehicle', 'getVehCD', 'getRegion', 'callback',
           'cancelCallback', 'hex_to_decimal', 'isReplay', 'getColor', 'isDisabledByBattleType', 'percentToRGB', 'getAccountDBID', 'checkNamesList',)


DEFAULT_EXCLUDED_GUI_TYPES = {
    ARENA_GUI_TYPE.EPIC_RANDOM,
    ARENA_GUI_TYPE.EPIC_BATTLE,
    ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING,
    ARENA_GUI_TYPE.EPIC_TRAINING,
    ARENA_GUI_TYPE.EVENT_BATTLES,
    ARENA_GUI_TYPE.UNKNOWN
}


class Utils(object):
    def __init__(self):
        pass

    @staticmethod
    def getAccountDBID():
        return getPlayerDatabaseID()

    @staticmethod
    def isReplay():
        return isPlaying() or isLoading()

    @staticmethod
    def getPlayer():
        return BigWorld.player()

    @staticmethod
    def getTarget():
        return BigWorld.target()

    @staticmethod
    def getEntity(entity_id):
        return BigWorld.entity(entity_id)

    def getDistanceTo(self, targetPos):
        return self.getPlayer().position.distTo(targetPos)

    def distanceToEntityVehicle(self, entityID):
        entity_vehicle = self.getEntity(entityID)
        if entity_vehicle is not None:
            return self.getDistanceTo(entity_vehicle.position)
        return 0.0

    @staticmethod
    def getVehCD(vID):
        return avatar_getter.getArena().vehicles[vID]['vehicleType'].type.compactDescr

    # noinspection PyUnresolvedReferences
    @staticmethod
    def getRegion():
        return importlib.import_module('constants').AUTH_REALM

    @staticmethod
    def callback(delay, callMethod, *args, **kwargs):
        return BigWorld.callback(delay, partial(callMethod, *args, **kwargs) if args or kwargs else callMethod)

    @staticmethod
    def cancelCallback(callbackID):
        return BigWorld.cancelCallback(callbackID)

    @staticmethod
    def percentToRGB(percent, saturation=0.5, brightness=1.0, **__):
        position = min(0.8333, percent * 0.3333)
        r, g, b = (int(math.ceil(i * 255)) for i in hsv_to_rgb(position, saturation, brightness))
        return '#{:02X}{:02X}{:02X}'.format(r, g, b)

    @staticmethod
    def hex_to_decimal(*args):
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
    def getColor(linkage, *args, **kwargs):
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

    def isDisabledByBattleType(self, exclude=None, include=tuple()):
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


getAccountDBID = Utils().getAccountDBID
isReplay = Utils().isReplay
getPlayer = Utils().getPlayer
getTarget = Utils().getTarget
getEntity = Utils().getEntity
getDistanceTo = Utils().getDistanceTo
distanceToEntityVehicle = Utils().distanceToEntityVehicle
getVehCD = Utils().getVehCD
getRegion = Utils().getRegion
callback = Utils().callback
cancelCallback = Utils().cancelCallback
hex_to_decimal = Utils().hex_to_decimal
getColor = Utils().getColor
isDisabledByBattleType = Utils().isDisabledByBattleType
checkNamesList = Utils().checkNamesList
percentToRGB = Utils().percentToRGB
