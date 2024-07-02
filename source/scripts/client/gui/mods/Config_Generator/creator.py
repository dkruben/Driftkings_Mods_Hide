# -*- coding: utf-8 -*-
from core import ConfigInterface

MODS_LIST = ['AimingAngles', 'ArcadeZoom', 'ArmorCalculator', 'ArtySplash', 'AutoAimOptimize', 'AutoServerSight', 'BanksLoader', 'BattleEfficiency', 'BattleOptions',
             'CrewSettings', 'CrewExtended', 'DispersionCircle', 'DistanceTimer', 'DistanceToEnemy', 'Driftkings_GUI', 'HangarOptions',
             'InfoPanel', 'LogsSwapper', 'MainGun', 'MarksOnGunBattle', 'MarksOnGunTechTree', 'MinimapPlugins', 'PlayersPanelHP',
             'RepairExtended', 'SafeShot', 'ServerTurretExtended', 'SixthSense', 'SpottedExtendedLight',
             'SpottedStatus', 'SystemColor', 'VehicleExpExtended', 'ZoomExtended', 'TooltipsCountItemsLimit', 'TotalLog', 'OwnHealth']


class Settings(ConfigInterface):
    enabled = True

    def init(self):
        self.ID = 'ZoomExtended'
        self.version = '1.1.0 (02.04.2024)'
        self.author = 'by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        # -
        self.data = {
            'enabled': False,
            'noBinoculars': False,
            'noFlashBang': False,
            'noShockWave': False,
            'noSniperDynamic': False,
            'disableCamAfterShot': False,
            'disableCamAfterShotLatency': 0.5,
            'disableCamAfterShotSkipClip': True,
            'dynamicZoom': {
                'enabled': False,
                'stepsOnly': False
            },
            'zoomSteps': {
                'enabled': False,
                'steps': [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 16.0, 20.0, 25.0, 30.0]
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_noBinoculars_text': 'Disable Binoculars.',
            'UI_setting_noBinoculars_tooltip': 'Remove the blackout in sniper mode.',
            'UI_setting_noFlashBang_text': 'Disable Red Flash.',
            'UI_setting_noFlashBang_tooltip': 'Remove red flash when taking damage.',
            'UI_setting_noShockWave_text': 'Shock Wave',
            'UI_setting_noShockWave_tooltip': 'Remove camera shaking when hit by tank.',
            'UI_setting_noSniperDynamic_text': 'Sniper Dynamic',
            'UI_setting_noSniperDynamic_tooltip': 'Disable dynamic camera in sniper mode.',
            'UI_setting_disableCamAfterShot_text': 'Disable Cam After Shot',
            'UI_setting_disableCamAfterShot_tooltip': 'Disable sniper mode after the shot.',
            'UI_setting_disableCamAfterShotLatency_text': 'Disable Cam After Shot Latency',
            'UI_setting_disableCamAfterShotLatency_tooltip': 'Delay automatic shutdown of the camera.',
            'UI_setting_disableCamAfterShotSkipClip_text': 'Disable Cam After Shot Skip Clip',
            'UI_setting_disableCamAfterShotSkipClip_tooltip': 'Do not exit if magazine loading system.',
        }
        super(Settings, self).init()


generator = Settings()


def _formatMessage(message, *args, **kwargs):
    return str(message).format(*args, **kwargs)


def do_log(message, *args, **kwargs):
    print(_formatMessage(message, *args, **kwargs))


if __name__ == '__main__':
    try:
        if generator.enabled:
            do_log('=' * 25)
            Settings()
    except Exception as err:
        print do_log('[ERROR]:', err)
    else:
        do_log('Status OK')
        do_log('Mod Name: {}, v.{} and author {}', generator.ID, generator.version, generator.author)
        do_log('=' * 25)
