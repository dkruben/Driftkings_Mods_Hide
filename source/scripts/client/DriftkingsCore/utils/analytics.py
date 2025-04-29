# -*- coding: utf-8 -*-
import threading
import json
import urllib2
import uuid
import time
import traceback

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
        self.clientID = str(uuid.uuid4())
        g_playerEvents.onAccountShowGUI += self.start
        game.fini.before.event += self.end

    def modManagerStart(self):
        self.modManager_started = True
        self.trackEvent('mod_start', {'ID': self.ID, 'version': self.version})

    def start(self, *_, **__):
        if self._thread_modManager and self._thread_modManager.is_alive():
            return
        self._thread_modManager = threading.Thread(target=self.modManagerStart, name='mod_%s' % self.ID)
        self._thread_modManager.daemon = True
        self._thread_modManager.start()

    def end(self, *_, **__):
        if self.modManager_started:
            self.trackEvent('mod_end', {'ID': self.ID, 'version': self.version})
            self.modManager_started = False
            if self._thread_modManager and self._thread_modManager.is_alive():
                self._thread_modManager.join(timeout=1.0)
                self._thread_modManager = None

    def trackEvent(self, eventName, eventParams=None):
        if not self.modManager_started:
            return
        tracking_thread = threading.Thread(target=self._send_event, args=(eventName, eventParams), name='ga4_tracking_%s' % eventName)
        tracking_thread.daemon = True
        tracking_thread.start()

    def _send_event(self, eventName, eventParams=None):
        try:
            url = '{0}?measurement_id={1}&api_secret={2}'.format(GA4_ENDPOINT, GA4_MEASUREMENT_ID, GA4_API_SECRET)
            payload = {'client_id': self.clientID, 'events': [{'name': eventName, 'params': eventParams or {}}]}
            payload['events'][0]['params']['timestamp'] = int(time.time())
            payload['events'][0]['params']['ID'] = self.ID
            payload['events'][0]['params']['version'] = self.version
            data = json.dumps(payload)
            request = urllib2.Request(url, data=data)
            request.add_header('Content-Type', 'application/json')
            request.add_header('User-Agent', 'WoT-Mod/{0}-{1}'.format(self.ID, self.version))
            try:
                response = urllib2.urlopen(request, timeout=3)
                print('Analytics: Event "{0}" sent successfully'.format(eventName))
            except urllib2.URLError as e:
                print('Analytics: Failed to send event \'{0}\': {1}'.format(eventName, e.reason))
            except Exception as e:
                print('Analytics: Error sending event \'{0}\': {1}'.format(eventName, str(e)))
        except Exception:
            # Catch any exceptions to prevent the thread from crashing
            print('Analytics: Unexpected error in _send_ga4_event:')
            print(traceback.format_exc())