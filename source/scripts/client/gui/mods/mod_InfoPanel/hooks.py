# -*- coding: utf-8 -*-
from Avatar import PlayerAvatar
from constants import ARENA_BONUS_TYPE
from messenger import MessengerEntry

from DriftkingsCore import override, checkKeys, getPlayer
from .configs import g_config
from .data import g_mod, _isEntitySatisfiesConditions


@override(PlayerAvatar, 'targetBlur')
def new__targetBlur(base, self, prevEntity):
    if g_config.data['enabled'] and _isEntitySatisfiesConditions(prevEntity):
        g_mod.updateBlur()
    base(self, prevEntity)


@override(PlayerAvatar, 'targetFocus')
def new_targetFocus(func, self, entity):
    func(self, entity)
    if not (g_config.data['enabled'] and _isEntitySatisfiesConditions(entity)):
        return
    g_mod.update(entity)


@override(PlayerAvatar, 'handleKey')
def new_handleKey(func, self, isDown, key, mods):
    func(self, isDown, key, mods)
    if g_config.data['enabled'] or (key != checkKeys(g_config.data['altKey'])) or MessengerEntry.g_instance.gui.isFocused():
        return
    g_mod.handleKey(isDown)


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    if not g_config.data['enabled']:
        return
    if not getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        return
    g_mod.reset()
