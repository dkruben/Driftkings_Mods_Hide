# -*- coding: utf-8 -*-
from Avatar import PlayerAvatar
from gui.shared.gui_items import Vehicle

from DriftkingsCore import SimpleConfigInterface, override, Analytics, callback, getPlayer, sendPanelMessage


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (spoter mods)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'lightTank': False,
            'mediumTank': False,
            'heavyTank': False,
            'SPG': True,
            'AT-SPG': False,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': sum(int(x) * (10 ** i) for i, x in enumerate(reversed(self.version.split(' ')[0].split('.')))),
            'UI_setting_lightTank_text': 'to LT',
            'UI_setting_lightTank_tooltip': '',
            'UI_setting_mediumTank_text': 'to MT',
            'UI_setting_mediumTank_tooltip': '',
            'UI_setting_heavyTank_text': 'to HT',
            'UI_setting_heavyTank_tooltip': '',
            'UI_setting_SPG_text': 'to Arty',
            'UI_setting_SPG_tooltip': '',
            'UI_setting_AT-SPG_text': 'to AT',
            'UI_setting_AT-SPG_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('lightTank'),
                self.tb.createControl('mediumTank'),
                self.tb.createControl('heavyTank'),
                self.tb.createControl('SPG'),
                self.tb.createControl('AT-SPG')
            ],
            'column2': []
        }

    def waitCallback(self):
        if self.data['enabled']:
            getPlayer()
            if not getPlayer():
                return
            try:
                vehicleType = Vehicle.getVehicleClassTag(getPlayer().getVehicleDescriptor().type.tags)
            except StandardError:
                vehicleType = None
            showServerMarker = vehicleType in self.data and self.data[vehicleType]
            if self.checkServerAimStatus(showServerMarker) and showServerMarker:
                sendPanelMessage('{0}: {1}'.format(self.i18n['UI_description'], self.i18n['UI_setting_%s_text' % vehicleType]))

    def startBattle(self):
        self.checkServerAimStatus()
        callback(5.0, self.waitCallback)

    def endBattle(self):
        self.checkServerAimStatus()

    def checkServerAimStatus(self, showServerMarker=None):
        if not getPlayer() or not self.data['enabled']:
            return
        try:
            if showServerMarker is None:
                showServerMarker = getPlayer().gunRotator.settingsCore.getSetting('useServerAim')
            getPlayer().gunRotator.showServerMarker = showServerMarker
            # noinspection PyProtectedMember
            getPlayer().gunRotator._VehicleGunRotator__set_showServerMarker(showServerMarker)
            return True
        except StandardError:
            return


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    config.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    config.endBattle()
    func(*args)
