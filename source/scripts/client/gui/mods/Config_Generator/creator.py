# -*- coding: utf-8 -*-
from core import ConfigClass

MODS_LIST = ['ArcadeZoom', 'ArmorCalculator', 'ArtySplash', 'AutoAimOptimize', 'AutoServerSight', 'BanksLoader', 'BattleEfficiency', 'BattleOptions',
             'CrewSettings', 'CrewExtended', 'DispersionCircle', 'DistanceTimer', 'DistanceToEnemy', 'Driftkings_GUI', 'HangarOptions',
             'InfoPanel', 'LogsSwapper', 'MainGun', 'MarksOnGunBattle', 'MarksOnGunTechTree', 'MinimapPlugins', 'PlayersPanelHP',
             'RepairExtended', 'SafeShot', 'ServerTurretExtended', 'SixthSense', 'SpottedExtendedLight',
             'SpottedStatus', 'SystemColor', 'VehicleExpExtended', 'ZoomExtended', 'TooltipsCountItemsLimit', 'TotalLog', 'OwnHealth']


class Settings(ConfigClass):
    enabled = True

    def __init__(self):
        self.ID = 'CrewSettings'
        self.version = '1.0.0'
        self.author = '_DKRuben_EU'
        self.defaultKeys = {}
        self.data = {
            'enabled': True,
            'crewReturn': False,
            'crewTraining': False,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_crewReturn_text': 'Crew Auto-Return',
            'UI_setting_crewReturn_tooltip': 'Return crew tanks.',
            'UI_setting_crewTraining_text': 'Crew Training',
            'UI_setting_crewTraining_tooltip': 'Monitors whether \'Field Upgrade\' is upgraded/available and enables or disables \'Expedited Crew Training\' accordingly',

            # crew dialogs
            'UI_dialog_apply': 'Apply',
            'UI_dialog_cancel': 'Cancel',
            'UI_dialog_ignore': 'Ignore',
            #
            'crewDialogs': {
                'enabled': '<br>Enable accelerated crew training?',
                'disabled': '<br>Disable accelerated crew training?',
                'notAvailable': 'Field upgrades are not available for this vehicle.',
                'isFullXp': 'You have accumulated the necessary amount of experience to fully upgrade the field upgrade.',
                'isFullComplete': 'You have pumped the field upgrade to the highest possible level.',
                'needTurnOff': 'You do not have field upgrades, it is recommended to disable accelerated crew training.'
            }
        }
        super(Settings, self).__init__()

    def getData(self):
        return self.data


generator = Settings()

try:
    if generator.enabled:
        print '=' * 25
        print generator.ID
except StandardError as err:
    print err
    print '=' * 25
else:
    print 'Status OK'
    print '=' * 25
