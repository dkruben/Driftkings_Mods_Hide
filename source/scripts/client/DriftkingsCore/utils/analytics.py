# -*- coding: utf-8 -*-
"""
import threading
import googleanalytics as ga


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
"""
# -*- coding: utf-8 -*-
import threading
import json
import urllib2
import uuid

import BigWorld
from PlayerEvents import g_playerEvents

__all__ = ('Analytics',)


GA4_MEASUREMENT_ID = 'G-B7Z425MJ3L'
GA4_API_SECRET = '5687050102'
GA4_ENDPOINT = 'https://www.google-analytics.com/mp/collect'


class Analytics(object):
    def __init__(self, ID, version, confList=None):
        from .events import game
        self.ID = ID
        self.version = version
        self.confList = confList if confList else []
        self.modManager_started = False
        self._thread_modManager = None
        self.client_id = str(uuid.uuid4())
        g_playerEvents.onAccountShowGUI += self.start
        game.fini.before.event += self.end

    def modManagerStart(self):
        self.modManager_started = True
        self.trackEvent('session_start', {'mod_id': self.ID, 'mod_version': self.version})

    def start(self, *_, **__):
        if self._thread_modManager and self._thread_modManager.is_alive():
            return
        self._thread_modManager = threading.Thread(target=self.modManagerStart, name='mod_%s' % self.ID)
        self._thread_modManager.daemon = True
        self._thread_modManager.start()

    def end(self, *_, **__):
        if self.modManager_started:
            # Send session_end event
            self.trackEvent('session_end', {'mod_id': self.ID, 'mod_version': self.version})
            self.modManager_started = False
            if self._thread_modManager and self._thread_modManager.is_alive():
                self._thread_modManager.join(timeout=1.0)
                self._thread_modManager = None

    def trackEvent(self, eventName, eventParams=None):
        if not self.modManager_started:
            return
        try:
            # Create a new thread for sending the event to avoid blocking
            threading.Thread(target=self._send_ga_event, args=(eventName, eventParams), name='track_%s_%s' % (self.ID, eventName)).start()
        except Exception as e:
            pass

    def _send_ga_event(self, eventName, eventParams=None):
        try:
            payload = {'client_id': self.client_id, 'events': [{'name': eventName, 'params': eventParams or {}}]}
            payload['events'][0]['params'].update({'engagement_time_msec': '100', 'session_id': self.client_id})
            data = json.dumps(payload)
            url = '%s?measurement_id=%s&api_secret=%s' % (GA4_ENDPOINT, GA4_MEASUREMENT_ID, GA4_API_SECRET)
            req = urllib2.Request(url, data=data)
            req.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(req)
            if response.getcode() != 204:
                pass
        except Exception:
            pass