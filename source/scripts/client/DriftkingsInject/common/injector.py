# -*- coding: utf-8 -*-
from gui.Scaleform.framework.entities.DisposableEntity import EntityState
from gui.Scaleform.framework.entities.View import View

from .events import g_events


class DriftkingsInjector(View):

    def _populate(self):
        # noinspection PyProtectedMember
        super(DriftkingsInjector, self)._populate()
        g_events.onBattleClosed += self.destroy

    def _dispose(self):
        g_events.onBattleClosed -= self.destroy
        # noinspection PyProtectedMember
        super(DriftkingsInjector, self)._dispose()

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            return
        super(DriftkingsInjector, self).destroy()
