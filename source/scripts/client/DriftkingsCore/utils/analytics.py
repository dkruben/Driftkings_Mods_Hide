# -*- coding: utf-8 -*-
import threading

import BigWorld
from PlayerEvents import g_playerEvents

__all__ = ('Analytics',)

# GA4_MEASUREMENT_ID = 'G-B7Z425MJ3L'
# GA4_API_SECRET = '5687050102'
# GA4_ENDPOINT = 'https://www.google-analytics.com/mp/collect'


class Analytics(object):
    def __init__(self, ID, version, confList=None):
        from .events import game
        self.ID = ID
        self.version = version
        self.confList = confList if confList else []
        self.modManager_started = False
        self._thread_modManager = None
        g_playerEvents.onAccountShowGUI += self.start
        game.fini.before.event += self.end

    def modManagerStart(self):
        self.modManager_started = True

    def start(self, *_, **__):
        if self._thread_modManager and self._thread_modManager.is_alive():
            return
        self._thread_modManager = threading.Thread(target=self.modManagerStart, name='mod_%s' % self.ID)
        self._thread_modManager.daemon = True
        self._thread_modManager.start()

    def end(self, *_, **__):
        if self.modManager_started:
            self.modManager_started = False
            if self._thread_modManager and self._thread_modManager.is_alive():
                self._thread_modManager.join(timeout=1.0)
                self._thread_modManager = None

    def trackEvent(self, eventName, eventParams=None):
        pass