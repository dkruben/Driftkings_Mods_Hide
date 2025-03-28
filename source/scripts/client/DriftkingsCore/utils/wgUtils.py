# -*- coding: utf-8 -*-
import importlib
import math
import os
from colorsys import hsv_to_rgb
from functools import partial

import BigWorld
import ResMgr
from BattleReplay import isPlaying, isLoading
from constants import ARENA_GUI_TYPE
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.daapi.view.battle.shared.formatters import normalizeHealth
from gui.battle_control import avatar_getter
from gui.shared.utils import getPlayerDatabaseID

from logger import logError

__all__ = ('battle_pages', 'battle_range', 'calculate_version', 'callback', 'cancelCallback', 'checkNamesList', 'distanceToEntityVehicle',
           'getAccountDBID', 'getColor', 'getDistanceTo', 'getEntity', 'getPercent', 'getPlayer', 'getRegion', 'getTarget', 'getVehCD',
           'hexToDecimal', 'isReplay', 'percentToRgb', 'replaceMacros', 'serverTime', 'square_position', 'xvmInstalled')


def getCurrentModsPath():
    for sec in ResMgr.openSection(os.path.join(cwd, 'paths.xml'))['Paths'].values():
        if './mods/' in sec.asString:
            return os.path.split(os.path.realpath(os.path.join(cwd, os.path.normpath(sec.asString))))


cwd = os.getcwdu() if os.path.supports_unicode_filenames else os.getcwd()
modsPath, gameVersion = getCurrentModsPath()


def create_range(obj, names):
    return tuple(getattr(obj, name) for name in names if hasattr(obj, name))


__battle_types = (
    "COMP7",
    "EPIC_BATTLE",
    "EPIC_RANDOM",
    "EPIC_RANDOM_TRAINING",
    "FORT_BATTLE_2",
    "MAPBOX",
    "RANDOM",
    "RANKED",
    "SORTIE_2",
    "TOURNAMENT_COMP7",
    "TRAINING",
    "UNKNOWN",
    "WINBACK",
)

__pages_types = (
    'CLASSIC_BATTLE_PAGE',
    'EPIC_BATTLE_PAGE',
    'EPIC_RANDOM_PAGE',
    'RANKED_BATTLE_PAGE',
    'STRONGHOLD_BATTLE_PAGE',
    'COMP7_BATTLE_PAGE',
)


battle_range = create_range(ARENA_GUI_TYPE, __battle_types)
battle_pages = create_range(VIEW_ALIAS, __pages_types)


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


def serverTime():
    return BigWorld.serverTime()


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
    SQUARES_NAME = 'KJHGFEDCBA'
    LINES_NAME = '1234567890'
    MIN_CLAMP_VALUE = 0.1
    GRID_SIZE = 10

    def __init__(self):
        self.player = None
        self.last_position = None
        self.last_square = None

    @staticmethod
    def clamp(val, v_max):
        return max(SquarePosition.MIN_CLAMP_VALUE, min(val, v_max))

    @classmethod
    def pos2name(cls, pos):
        try:
            x, y = int(pos[0]), int(pos[1])
            return "%s%s" % (cls.SQUARES_NAME[y - 1], cls.LINES_NAME[x - 1])
        except (IndexError, TypeError):
            logError('DriftkingsCore', "Invalid position coordinates: {}", pos)
            return "A1"

    def getSquarePosition(self):
        try:
            self.player = getPlayer()
            if self.player is None:
                logError('DriftkingsCore', "Player not available")
                return self.last_square or "A1"
            arena = getattr(self.player, 'arena', None)
            if arena is None:
                logError('DriftkingsCore', "Invalid Arena")
                return self.last_square or "A1"
            player_vehicle_id = getattr(self.player, 'playerVehicleID', None)
            if player_vehicle_id is None or player_vehicle_id not in BigWorld.entities:
                logError('DriftkingsCore', "Player vehicle not found")
                return self.last_square or "A1"
            position = BigWorld.entities[player_vehicle_id].position
            if self.last_position and position == self.last_position:
                return self.last_square
            self.last_position = position
            position_rect = (position[0], position[2])
            bounding_box = arena.arenaType.boundingBox
            bottom_left, upper_right = bounding_box
            space_size = (upper_right[0] - bottom_left[0], upper_right[1] - bottom_left[1])
            rel_pos = (position_rect[0] - bottom_left[0], position_rect[1] - bottom_left[1])
            rel_pos = (self.clamp(rel_pos[0], space_size[0]), self.clamp(rel_pos[1], space_size[1]))
            grid_pos = (int(rel_pos[0] / space_size[0] * self.GRID_SIZE + 0.5), int(rel_pos[1] / space_size[1] * self.GRID_SIZE + 0.5))
            self.last_square = self.pos2name(grid_pos)
            return self.last_square
        except Exception as e:
            logError('DriftkingsCore', "Error calculating square position: {}", e)
            return self.last_square or "A1"

    def getSquareForPosition(self, position):
        try:
            self.player = getPlayer()
            arena = getattr(self.player, 'arena', None)
            if arena is None:
                return "A1"
            position_rect = (position[0], position[2])
            bounding_box = arena.arenaType.boundingBox
            bottom_left, upper_right = bounding_box
            space_size = (upper_right[0] - bottom_left[0], upper_right[1] - bottom_left[1])
            rel_pos = (position_rect[0] - bottom_left[0], position_rect[1] - bottom_left[1])
            grid_pos = (int(rel_pos[0] / space_size[0] * self.GRID_SIZE + 0.5), int(rel_pos[1] / space_size[1] * self.GRID_SIZE + 0.5))
            return self.pos2name(grid_pos)
        except Exception as e:
            logError('DriftkingsCore', "Error calculating square for position: {}", e)
            return "A1"


square_position = SquarePosition()
