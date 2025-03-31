# -*- coding: utf-8 -*-
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

__all__ = ('battle_pages', 'battle_range', 'calculate_version', 'callback', 'cancelCallback', 'checkNamesList',
           'distanceToEntityVehicle', 'getAccountDBID', 'getColor', 'getDistanceTo', 'getEntity', 'getPercent',
           'getPlayer', 'getTarget', 'getVehCD', 'hexToDecimal', 'isReplay', 'percentToRgb', 'replaceMacros',
           'serverTime', 'square_position', 'xvmInstalled')


def getCurrentModsPath():
    """
    Get the current mods path from paths.xml.
    """
    for sec in ResMgr.openSection(os.path.join(cwd, 'paths.xml'))['Paths'].values():
        if './mods/' in sec.asString:
            return os.path.split(os.path.realpath(os.path.join(cwd, os.path.normpath(sec.asString))))


cwd = os.getcwdu() if os.path.supports_unicode_filenames else os.getcwd()
modsPath, gameVersion = getCurrentModsPath()


def create_range(obj, names):
    """
    Create a tuple of attributes from an object based on a list of attribute names.
    obj: The object to extract attributes from.
    names: A sequence of attribute names to extract.
    """
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
    """
    Check if XVM mod is installed.
    bool: True if XVM is installed, False otherwise.
    """
    xfw = os.path.exists(os.path.join(modsPath, gameVersion, 'com.modxvm.xfw'))
    xvm = os.path.exists(os.path.join(cwd, 'res_mods', 'mods', 'xfw_packages', 'xvm_main'))
    return xfw and xvm


xvmInstalled = isXvmInstalled()


def calculate_version(version):
    """
    Calculate a numeric version from a version string.
    version (str): Version string in format "X.Y.Z [...]"
    """
    return sum(int(x) * (10 ** i) for i, x in enumerate(reversed(version.split(' ')[0].split('.'))))


def getAccountDBID():
    """
    Get the current player's database ID.
    int: Player's database ID.
    """
    return getPlayerDatabaseID()


def isReplay():
    """
    Check if the current session is a replay.
    bool: True if in replay mode, False otherwise.
    """
    return isPlaying() or isLoading()


def getPlayer():
    """
    Get the current player entity.
    object: The player entity.
    """
    return BigWorld.player()


def getTarget():
    """
    Get the current target entity.
    object: The target entity or None if no target.
    """
    return BigWorld.target()


def getEntity(entityID):
    """
    Get an entity by its ID.
    entityID (int): The entity ID to look up.
    object: The entity or None if not found.
    """
    return BigWorld.entity(entityID)


def getDistanceTo(self, target_pos):
    """
    Calculate distance from player to a target position.
    self: The instance containing the player.
    target_pos: The target position to measure distance to.
    float: Distance to the target position.
    """
    return self.getPlayer().position.distTo(target_pos)


def distanceToEntityVehicle(self, entityID):
    """
    Calculate distance from player to a specific entity vehicle.
    self: The instance containing the player.
    entityID (int): The entity ID of the vehicle.
    float: Distance to the entity vehicle or 0.0 if entity not found.
    """
    entity_vehicle = self.getEntity(entityID)
    if entity_vehicle is not None:
        return self.getDistanceTo(entity_vehicle.position)
    return 0.0


def getVehCD(vType):
    """
    Get the compact descriptor for a vehicle type.
    vType: The vehicle type.
    int: The compact descriptor for the vehicle type.
    """
    return avatar_getter.getArena().vehicles[vType]['vehicleType'].type.compactDescr


def callback(delay, callMethod, *args, **kwargs):
    """
    Schedule a callback to be executed after a delay.
    delay (float): Delay in seconds before executing the callback.
    call_method (callable): The method to call.
    *args: Arguments to pass to the method.
    **kwargs: Keyword arguments to pass to the method.
    int: Callback ID that can be used to cancel the callback.
    """
    return BigWorld.callback(delay, partial(callMethod, *args, **kwargs) if args or kwargs else callMethod)


def serverTime():
    """
    Get the current server time.
    float: Current server time.
    """
    return BigWorld.serverTime()


def cancelCallback(callbackID):
    """
    Cancel a previously scheduled callback.
    callbackID (int): The ID of the callback to cancel.
    bool: True if successful, False otherwise.
    """
    return BigWorld.cancelCallback(callbackID)


def percentToRgb(percent, saturation=0.5, brightness=1.0, **__):
    """
    Convert a percentage value to an RGB color.
    percent (float): Percentage value between 0.0 and 1.0.
    saturation (float, optional): Color saturation. Defaults to 0.5.
    brightness (float, optional): Color brightness. Defaults to 1.0.
    **__: Additional unused keyword arguments.
    str: RGB color in hex format (#RRGGBB).
    """
    position = min(0.8333, percent * 0.3333)
    r, g, b = (int(math.ceil(i * 255)) for i in hsv_to_rgb(position, saturation, brightness))
    return '#{:02X}{:02X}{:02X}'.format(r, g, b)


def hexToDecimal(*args):
    """
    Convert a hexadecimal string to a decimal integer.
    *args: First argument should be a string containing hexadecimal digits.
    int: Decimal representation of the hexadecimal string.
    """
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
    """
    Get a sorted list of keys from a resource directory.
    directory (str): Path to the resource directory.
    list: Sorted list of keys in the directory.
    """
    folder = ResMgr.openSection(directory)
    return sorted(folder.keys())


