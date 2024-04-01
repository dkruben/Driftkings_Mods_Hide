# -*- coding: utf-8 -*-
import traceback

from core import ConfigClass

MODS_LIST = ['ArcadeZoom', 'ArmorCalculator', 'ArtySplash', 'AutoAimOptimize', 'BanksLoader', 'BattleEfficiency', 'BattleMessages', 'BattleOptions',
             'ChatMessagesController', 'ClockTimer', 'CrewExtended', 'DispersionCircle', 'Driftkings_GUI', 'HangarOptions',
             'InfoPanel', 'LogsSwapper', 'MarksOnGunBattle', 'MarksOnGunTechTree', 'MinimapPlugins', 'PlayersPanelHP',
             'RepairExtended', 'SafeShot', 'ServerTurretExtended', 'SixthSenseIcon', 'SpottedExtendedLight',
             'SpottedStatus', 'SystemColor', 'TankCarousel', 'VehicleExpExtended', 'ZoomExtended', 'TooltipsCountItemsLimit', 'TotalLog']


class Settings(ConfigClass):
    enabled = True

    def __init__(self):
        self.ID = 'AutoAimOptimize'
        self.version = '1.0.0'
        self.author = '_DKRuben_EU'

        self.data = {
            'enabled': True,
            'angle': 1.3,
            'catchHiddenTarget': True,
            'disableArtyMode': True
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_angle_text': 'Set angle to catch target',
            'UI_setting_angle_value': 'x',
            'UI_setting_catchHiddenTarget_text': 'Catch target hidden behind an obstacle',
            'UI_setting_catchHiddenTarget_tooltip': '',
            'UI_setting_disableArtyMode_text': 'Disable in Arty mode',
            'UI_setting_disableArtyMode_tooltip': '',
        }
        super(Settings, self).__init__()

    def getData(self):
        return self.data


generator = Settings()

try:
    if generator.enabled:
        print '=' * 25
        print generator.ID
except Exception as err:
    traceback.format_exc(err)
    print '=' * 25
else:
    print 'Status OK'
    print '=' * 25
