# -*- coding: utf-8 -*-
import copy
import sys
import traceback

import BigWorld
import Event
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

from DriftkingsCore import override, logError, logWarning

__all__ = ('g_driftkingsPlayersPanels',)


class DriftkingsPlayersPanelMeta(BaseDAAPIComponent):

    @staticmethod
    def logInfo(name, message, *args):
        print '%s: %s %s' % (name, message, args)

    # noinspection PyProtectedMember
    def _populate(self):
        super(DriftkingsPlayersPanelMeta, self)._populate()
        g_driftkingsPlayersPanels._populate(self)

    # noinspection PyProtectedMember
    def _dispose(self):
        g_driftkingsPlayersPanels._dispose(self)
        super(DriftkingsPlayersPanelMeta, self)._dispose()

    def flashLogS(self, *args):
        self.logInfo('DriftkingsPlayersPanelAPI: ', args)
        return True

    def as_createS(self, linkage, config):
        return self.flashObject.as_create(linkage, config) if self._isDAAPIInited() else None

    def as_updateS(self, linkage, data):
        return self.flashObject.as_update(linkage, data) if self._isDAAPIInited() else None

    def as_deleteS(self, linkage):
        return self.flashObject.as_delete(linkage) if self._isDAAPIInited() else None

    def as_updatePositionS(self, linkage, vehicleID):
        return self.flashObject.as_updatePosition(linkage, vehicleID) if self._isDAAPIInited() else None

    def as_shadowListItemS(self, shadow):
        return self.flashObject.as_shadowListItem(shadow) if self._isDAAPIInited() else None

    def as_extendedSettingS(self, linkage, vehicleID):
        return self.flashObject.extendedSetting(linkage, vehicleID) if self._isDAAPIInited() else None

    def as_getPPListItemS(self, vehicleID):
        return self.flashObject.as_getPPListItem(vehicleID) if self._isDAAPIInited() else None

    def as_hasOwnPropertyS(self, linkage):
        return self.flashObject.as_hasOwnProperty(linkage) if self._isDAAPIInited() else None

    def as_vehicleIconColorS(self, vehicleID, color):
        return self.flashObject.as_vehicleIconColor(vehicleID, color) if self._isDAAPIInited() else None


