# -*- coding: utf-8 -*-
import BigWorld
import Keys
import game
from Vehicle import Vehicle
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID as _FET
from gui.battle_control.controllers.feedback_adaptor import BattleFeedbackAdaptor
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader

from DriftkingsCore import SimpleConfigInterface, Analytics, override


class ConfigInterface(SimpleConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = '(orig: MakcT40)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.defaultKeys = {'key': [Keys.KEY_N]}
        self.data = {
            'enabled': True,
            'key': self.defaultKeys['key'],
            'marker': False,
            'proxy': None,
            'arenaDP': None
        }

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createHotKey('key'),
                self.tb.createControl('marker')
            ],
            'column2': []}


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(BattleFeedbackAdaptor, 'startVehicleVisual')
def BattleFeedbackAdaptor_startVehicleVisual(func, self, vProxy, isImmediate=False):
    func(self, vProxy, isImmediate)
    if vProxy.isPlayerVehicle:
        config.data['proxy'] = vProxy
        config.data['arenaDP'] = self._BattleFeedbackAdaptor__arenaDP
        vInfo = config.data['arenaDP'].getVehicleInfo(vProxy.id)
        if config.data['enabled']:
            self.onVehicleMarkerAdded(vProxy, vInfo, config.data['arenaDP'].getPlayerGuiProps(vProxy.id, vInfo.team))
            config.data['marker'] = True


@override(BattleFeedbackAdaptor, 'stopVehicleVisual')
def BattleFeedbackAdaptor_stopVehicleVisual(func, self, vehicleID, isPlayerVehicle):
    func(self, vehicleID, isPlayerVehicle)
    if isPlayerVehicle and config.data['marker']:
        self.onVehicleMarkerRemoved(vehicleID)
        config.data['marker'] = False
    return


@override(Vehicle, '_Vehicle__onVehicleDeath')
def Vehicle__onVehicleDeath(func, self, isDeadStarted=False):
    func(self, isDeadStarted)
    if self.isPlayerVehicle and config.data['marker']:
        self.guiSessionProvider.shared.feedback.onVehicleFeedbackReceived(_FET.VEHICLE_DEAD, self.id, isDeadStarted)


@override(Vehicle, 'onHealthChanged')
def Vehicle_onHealthChanged(func, self, newHealth, oldHealth, attackerID, attackReasonID):
    func(self, newHealth, oldHealth, attackerID, attackReasonID)
    if self.isPlayerVehicle and config.data['marker']:
        self.guiSessionProvider.shared.feedback.setVehicleNewHealth(self.id, newHealth, attackerID, attackReasonID)


@override(game, 'handleKeyEvent')
def game_handleKeyEvent(func, self, event):
    func(self, event)
    isDown, key, mods, isRepeat = game.convertKeyEvent(event)
    if mods == 0 and isDown and config.data['proxy'] is not None:
        app = dependency.instance(IAppLoader)
        player = BigWorld.player()
        if key == config.data['key'] and app.getDefBattleApp() and player.inputHandler.isGuiVisible:
            if config.data['marker']:
                player.guiSessionProvider.shared.feedback.onVehicleMarkerRemoved(config.data['proxy'].id)
                config.data['marker'] = False
            else:
                vInfo = config.data['arenaDP'].getVehicleInfo(config.data['proxy'].id)
                player.guiSessionProvider.shared.feedback.onVehicleMarkerAdded(config.data['proxy'], vInfo, config.data['arenaDP'].getPlayerGuiProps(config.data['proxy'].id, vInfo.team))
                config.data['marker'] = True
