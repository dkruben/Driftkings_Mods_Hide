# -*- coding: utf-8 -*-
import copy

import Event
from Avatar import PlayerAvatar
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.battle.classic.players_panel import PlayersPanel
from gui.Scaleform.daapi.view.battle.shared.stats_exchange.stats_ctrl import BattleStatisticsDataController
from gui.Scaleform.daapi.view.meta.PlayersPanelMeta import PlayersPanelMeta
from gui.Scaleform.framework import g_entitiesFactories, ScopeTemplates, ViewSettings, ComponentSettings
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.shared import events, g_eventBus, EVENT_BUS_SCOPE
from gui.shared.personality import ServicesLocator
from helpers import getShortClientVersion

from DriftkingsCore import override, smart_update, getPlayer


class DriftkingsPlayersPanelMeta(BaseDAAPIComponent):

    def _populate(self):
        # noinspection PyProtectedMember
        super(DriftkingsPlayersPanelMeta, self)._populate()
        g_driftkingsPlayersPanels._populate(self)

    def _dispose(self):
        g_driftkingsPlayersPanels._dispose(self)
        # noinspection PyProtectedMember
        super(DriftkingsPlayersPanelMeta, self)._dispose()

    def flashLogS(self, *args):
        print('DriftkingsPlayersPanelUI: %s', args)

    def as_createS(self, container, config):
        return self.flashObject.as_create(container, config) if self._isDAAPIInited() else None

    def as_updateS(self, container, data):
        return self.flashObject.as_update(container, data) if self._isDAAPIInited() else None

    def as_deleteS(self, container):
        return self.flashObject.as_delete(container) if self._isDAAPIInited() else None

    def as_updatePositionS(self, container, vehicleID):
        return self.flashObject.as_updatePosition(container, vehicleID) if self._isDAAPIInited() else None

    def as_shadowListItemS(self, shadow):
        return self.flashObject.as_shadowListItem(shadow) if self._isDAAPIInited() else None

    def as_extendedSettingS(self, container, vehicleID):
        return self.flashObject.extendedSetting(container, vehicleID) if self._isDAAPIInited() else None

    def as_getPPListItemS(self, vehicleID):
        return self.flashObject.as_getPPListItem(vehicleID) if self._isDAAPIInited() else None

    def as_hasOwnPropertyS(self, container):
        return self.flashObject.as_hasOwnProperty(container) if self._isDAAPIInited() else None

    def as_vehicleIconColorS(self, vehicleID, color):
        return self.flashObject.as_vehicleIconColor(vehicleID, color) if self._isDAAPIInited() else None


class Events(object):
    def __init__(self):
        self.impl = False
        self.viewLoad = False
        self.componentUI = None
        self.onUIReady = Event.Event()
        self.updateMode = Event.Event()
        override(PlayersPanel, 'setInitialMode', self.setInitialMode)
        override(PlayersPanel, 'setLargeMode', self.setInitialMode)
        override(PlayersPanel, '_handleNextMode', self.setPanelMode)
        override(PlayersPanel, '_PlayersPanel__handleShowExtendedInfo', self.setPanelMode)
        override(PlayersPanelMeta, 'as_setPanelModeS', self.setPanelMode)
        override(PlayersPanel, 'as_setPanelModeS', self.setPanelMode)
        override(PlayersPanel, 'tryToSetPanelModeByMouse', self.setPanelMode)
        override(PlayersPanelMeta, 'tryToSetPanelModeByMouse', self.setPanelMode)
        override(BattleStatisticsDataController, 'updateVehiclesInfo', self.updateVehicles)
        override(BattleStatisticsDataController, 'updateVehiclesStats', self.updateVehicles)
        self.config = {
            'child': 'vehicleTF',
            'holder': 'vehicleIcon',
            'isHtml': True,
            'left': {
                'x': 0,
                'y': 0,
                'align': 'left',
                'height': 24,
                'width': 100
            },
            'right': {
                'x': 0,
                'y': 0,
                'align': 'right',
                'height': 24,
                'width': 100
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

    def updateVehicles(self, func, orig, updated, arenaDP):
        func(orig, updated, arenaDP)
        if self.impl:
            self.updateMode()

    def setInitialMode(self, func, orig):
        func(orig)
        if self.impl:
            self.updateMode()

    def setPanelMode(self, func, orig, value):
        func(orig, value)
        if self.impl:
            self.updateMode()

    def _populate(self, orig):
        self.viewLoad = True
        self.componentUI = orig
        self.onUIReady(self, 'DriftkingsPlayersPanelUI', orig)

    def _dispose(self, _):
        self.impl = False
        self.viewLoad = False
        self.componentUI = None

    def create(self, container, config=None):
        if not self.componentUI:
            return None
        conf = copy.deepcopy(self.config)
        if config:
            smart_update(conf, config)
        return self.componentUI.as_createS(container, conf)

    def update(self, container, data):
        if not self.componentUI:
            return None
        if 'text' in data:
            data['text'] = data['text'].replace('$IMELanguageBar', '$FieldFont')
        return self.componentUI.as_updateS(container, data)

    def delete(self, container):
        return self.componentUI.as_deleteS(container) if self.componentUI else None

    def shadowListItem(self, shadow):
        return self.componentUI.as_shadowListItemS(shadow) if self.componentUI else None

    def hasOwnProperty(self, container):
        return self.componentUI.as_hasOwnPropertyS(container) if self.componentUI else None

    def vehicleIconColor(self, vehicleID, color):
        return self.componentUI.as_vehicleIconColorS(vehicleID, color) if self.componentUI else None

    def extendedSetting(self, container, vehicleID):
        return self.componentUI.as_extendedSettingS(container, vehicleID) if self.componentUI else None

    def getPPListItem(self, vehicleID):
        return self.componentUI.as_getPPListItemS(vehicleID) if self.componentUI else None

    def updatePosition(self, container, vehicleID):
        return self.componentUI.as_updatePositionS(container, vehicleID) if self.componentUI else None

    def onComponentRegistered(self, event):
        if event.alias != BATTLE_VIEW_ALIASES.PLAYERS_PANEL:
            return
        arena_visitor = getPlayer().guiSessionProvider.arenaVisitor.gui
        if arena_visitor.isEpicRandomBattle() or arena_visitor.isBattleRoyale():
            return
        self.impl = True
        app = ServicesLocator.appLoader.getDefBattleApp()
        app.loadView(SFViewLoadParams('DriftkingsPlayersPanelUI', 'DriftkingsPlayersPanelUI'), {})


if not g_entitiesFactories.getSettings('DriftkingsPlayersPanelUI'):
    g_driftkingsPlayersPanels = Events()
    g_entitiesFactories.addSettings(ViewSettings('DriftkingsPlayersPanelUI', View, 'DriftkingsPlayersPanelAPI_V2.swf', WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
    g_entitiesFactories.addSettings(ComponentSettings('DriftkingsPlayersPanelAPI', DriftkingsPlayersPanelMeta, ScopeTemplates.DEFAULT_SCOPE))
    g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED, g_driftkingsPlayersPanels.onComponentRegistered, scope=EVENT_BUS_SCOPE.GLOBAL)
