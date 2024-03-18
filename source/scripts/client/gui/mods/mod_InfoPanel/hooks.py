# -*- coding: utf-8 -*-
from Avatar import PlayerAvatar
from constants import ARENA_BONUS_TYPE
from messenger import MessengerEntry

from DriftkingsCore import override, checkKeys, getPlayer
from .configs import g_config
from .data import g_mod  # , _isEntitySatisfiesConditions


@override(PlayerAvatar, 'targetBlur')
def new_targetBlur(func, self, prevEntity):
    player = getPlayer()
    if g_config.data['enabled'] and hasattr(prevEntity, 'publicInfo'):
        if not (g_config.data['enemiesOnly'] and 0 < getattr(prevEntity.publicInfo, 'team', 0) == player().team) or not (g_config.data['aliveOnly'] and not prevEntity.isAlive()):
            g_mod.updateBlur()
    # if g_config.data['enabled'] and hasattr(prevEntity, 'publicInfo'):
    #    enabledFor = g_config.data['showFor']
    #    isAlly = 0 < getattr(prevEntity.publicInfo, 'team', 0) == getPlayer().team
    #    showFor = (enabledFor == 0) or ((enabledFor == 1) and isAlly) or ((enabledFor == 2) and not isAlly)
    #    aliveOnly = (not g_config.data['aliveOnly']) or (g_config.data['aliveOnly'] and prevEntity.isAlive())
    #    g_mod.updateBlur()
    #    return showFor and aliveOnly
    func(self, prevEntity)


@override(PlayerAvatar, 'targetFocus')
def targetFocus(func, self, entity):
    func(self, entity)
    if not g_config.data['enabled'] or not hasattr(entity, 'publicInfo'):
        return
    if g_config.data['enemiesOnly']:
        player = getPlayer()
        return (0 < getattr(entity.publicInfo, 'team', 0) == player().team or g_config.data['aliveOnly'] and not entity.isAlive()) and None
    g_mod.update(entity)


# @override(PlayerAvatar, 'targetFocus')
# def new_targetFocus(func, self, entity):
#    func(self, entity)
#    if not (g_config.data['enabled'] and _isEntitySatisfiesConditions(entity)):
#        return
#    g_mod.update(entity)


# @override(PlayerAvatar, 'handleKey')
# def new_handleKey(func, self, isDown, key, mods):
#    func(self, isDown, key, mods)
#    if g_config.data['enabled'] or (key != checkKeys(g_config.data['altKey'])) or MessengerEntry.g_instance.gui.isFocused():
#        return
#    g_mod.handleKey(isDown)


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    if not g_config.data['enabled']:
        return
    if not getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        return
    g_mod.reset()
