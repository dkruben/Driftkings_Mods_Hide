# -*- coding: utf-8 -*-
import importlib
import math
from colorsys import hsv_to_rgb
from functools import partial

import BigWorld
import ResMgr
from BattleReplay import isPlaying, isLoading
from constants import ARENA_GUI_TYPE
from gui.Scaleform.daapi.view.battle.shared.formatters import normalizeHealth
from gui.battle_control import avatar_getter
from gui.shared.utils import getPlayerDatabaseID

__all__ = ('calculateVersion', 'getPlayer', 'getTarget', 'getEntity', 'getDistanceTo', 'distanceToEntityVehicle', 'getVehCD', 'getRegion', 'callback', 'getPercent',
           'cancelCallback', 'hex_to_decimal', 'isReplay', 'getColor', 'isDisabledByBattleType', 'percentToRGB', 'getAccountDBID', 'checkNamesList',)


DEFAULT_EXCLUDED_GUI_TYPES = {
    ARENA_GUI_TYPE.EPIC_RANDOM,
    ARENA_GUI_TYPE.EPIC_BATTLE,
    ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING,
    ARENA_GUI_TYPE.EPIC_TRAINING,
    ARENA_GUI_TYPE.EVENT_BATTLES,
    ARENA_GUI_TYPE.UNKNOWN
}


def calculateVersion(version):
    return sum(int(x) * (10 ** i) for i, x in enumerate(reversed(version.split(' ')[0].split('.'))))


def getAccountDBID():
    return getPlayerDatabaseID()


def isReplay():
    return isPlaying() or isLoading()


def getPlayer():
    return BigWorld.player()


def getTarget():
    return BigWorld.target()


def getEntity(entity_id):
    return BigWorld.entity(entity_id)


def getDistanceTo(self, targetPos):
    return self.getPlayer().position.distTo(targetPos)


def distanceToEntityVehicle(self, entityID):
    entity_vehicle = self.getEntity(entityID)
    if entity_vehicle is not None:
        return self.getDistanceTo(entity_vehicle.position)
    return 0.0


def getVehCD(vID):
    return avatar_getter.getArena().vehicles[vID]['vehicleType'].type.compactDescr


# noinspection PyUnresolvedReferences
def getRegion():
    return importlib.import_module('constants').AUTH_REALM


def callback(delay, callMethod, *args, **kwargs):
    return BigWorld.callback(delay, partial(callMethod, *args, **kwargs) if args or kwargs else callMethod)


def cancelCallback(callbackID):
    return BigWorld.cancelCallback(callbackID)


def percentToRGB(percent, saturation=0.5, brightness=1.0, **__):
    position = min(0.8333, percent * 0.3333)
    r, g, b = (int(math.ceil(i * 255)) for i in hsv_to_rgb(position, saturation, brightness))
    return '#{:02X}{:02X}{:02X}'.format(r, g, b)


def hex_to_decimal(*args):
    hex_decimal_conversion = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                              'A': 10, 'a': 10, 'B': 11, 'b': 11, 'C': 12, 'c': 12, 'D': 13, 'd': 13, 'E': 14, 'e': 14, 'F': 15, 'f': 15}
    p = len(args[0]) - 1
    decimal = 0
    for color in args[0]:
        decimal += hex_decimal_conversion[color] * (16 ** p)
        p -= 1
    return decimal


def checkNamesList(directory):
    folder = ResMgr.openSection(directory)
    return sorted(folder.keys())


# def getColor(linkage, *args, **kwargs):
#    _var = linkage[args[0]]
#    if args[1] is not None and _var is not None:
#        for val in _var:
#            if val['value'] > args[1]:
#                return '#' + val['color'][2:] if val['color'][:2] == '0x' else val['color']

#    elif kwargs is not None:
#        colors_x = linkage['x']
#        for val in colors_x:
#            if val['value'] > kwargs:
#                return '#' + val['color'][2:] if val['color'][:2] == '0x' else val['color']


def getColor(linkage, ratting_color, value=None, kwargs=None):
    if ratting_color in linkage:
        category_values = linkage[ratting_color]
        if value is not None:
            for item in category_values:
                if item['value'] > value:
                    return format_color(item['color'])

        if kwargs is not None:
            colors_x = linkage.get('x', [])
            for item in colors_x:
                if item['value'] > kwargs:
                    return format_color(item['color'])
    return None


def format_color(color):
    return '#' + color[2:] if color.startswith('0x') else color


def getPercent(param_a, param_b):
    if param_b <= 0:
        return 0.0
    return float(normalizeHealth(param_a)) / param_b


def isDisabledByBattleType(exclude=None, include=tuple()):
    if not exclude:
        exclude = DEFAULT_EXCLUDED_GUI_TYPES
    if not hasattr(getPlayer(), 'arena') or getPlayer().arena is None:
        return False
    else:
        return True if getPlayer().arena.guiType in exclude and getPlayer().arena.guiType not in include else False
