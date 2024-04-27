# -*- coding: utf-8 -*-
import math

from Avatar import PlayerAvatar
from AvatarInputHandler.DynamicCameras.SniperCamera import SniperCamera
from AvatarInputHandler.control_modes import SniperControlMode
from account_helpers.settings_core.options import SniperZoomSetting
from aih_constants import CTRL_MODE_NAME
from gui.battle_control.avatar_getter import getOwnVehiclePosition
from helpers.bound_effects import ModelBoundEffects

from DriftkingsCore import SimpleConfigInterface, Analytics, override, logDebug, isReplay, callback


class ConfigsInterface(SimpleConfigInterface):
    def __init__(self):
        self.settingsCache = {'dynamicZoom': False, 'zoomXMeters': 20, 'stepsOnly': False}
        super(ConfigsInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
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
            'UI_setting_disableCamAfterShot_text': 'Sisable Cam After Shot',
            'UI_setting_disableCamAfterShot_tooltip': 'Disable sniper mode after the shot.',
            'UI_setting_disableCamAfterShotLatency_text': 'Disable Cam After Shot Latency',
            'UI_setting_disableCamAfterShotLatency_tooltip': 'Delay automatic shutdown of the camera.',
            'UI_setting_disableCamAfterShotSkipClip_text': 'Disable Cam After Shot Skip Clip',
            'UI_setting_disableCamAfterShotSkipClip_tooltip': 'Do not exit if magazine loading system.',
        }
        super(ConfigsInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'settingsVersion': 1,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('noBinoculars'),
                self.tb.createControl('noFlashBang'),
                self.tb.createControl('noShockWave'),
                self.tb.createControl('noSniperDynamic')
            ],
            'column2': [
                self.tb.createControl('disableCamAfterShot'),
                self.tb.createSlider('disableCamAfterShotLatency', 1.0, 20.0, 1.0, '{{value}} %'),
                self.tb.createControl('disableCamAfterShotSkipClip')
            ]
        }


config = ConfigsInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(SniperCamera, '_readConfigs')
def new__readConfigs(func, self, data):
    self._baseCfg.clear()
    self._userCfg.clear()
    self._cfg.clear()
    func(self, data)
    if not config.data['enabled'] or isReplay():
        return
    if config.data['noSniperDynamic'] and self.isCameraDynamic():
        self.enableDynamicCamera(False)
    if config.data['zoomSteps']['enabled']:
        steps = [step for step in config.data['zoomSteps']['steps'] if step >= 2.0]
        if len(steps) > 3:
            steps.sort()
            for cfg in (self._cfg, self._userCfg, self._baseCfg):
                cfg['increasedZoom'] = True
                cfg['zooms'] = steps
            exposure = self._SniperCamera__dynamicCfg['zoomExposure']
            while len(steps) > len(exposure):
                exposure.insert(0, exposure[0] + 0.1)
    if config.settingsCache['dynamicZoom']:
        self.setSniperZoomSettings(-1)
        # if settingsCache[SNIPER.STEPS_ONLY]:
        #     settingsCache[SNIPER.METERS] = math.ceil(SNIPER.MAX_DIST / camera._cfg[SNIPER.ZOOMS][GLOBAL.LAST])
        # else:
        #     settingsCache[SNIPER.METERS] = DEFAULT_X_METERS


@override(SniperZoomSetting, 'setSystemValue')
def new__setSystemValue(func, self, value):
    return func(self, 0 if config.settingsCache['dynamicZoom'] else value)


def getZoom(distance, steps):
    zoom = math.floor(distance / 20)
    if config.settingsCache['stepsOnly']:
        zoom = min(steps, key=lambda value: abs(value - zoom))
    if zoom < 2.0:
        return 2.0
    return zoom


@override(SniperCamera, 'enable')
def new__enable(func, self, targetPos, saveZoom):
    if config.settingsCache['dynamicZoom']:
        saveZoom = True
        ownPosition = getOwnVehiclePosition()
        distance = (targetPos - ownPosition).length if ownPosition is not None else 0
        if distance > 700.0:
            distance = 0
        self._cfg['zoom'] = getZoom(distance, self._cfg['zooms'])
    return func(self, targetPos, saveZoom)


def changeControlMode(avatar):
    input_handler = avatar.inputHandler
    if input_handler is not None and input_handler.ctrlModeName == CTRL_MODE_NAME.SNIPER:
        v_desc = avatar.getVehicleDescriptor()
        caliberSkip = v_desc.shot.shell.caliber <= 60
        if caliberSkip or config.data['disableCamAfterShotSkipClip'] and 'clip' in v_desc.gun.tags:
            return
        aiming_system = input_handler.ctrl.camera.aimingSystem
        input_handler.onControlModeChanged(CTRL_MODE_NAME.ARCADE,
                                           prevModeName=input_handler.ctrlModeName,
                                           preferredPos=aiming_system.getDesiredShotPoint(),
                                           turretYaw=aiming_system.turretYaw,
                                           gunPitch=aiming_system.gunPitch,
                                           aimingMode=input_handler.ctrl._aimingMode,
                                           closesDist=False)


@override(PlayerAvatar, 'showTracer')
def new__showTracer(func, self, shooterID, *args):
    try:
        if config.data['disableCamAfterShot'] and config.data['enabled'] and not isReplay():
            if shooterID == self.playerVehicleID:
                callback(max(config.data['disableCamAfterShotLatency'], 0), changeControlMode, self)
    except Exception as err:
        logDebug(config.ID, True, 'I can\'t get out of sniper mode. Error {}.changeControlMode, {}', __package__, err)
    finally:
        return func(self, shooterID, *args)


# EFFECTS
@override(SniperControlMode, '__setupBinoculars')
def new__setupBinoculars(func, self, isCoatedOptics):
    func(self, isCoatedOptics)
    if config.data['noBinoculars']:
        self._binoculars.setEnabled(False)
        self._binoculars.resetTextures()


@override(ModelBoundEffects, 'addNewToNode')
def new__effectsListPlayer(func, *args, **kwargs):
    if 'isPlayerVehicle' in kwargs:
        if config.data['noFlashBang'] and 'showFlashBang' in kwargs:
            kwargs['showFlashBang'] = False
        if config.data['noShockWave'] and 'showShockWave' in kwargs:
            kwargs['showShockWave'] = False
    return func(*args, **kwargs)