def getColor(data, ratting_color, value=None, kwargs=None):
    """
    Get a color based on a rating value from a color configuration.
    data (dict): Color configuration data.
    ratting_color (str): Rating category key.
    value (float, optional): Value to compare against thresholds. Defaults to None.
    kwargs (float, optional): Alternative value for 'x' category. Defaults to None.
    str: Color in hex format or None if not found.
    """
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
    """
    Format a color string to a standard hex format.
    color (str): Color string, possibly starting with '0x'.
    str: Color in standard hex format (#RRGGBB).
    """
    return '#' + color[2:] if color.startswith('0x') else color


def replaceMacros(text_format, data):
    """
    Replace macros in a text format with their corresponding values.
    text_format (str): Text containing macros to be replaced.
    data (dict): Dictionary of macro-value pairs.
    str: Text with macros replaced by their values.
    """
    for macro, value in data.items():
        text_format = text_format.replace(macro, value)
    return text_format


def getPercent(param_a, param_b):
    """
    Calculate the percentage of one value relative to another.
    param_a (float): Numerator value.
    param_b (float): Denominator value.
    float: Percentage value or 0.0 if param_b is zero or negative.
    """
    if param_b <= 0:
        return 0.0
    return float(normalizeHealth(param_a)) / param_b


class SquarePosition(object):
    """
    Class for calculating grid positions on the battle map.
    The map is divided into a 10x10 grid with letters for rows (K-A)
    and numbers for columns (1-0).
    """
    SQUARES_NAME = 'KJHGFEDCBA'
    LINES_NAME = '1234567890'

    def __init__(self):
        """Initialize the SquarePosition object."""
        self.player = None
        self.lastPosition = None
        self.lastSquare = None

    @staticmethod
    def clamp(val, v_max):
        """
        Clamp a value between MIN_CLAMP_VALUE and v_max.
        val (float): Value to clamp.
        v_max (float): Maximum allowed value.
        float: Clamped value.
        """
        return max(0.1, min(val, v_max))

    @classmethod
    def pos2name(cls, pos):
        """
        Convert grid position to square name.
        pos (tuple): Grid position as (x, y) coordinates.
        str: Square name (e.g., 'A1', 'B2').
        """
        x, y = int(pos[0]), int(pos[1])
        x_idx = max(0, min(x - 1, len(cls.LINES_NAME) - 1))
        y_idx = max(0, min(y - 1, len(cls.SQUARES_NAME) - 1))
        return "%s%s" % (cls.SQUARES_NAME[y_idx], cls.LINES_NAME[x_idx])

    def getSquarePosition(self):
        """
        Get the current player's square position on the map.
        str: Square position (e.g., 'A1', 'B2') or last known position if player not found.
        """
        self.player = getPlayer()
        arena = getattr(self.player, 'arena', None)
        playerVehicleID = getattr(self.player, 'playerVehicleID', None)
        if playerVehicleID is None or playerVehicleID not in BigWorld.entities:
            logError('DriftkingsCore', "Player vehicle not found")
            return self.lastSquare
        position = BigWorld.entities[playerVehicleID].position
        if self.lastSquare and position == self.lastPosition:
            return self.lastSquare
        self.lastPosition = position
        position_rect = (position[0], position[2])
        bounding_box = arena.arenaType.boundingBox
        bottom_left, upper_right = bounding_box
        space_size = (upper_right[0] - bottom_left[0], upper_right[1] - bottom_left[1])
        rel_pos = (position_rect[0] - bottom_left[0], position_rect[1] - bottom_left[1])
        rel_pos = (self.clamp(rel_pos[0], space_size[0]), self.clamp(rel_pos[1], space_size[1]))
        grid_pos = (int(rel_pos[0] / space_size[0] * 10 + 0.5), int(rel_pos[1] / space_size[1] * 10 + 0.5))
        try:
            self.lastSquare = self.pos2name(grid_pos)
        except Exception as e:
            logError('DriftkingsCore', "Error in pos2name: %s, grid_pos=%s", str(e), str(grid_pos))
            self.lastSquare = self.lastSquare or "A1"
        return self.lastSquare

    def getSquareForPosition(self, position):
        """
        Get the square name for a specific position on the map.
        position (tuple): 3D position coordinates.
        str: Square position (e.g., 'A1', 'B2').
        """
        self.player = getPlayer()
        arena = getattr(self.player, 'arena', None)
        position_rect = (position[0], position[2])
        bounding_box = arena.arenaType.boundingBox
        bottom_left, upper_right = bounding_box
        space_size = (upper_right[0] - bottom_left[0], upper_right[1] - bottom_left[1])
        rel_pos = (position_rect[0] - bottom_left[0], position_rect[1] - bottom_left[1])
        rel_pos = (self.clamp(rel_pos[0], space_size[0]), self.clamp(rel_pos[1], space_size[1]))
        grid_pos = (int(rel_pos[0] / space_size[0] * 10 + 0.5), int(rel_pos[1] / space_size[1] * 10 + 0.5))
        try:
            return self.pos2name(grid_pos)
        except Exception as e:
            logError('DriftkingsCore', "Error in getSquareForPosition: %s, grid_pos=%s", str(e), str(grid_pos))
            return "A1"


square_position = SquarePosition()
