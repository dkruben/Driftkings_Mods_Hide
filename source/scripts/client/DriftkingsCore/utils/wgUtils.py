# -*- coding: utf-8 -*-
import math
import os
from colorsys import hsv_to_rgb
from functools import partial

import BigWorld
import ResMgr
import Math
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
    Class to determine the grid square position of the player on the map.
    """
    def __call__(self):
        """
        Calculate the current square position of the player.
        str: The grid square position in format 'A1', 'B2', etc.
        """
        return self.getSquarePosition()

    @staticmethod
    def clamp(val, v_max):
        """
        Clamp a value between a minimum and maximum.
        val: The value to clamp
        v_max: The maximum allowed value
        float: The clamped value
        """
        v_min = 0.1
        return v_min if (val < v_min) else v_max if (val > v_max) else val

    @staticmethod
    def pos2name(pos):
        """
        Convert a position tuple to a grid square name.
        pos: Tuple containing (x, y) position
        str: Grid square name (e.g. 'A1', 'B2')
        """
        squareName = 'KJHGFEDCBA'
        linesName = '1234567890'
        return '{}{}'.format(squareName[int(pos[1]) - 1], linesName[int(pos[0]) - 1])

    def getSquarePosition(self):
        """
        Get the current square position of the player.
        str: The grid square position
        """
        player = getPlayer()
        boundingBox = player.arena.arenaType.boundingBox
        position = BigWorld.entities[player.playerVehicleID].position
        positionRect = Math.Vector2(position[0], position[2])
        bottomLeft, upperRight = boundingBox
        spaceSize = upperRight - bottomLeft
        relPos = positionRect - bottomLeft
        relPos[0] = self.clamp(relPos[0], spaceSize[0])
        relPos[1] = self.clamp(relPos[1], spaceSize[1])
        return self.pos2name((math.ceil(relPos[0] / spaceSize[0] * 10), math.ceil(relPos[1] / spaceSize[1] * 10)))


square_position = SquarePosition()
