# -*- coding: utf-8 -*-
import BigWorld

from . import ModEvent

__all__ = ('populate',)

populate = ModEvent()


def delayed_hooks():
    global populate
    from .. import override
    from gui.Scaleform.daapi.view.login.LoginView import LoginView
    populate = override(LoginView, '_populate', populate)


BigWorld.callback(0, delayed_hooks)
