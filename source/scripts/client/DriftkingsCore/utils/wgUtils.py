# -*- coding: utf-8 -*-
import importlib
import math
import os
from colorsys import hsv_to_rgb
from functools import partial

import BigWorld
import ResMgr
from BattleReplay import isPlaying, isLoading
from gui.Scaleform.daapi.view.battle.shared.formatters import normalizeHealth
from gui.battle_control import avatar_getter
from gui.shared.utils import getPlayerDatabaseID

from logger import logError

__all__ = ('calculate_version', 'callback', 'cancelCallback', 'checkNamesList', 'distanceToEntityVehicle', 'getAccountDBID',
           'getDistanceTo', 'getEntity', 'getPlayer', 'getTarget', 'getVehCD', 'getColor', 'getPercent', 'getRegion',
           'hexToDecimal', 'isReplay', 'percentToRgb', 'replaceMacros','xvmInstalled', 'square_position')


def getCurrentModsPath():
    for sec in ResMgr.openSection(os.path.join(cwd, 'paths.xml'))['Paths'].values():
        if './mods/' in sec.asString:
            return os.path.split(os.path.realpath(os.path.join(cwd, os.path.normpath(sec.asString))))


cwd = os.getcwdu() if os.path.supports_unicode_filenames else os.getcwd()
modsPath, gameVersion = getCurrentModsPath()


def isXvmInstalled():
    xfw = os.path.exists(os.path.join(modsPath, gameVersion, 'com.modxvm.xfw'))
    xvm = os.path.exists(os.path.join(cwd, 'res_mods', 'mods', 'xfw_packages', 'xvm_main'))
    return xfw and xvm


xvmInstalled = isXvmInstalled()


def calculate_version(version):
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


def getDistanceTo(self, target_pos):
    return self.getPlayer().position.distTo(target_pos)


def distanceToEntityVehicle(self, entity_id):
    entity_vehicle = self.getEntity(entity_id)
    if entity_vehicle is not None:
        return self.getDistanceTo(entity_vehicle.position)
    return 0.0


def getVehCD(v_type):
    return avatar_getter.getArena().vehicles[v_type]['vehicleType'].type.compactDescr


# noinspection PyUnresolvedReferences
def getRegion():
    return importlib.import_module('constants').AUTH_REALM


def callback(delay, call_method, *args, **kwargs):
    return BigWorld.callback(delay, partial(call_method, *args, **kwargs) if args or kwargs else call_method)


def cancelCallback(callback_id):
    return BigWorld.cancelCallback(callback_id)


def percentToRgb(percent, saturation=0.5, brightness=1.0, **__):
    position = min(0.8333, percent * 0.3333)
    r, g, b = (int(math.ceil(i * 255)) for i in hsv_to_rgb(position, saturation, brightness))
    return '#{:02X}{:02X}{:02X}'.format(r, g, b)


def hexToDecimal(*args):
    hex_decimal_conversion = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'A': 10, 'a': 10, 'B': 11, 'b': 11, 'C': 12, 'c': 12, 'D': 13, 'd': 13, 'E': 14, 'e': 14, 'F': 15, 'f': 15
    }
    p = len(args[0]) - 1
    decimal = 0
    for color in args[0]:
        decimal += hex_decimal_conversion[color] * (16 ** p)
        p -= 1
    return decimal


def checkNamesList(directory):
    folder = ResMgr.openSection(directory)
    return sorted(folder.keys())


def getColor(data, ratting_color, value=None, kwargs=None):
    if ratting_color in data:
        category_values = data[ratting_color]
        if value is not None:
            for item in category_values:
                if item['value'] > value:
                    return formatColor(item['color'])

        if kwargs is not None:
            colors_x = data.get('x', [])
            for item in colors_x:
                if item['value'] > kwargs:
                    return formatColor(item['color'])
    return None


def formatColor(color):
    return '#' + color[2:] if color.startswith('0x') else color


def replaceMacros(text_format, data):
    for macro, value in data.items():
        text_format = text_format.replace(macro, value)
    return text_format


def getPercent(param_a, param_b):
    if param_b <= 0:
        return 0.0
    return float(normalizeHealth(param_a)) / param_b


class SquarePosition(object):
    def __init__(self):
        self.player = None

    def getSquarePosition(self):

        def clamp(val, vMax):
            vMin = 0.1
            return max(vMin, min(val, vMax))

        def pos2name(pos):
            sqrsName = 'KJHGFEDCBA'
            linesName = '1234567890'
            return '%s%s' % (sqrsName[int(pos[1]) - 1], linesName[int(pos[0]) - 1])

        self.player = getPlayer()
        arena = getattr(self.player, 'arena', None)
        if arena is None:
            logError('DriftkingsCore', "Invalid Arena {}", self.player.arena)

        boundingBox = arena.arenaType.boundingBox
        position = BigWorld.entities[self.player.playerVehicleID].position
        positionRect = (position[0], position[2])
        bottomLeft, upperRight = boundingBox
        spaceSize = (upperRight[0] - bottomLeft[0], upperRight[1] - bottomLeft[1])
        relPos = (positionRect[0] - bottomLeft[0], positionRect[1] - bottomLeft[1])
        relPos = (clamp(relPos[0], spaceSize[0]), clamp(relPos[1], spaceSize[1]))

        return pos2name((int(relPos[0] / spaceSize[0] * 10 + 0.5), int(relPos[1] / spaceSize[1] * 10 + 0.5)))


square_position = SquarePosition()
