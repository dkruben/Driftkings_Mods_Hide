# -*- coding: utf-8 -*-
import threading

import BigWorld
from PlayerEvents import g_playerEvents

__all__ = ('Analytics',)


class Analytics(object):
    def __init__(self, ID, version, confList=None):
        from .events import game
        self.mod_id = ID
        self.mod_version = version
        self.confList = confList if confList else []
        self.modManager_started = False
        self._thread_modManager = None
        g_playerEvents.onAccountShowGUI += self.start
        game.fini.before.event += self.end

    def modManager_start(self):
        """Initialize the mod manager functionality"""
        self.modManager_started = True

    def start(self, *_, **__):
        """Start the mod manager in a separate thread when account GUI is shown"""
        if self._thread_modManager and self._thread_modManager.is_alive():
            return
        self._thread_modManager = threading.Thread(target=self.modManager_start, name='mod_%s' % self.mod_id)
        self._thread_modManager.daemon = True
        self._thread_modManager.start()

    def end(self, *_, **__):
        """Clean up resources when game is finishing"""
        if self.modManager_started:
            self.modManager_started = False
            if self._thread_modManager and self._thread_modManager.is_alive():
                self._thread_modManager.join(timeout=1.0)
                self._thread_modManager = None
