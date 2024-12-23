# -*- coding: utf-8 -*-
import copy

from Event import SafeEvent
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, WindowLayer, ScopeTemplates
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.shared.personality import ServicesLocator
from skeletons.gui.app_loader import GuiGlobalSpaceID


def smart_update(old_conf, new_conf):
    changed = False
    for k, old_v in old_conf.items():
        new_v = new_conf.get(k)
        if isinstance(new_v, dict) and isinstance(old_v, dict):
            changed |= smart_update(old_v, new_v)
        elif new_v is not None:
            if isinstance(new_v, unicode):
                new_v = new_v.encode('utf-8')
            if old_v != new_v:
                old_conf[k] = new_v
                changed = True

    # Add new keys from new_conf that are not in old_conf
    for k, v in new_conf.items():
        if k not in old_conf:
            old_conf[k] = v.encode('utf-8') if isinstance(v, unicode) else v
            changed = True
    return changed


class Cache(object):
    def __init__(self):
        self.items = {}
        g_events.create += self.__create
        g_events.update += self.__update
        g_events.delete += self.__delete

    def __create(self, linkage, config):
        if linkage not in self.items:
            self.items[linkage] = {'config': config, 'data': {}}

    def __update(self, linkage, data):
        if linkage in self.items:
            self.items[linkage]['data'] = data

    def __delete(self, linkage):
        if linkage in self.items:
            del self.items[linkage]


class Events(object):
    def __init__(self):
        self.create = SafeEvent()
        self.update = SafeEvent()
        self.delete = SafeEvent()
        self.onUIReady = SafeEvent()
        self.onBattleLoaded = SafeEvent()
        ServicesLocator.appLoader.onGUISpaceEntered += self.onGUISpaceEntered

    def onGUISpaceEntered(self, spaceID):
        if spaceID != GuiGlobalSpaceID.BATTLE:
            return
        app = ServicesLocator.appLoader.getDefBattleApp()
        if app is not None:
            app.loadView(SFViewLoadParams('Driftkings_PlayersPanelAPI_UI'))


class PlayersPanelUI(View):
    def _populate(self):
        # noinspection PyProtectedMember
        super(PlayersPanelUI, self)._populate()
        for linkage, data in g_cache.items.iteritems():
            self.as_createS(linkage, data['config'])
        g_events.create += self.as_createS
        g_events.update += self.as_updateS
        g_events.delete += self.as_deleteS
        g_events.onUIReady()

    def _dispose(self):
        g_events.create -= self.as_createS
        g_events.update -= self.as_updateS
        g_events.delete -= self.as_deleteS
        # noinspection PyProtectedMember
        super(PlayersPanelUI, self)._dispose()

    def as_createS(self, linkage, config):
        if self._isDAAPIInited():
            self.flashObject.as_create(linkage, config)

    def as_updateS(self, linkage, data):
        if self._isDAAPIInited():
            self.flashObject.as_update(linkage, data)

    def as_deleteS(self, linkage):
        if self._isDAAPIInited():
            self.flashObject.as_delete(linkage)


# noinspection PyArgumentList
g_entitiesFactories.addSettings(ViewSettings('Driftkings_PlayersPanelAPI_UI', PlayersPanelUI, 'DriftkingsPlayersPanelAPI.swf', WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))

g_events = Events()
g_cache = Cache()

LABEL_CONFIG = {
    'isHtml': True,
    'left': {
        'x': 0,
        'y': 0,
        'height': 24,
        'width': 100,
        'align': 'left'
    },
    'right': {
        'x': 0,
        'y': 0,
        'height': 24,
        'width': 100,
        'align': 'right'
    },
    'shadow': {
        'distance': 0,
        'angle': 0,
        'color': "#000000",
        'alpha': 90,
        'blurX': 2,
        'blurY': 2,
        'strength': 2,
        'quality': 2
    }
}


class PlayersPanelAPI(object):
    events = g_events

    def create(self, linkage, config):
        conf = copy.deepcopy(LABEL_CONFIG)
        smart_update(conf, config)
        g_events.create(linkage, conf)

    def update(self, linkage, data):
        g_events.update(linkage, data)

    def delete(self, linkage):
        g_events.delete(linkage)


g_driftkingsPlayersPanels = PlayersPanelAPI()
