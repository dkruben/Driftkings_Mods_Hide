# -*- coding: utf-8 -*-
import BigWorld

from . import ModEvent

__all__ = ('startGUI', 'destroyGUI')

startGUI = ModEvent()
destroyGUI = ModEvent()


def delayed_hooks():
    global startGUI, destroyGUI
    from Avatar import PlayerAvatar
    from .. import override
    startGUI = override(PlayerAvatar, '__startGUI', startGUI)
    destroyGUI = override(PlayerAvatar, '__destroyGUI', destroyGUI)


BigWorld.callback(0, delayed_hooks)
