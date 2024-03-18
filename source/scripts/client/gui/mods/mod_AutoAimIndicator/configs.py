# -*- coding: utf-8 -*-
from collections import OrderedDict

import BattleReplay
import BigWorld
from BattleReplay import CallbackDataNames
from PlayerEvents import g_playerEvents
from Vehicle import Vehicle
from constants import ARENA_GUI_TYPE
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import GameEvent

from DriftkingsCore import SimpleConfigInterface, isDisabledByBattleType, getPlayer
from indicator import IndicatorsCtrl


class ConfigInterface(SimpleConfigInterface):

    def __init__(self):
        self.cfg = {}
        self.colors_config = OrderedDict([
            ('wg_blur', '#8378FC'),
            ('wg_enemy', '#DB0400'),
            ('wg_friend', '#80D639'),
            ('wg_squad', '#FFB964')])
        self._colors = ['wg_enemy', 'wg_blur', 'wg_friend', 'wg_squad']
        self.model_path = 'mods/mod_AutoAimIndicator/objects/%s/marker.model'
        self.vehicleID = None
        self.isReplayCBAdded = False
        self.player = None
        self.indicator = None
        super(ConfigInterface, self).__init__()
        g_playerEvents.onAvatarBecomePlayer += self.start
        g_playerEvents.onAvatarBecomeNonPlayer += self.stop
        g_eventBus.addListener(GameEvent.ON_TARGET_VEHICLE_CHANGED, self._handleAutoAimMarker, scope=EVENT_BUS_SCOPE.BATTLE)

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'

        self.data = {
            'enabled': True,
            'isModel': True,
            'colour': 0
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_colour_text': 'AutoAim Colour',
            'UI_setting_colour_tooltip': '',
            'UI_setting_isModel_text': 'Is Model',
            'UI_setting_isModel_tooltip': '',

            'wg_blur': 'WG Color blind',
            'wg_enemy': 'WG Enemy',
            'wg_friend': 'WG Ally',
            'wg_squad': 'WG SquadMan'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        textExamples = []
        colourDropdown = self.tb.createOptions('colour', ('<font color=\'%s\'>%s</font>' % (x[1], self.i18n[x[0]]) for x in self.colors_config.iteritems()))
        colourDropdown['tooltip'] = colourDropdown['tooltip'].replace('{/BODY}', '\n'.join(textExamples) + '{/BODY}')
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('isModel')
            ],
            'column2': [
                colourDropdown
            ]
        }

    def readData(self, quiet=True):
        super(ConfigInterface, self).readData(quiet=True)
        if self.colors_config.keys():
            self.cfg['model'] = self.model_path % self._colors[self.data['colour']]
            self.indicator = IndicatorsCtrl(self.cfg['model'], self.data['isModel'])

    @property
    def isEnabled(self):
        return self.data['enabled'] and not isDisabledByBattleType(include=(ARENA_GUI_TYPE.EPIC_BATTLE, ARENA_GUI_TYPE.EPIC_RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING, ARENA_GUI_TYPE.EPIC_TRAINING))

    def isAlly(self, vehicle):
        self.player = getPlayer()
        vehicles = self.player.arena.vehicles
        vehicleID = vehicle.id if isinstance(vehicle, BigWorld.Entity) else vehicle
        return vehicleID in vehicles and vehicles[self.player.playerVehicleID]['team'] == vehicles[vehicleID]['team']

    def start(self):
        if not self.isReplayCBAdded:
            if BattleReplay.g_replayCtrl.isPlaying:
                BattleReplay.g_replayCtrl.setDataCallback(CallbackDataNames.SHOW_AUTO_AIM_MARKER, self.show)
                BattleReplay.g_replayCtrl.setDataCallback(CallbackDataNames.HIDE_AUTO_AIM_MARKER, self.hide)
        if self.isEnabled:
            self.indicator.onStart()
            self.indicator.onCreate()
            self.hide()

    def stop(self):
        if self.isEnabled:
            self.hide()
            self.indicator.onDestroy()
            self.indicator.onStop()

    def show(self, vehicleID):
        self.hide()
        if self.isEnabled and self.vehicleID != vehicleID:
            vehicle = BigWorld.entity(vehicleID)
            if isinstance(vehicle, Vehicle) and vehicle.isStarted and vehicle.isAlive() and not self.isAlly(vehicle):
                self.vehicleID = vehicleID
                self.indicator.onShow(vehicle)

    def hide(self, *_):
        self.vehicleID = None
        if self.isEnabled:
            self.indicator.onHide()

    def _handleAutoAimMarker(self, event):
        vehicleID = event.ctx.get('vehicleID')
        if vehicleID is not None and vehicleID != 0:
            self.show(vehicleID)
        else:
            self.hide()


g_config = ConfigInterface()
