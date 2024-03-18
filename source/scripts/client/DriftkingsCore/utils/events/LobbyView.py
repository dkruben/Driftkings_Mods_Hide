# -*- coding: utf-8 -*-
import BigWorld

from . import ModEvent

__all__ = ('populate',)

populate = ModEvent()


def delayed_hooks():
    global populate
    from .. import override
    from gui.Scaleform.daapi.view.lobby.LobbyView import LobbyView
    populate = override(LobbyView, '_populate', populate)


BigWorld.callback(0, delayed_hooks)