class PlayersPanelAPI(object):

    def __init__(self):
        self.impl = False
        self.viewLoad = False
        self.componentUI = None
        self.onUIReady = Event.Event()
        self.updateMode = Event.Event()
        try:
            self.applyOverride(PlayersPanel, 'setInitialMode', self.setInitialMode)
            self.applyOverride(PlayersPanel, 'setLargeMode', self.setLargeMode)
            self.applyOverride(PlayersPanel, '_handleNextMode', self.handleNextMode)
            self.applyOverride(PlayersPanel, '_PlayersPanel__handleShowExtendedInfo', self.handleShowExtendedInfo)
            self.applyOverride(PlayersPanelMeta, 'as_setPanelModeS', self.setPanelMode)
            self.applyOverride(PlayersPanel, 'as_setPanelModeS', self.setPanelMode)
            self.applyOverride(PlayersPanel, 'tryToSetPanelModeByMouse', self.tryToSetPanelModeByMouse)
            self.applyOverride(PlayersPanelMeta, 'tryToSetPanelModeByMouse', self.tryToSetPanelModeByMouse)
            self.applyOverride(BattleStatisticsDataController, 'updateVehiclesInfo', self.updateVehicles)
            self.applyOverride(BattleStatisticsDataController, 'updateVehiclesStats', self.updateVehicles)
        except Exception as err:
            logError('[DriftkingsPlayersPanelAPI]:', 'Error in applying overrides: {}'.format(str(err)))
            traceback.print_exc()

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
                'color': '#000000',
                'alpha': 90,
                'blurX': 2,
                'blurY': 2,
                'strength': 2,
                'quality': 2
            }
        }

    @staticmethod
    def applyOverride(cls, methodName, newMethod):
        try:
            if not isinstance(methodName, str) and not (sys.version_info[0] == 2 and isinstance(methodName, unicode)):
                logWarning('[DriftkingsPlayersPanelAPI]:', 'Method name is not a string: {}'.format(repr(methodName)))
                if methodName is None:
                    logError('[DriftkingsPlayersPanelAPI]:', 'Cannot override with None method name')
                    return
                try:
                    methodName = str(methodName)
                except:
                    logError('[DriftkingsPlayersPanelAPI]:', 'Failed to convert method name to string: {}'.format(repr(methodName)))
                    return
            if not hasattr(cls, methodName):
                logWarning('[DriftkingsPlayersPanelAPI]:', 'Method {} not found in class {}'.format(methodName, cls.__name__))
                return
            override(cls, methodName, newMethod)
        except Exception as err:
            logError('[DriftkingsPlayersPanelAPI]:', 'Failed to override {}.{}: {}'.format(cls.__name__, methodName, str(err)))
            traceback.print_exc()

    def smartUpdate(self, old_setting, new_setting):
        changed = False
        for k in old_setting:
            v = new_setting.get(k)
            if isinstance(v, dict):
                changed |= self.smartUpdate(old_setting[k], v)
            if v is not None:
                if sys.version_info[0] == 2 and isinstance(v, unicode):
                    v = v.encode('utf-8')
                elif sys.version_info[0] == 3 and isinstance(v, str):
                    v = v.encode('utf-8').decode('utf-8')
                changed |= old_setting[k] != v
                old_setting[k] = v
        return changed

    def updateVehicles(self, func, orig, updated, arenaDP):
        func(orig, updated, arenaDP)
        if self.impl:
            self.updateMode()

    def setInitialMode(self, func, orig):
        func(orig)
        if self.impl:
            self.updateMode()

    def setLargeMode(self, func, orig):
        func(orig)
        if self.impl:
            self.updateMode()

    def handleNextMode(self, func, orig, event):
        func(orig, event)
        if self.impl:
            self.updateMode()

    def handleShowExtendedInfo(self, func, orig, event):
        func(orig, event)
        if self.impl:
            self.updateMode()

    def tryToSetPanelModeByMouse(self, func, orig, mode):
        func(orig, mode)
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

    def create(self, linkage, config=None):
        if not self.componentUI:
            return None
        else:
            conf = copy.deepcopy(self.config)
            if config:
                self.smartUpdate(conf, config)
            return self.componentUI.as_createS(linkage, conf)

    def update(self, linkage, data):
        if not self.componentUI:
            return None
        else:
            if 'text' in data and data['text']:
                data['text'] = data['text'].replace('$IMELanguageBar', '$FieldFont')
            return self.componentUI.as_updateS(linkage, data)

    def delete(self, linkage):
        return self.componentUI.as_deleteS(linkage) if self.componentUI else None

    def shadowListItem(self, shadow):
        return self.componentUI.as_shadowListItemS(shadow) if self.componentUI else None

    def hasOwnProperty(self, linkage):
        return self.componentUI.as_hasOwnPropertyS(linkage) if self.componentUI else None

    def vehicleIconColor(self, vehicleID, color):
        return self.componentUI.as_vehicleIconColorS(vehicleID, color) if self.componentUI else None

    def extendedSetting(self, linkage, vehicleID):
        return self.componentUI.as_extendedSettingS(linkage, vehicleID) if self.componentUI else None

    def getPPListItem(self, vehicleID):
        return self.componentUI.as_getPPListItemS(vehicleID) if self.componentUI else None

    def updatePosition(self, linkage, vehicleID):
        return self.componentUI.as_updatePositionS(linkage, vehicleID) if self.componentUI else None

    def onComponentRegistered(self, event):
        if event.alias != BATTLE_VIEW_ALIASES.PLAYERS_PANEL:
            return
        try:
            player = BigWorld.player()
            if not player or not hasattr(player, 'guiSessionProvider'):
                return
            gui_session = player.guiSessionProvider
            if not gui_session or not hasattr(gui_session, 'arenaVisitor'):
                return
            arena_visitor = gui_session.arenaVisitor.gui
            if not arena_visitor:
                return
            if arena_visitor.isEpicRandomBattle() or arena_visitor.isBattleRoyale():
                return
            self.impl = True
            app = ServicesLocator.appLoader.getDefBattleApp()
            if app:
                app.loadView(SFViewLoadParams('DriftkingsPlayersPanelUI', 'DriftkingsPlayersPanelUI'), {})
        except (AttributeError, TypeError) as err:
            logError('[DriftkingsPlayersPanelAPI]', 'Error in onComponentRegistered: {}'.format(str(err)))
            self.impl = False


if not g_entitiesFactories.getSettings('DriftkingsPlayersPanelUI'):
    try:
        g_driftkingsPlayersPanels = PlayersPanelAPI()
        g_entitiesFactories.addSettings(ViewSettings('DriftkingsPlayersPanelUI', View, 'DriftkingsPlayersPanelAPI.swf', WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
        g_entitiesFactories.addSettings(ComponentSettings('DriftkingsPlayersPanelAPI', DriftkingsPlayersPanelMeta, ScopeTemplates.DEFAULT_SCOPE))
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED, g_driftkingsPlayersPanels.onComponentRegistered, scope=EVENT_BUS_SCOPE.GLOBAL)
    except Exception as e:
        logError('[DriftkingsPlayersPanelAPI]', 'Failed to initialize PlayersPanelAPI: {}'.format(str(e)))
        traceback.print_exc()
