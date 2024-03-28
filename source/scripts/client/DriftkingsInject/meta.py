# -*- coding: utf-8 -*-
from account_helpers.settings_core.settings_constants import GRAPHICS
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.DisposableEntity import EntityState
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import logDebug, logInfo
from common import g_events


class DriftkingsView(BaseDAAPIComponent):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self, ID):
        super(DriftkingsView, self).__init__()
        self.ID = ID
        self._arenaDP = self.sessionProvider.getArenaDP()
        self._arenaVisitor = self.sessionProvider.arenaVisitor

    @property
    def gui(self):
        return self._arenaVisitor.gui

    def isSPG(self):
        return self.getVehicleInfo().isSPG()

    def getVehicleInfo(self, vID=None):
        return self._arenaDP.getVehicleInfo(vID)

    def getColors(self):
        pass

    def getSettings(self):
        pass

    def getShadowSettings(self):
        pass

    @staticmethod
    def getVehicleClassColors():
        pass

    @staticmethod
    def getVehicleClassColor(classTag):
        pass

    def doLog(self, *args):
        for arg in args:
            logInfo('%s:%s - %s' % (self.getAlias(), arg, dir(arg)))

    def _populate(self):
        # noinspection PyProtectedMember
        super(DriftkingsView, self)._populate()
        g_events.onBattleClosed += self.destroy
        logDebug(True, '\'%s\' is loaded' % self.ID)

    def _dispose(self):
        g_events.onBattleClosed -= self.destroy
        # noinspection PyProtectedMember
        super(DriftkingsView, self)._dispose()
        logDebug(True, '\'%s\' is closed' % self.ID)

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            return
        super(DriftkingsView, self).destroy()

    @property
    def playerVehicleID(self):
        return self._arenaDP.getPlayerVehicleID()

    @property
    def isPlayerVehicle(self):
        vehicle = self.sessionProvider.shared.vehicleState.getControllingVehicle()
        if vehicle is not None:
            return vehicle.id == self.playerVehicleID
        observed_veh_id = self.sessionProvider.shared.vehicleState.getControllingVehicleID()
        return self.playerVehicleID == observed_veh_id or observed_veh_id == 0

    def isColorBlind(self):
        return bool(self.settingsCore.getSetting(GRAPHICS.COLOR_BLIND))

    def as_startUpdateS(self, *args):
        return self.flashObject.as_startUpdate(*args) if self._isDAAPIInited() else None

    def as_colorBlindS(self, enabled):
        return self.flashObject.as_colorBlind(enabled) if self._isDAAPIInited() else None

    def as_onCrosshairPositionChangedS(self, x, y):
        return self.flashObject.as_onCrosshairPositionChanged(x, y) if self._isDAAPIInited() else None
