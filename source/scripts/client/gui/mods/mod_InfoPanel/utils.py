# -*- coding: utf-8 -*-
from constants import ARENA_GUI_TYPE

from DriftkingsCore import getPlayer

DEFAULT_EXCLUDED_GUI_TYPES = {
    ARENA_GUI_TYPE.EPIC_RANDOM, ARENA_GUI_TYPE.EPIC_BATTLE, ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING,
    ARENA_GUI_TYPE.EPIC_TRAINING, ARENA_GUI_TYPE.EVENT_BATTLES, ARENA_GUI_TYPE.UNKNOWN
}


def isDisabledByBattleType(exclude=None, include=tuple()):
    if not exclude:
        exclude = DEFAULT_EXCLUDED_GUI_TYPES
    if not hasattr(getPlayer(), 'arena') or getPlayer().arena is None:
        return False
    else:
        return True if getPlayer().arena.guiType in exclude and getPlayer().arena.guiType not in include else False
