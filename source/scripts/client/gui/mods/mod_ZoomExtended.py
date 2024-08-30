# -*- coding: utf-8 -*-
import math

import TriggersManager
from AvatarInputHandler.DynamicCameras.SniperCamera import SniperCamera
from AvatarInputHandler.control_modes import SniperControlMode
from PlayerEvents import g_playerEvents
from account_helpers.settings_core.options import SniperZoomSetting
from aih_constants import CTRL_MODE_NAME
from gui.battle_control.avatar_getter import getOwnVehiclePosition
from helpers.bound_effects import ModelBoundEffects

from DriftkingsCore import SimpleConfigInterface, Analytics, override, isReplay, callback, calculate_version, getPlayer


class ConfigsInterface(SimpleConfigInterface):
    def __init__(self):
        self.settingsCache = {'dynamicZoom': False, 'zoomXMeters': 20, 'stepsOnly': False}
        super(ConfigsInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.5 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'noBinoculars': False,
            'noFlashBang': False,
            'noShockWave': False,
            'noSniperDynamic': False,
            'disableCamAfterShot': False,
            'disableCamAfterShotLatency': 0.5,
            'disableCamAfterShotSkipClip': True,
            'dynamicZoom': {'enabled': False, 'stepsOnly': False},
            'zoomSteps': {
                'enabled': True,
                'steps': [4.0, 6.0, 8.0, 12.0, 16.0, 25.0, 30.0]
            }
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
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
        super(ConfigsInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
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


class ChangeCameraModeAfterShoot(TriggersManager.ITriggerListener):

    def __init__(self):
        self.latency = 0
        self.skip_clip = False
        self.subscribed = False
        self.avatar = None
        self.__trigger_type = TriggersManager.TRIGGER_TYPE.PLAYER_DISCRETE_SHOOT

    def updateSettings(self):
        enabled = config.data['disableCamAfterShot'] and config.data['enabled']
        self.latency = float(config.data['disableCamAfterShotLatency'])
        self.skip_clip = config.data['disableCamAfterShotSkipClip']
        if not self.subscribed and enabled:
            g_playerEvents.onAvatarReady += self.onStart
            g_playerEvents.onAvatarBecomeNonPlayer += self.onFinish
            self.subscribed = True
        elif self.subscribed and not enabled:
            g_playerEvents.onAvatarReady -= self.onStart
            g_playerEvents.onAvatarBecomeNonPlayer -= self.onFinish
            self.subscribed = False

    def onStart(self):
        self.avatar = getPlayer()
        TriggersManager.g_manager.addListener(self)

    def onFinish(self):
        self.avatar = None
        TriggersManager.g_manager.delListener(self)

    def onTriggerActivated(self, params):
        if params.get('type') == self.__trigger_type:
            callback(max(self.latency, 0), self.changeControlMode)

    def changeControlMode(self):
        if self.avatar is None:
            return
        input_handler = self.avatar.inputHandler
        if self.avatar.inputHandler is not None and input_handler.ctrlModeName == CTRL_MODE_NAME.SNIPER:
            v_desc = self.avatar.getVehicleDescriptor()
            caliber_skip = v_desc.shot.shell.caliber <= 60
            if caliber_skip or self.skip_clip and 'clip' in v_desc.gun.tags:
                return
            aiming_system = input_handler.ctrl.camera.aimingSystem
            input_handler.onControlModeChanged(CTRL_MODE_NAME.ARCADE,
                                               prevModeName=input_handler.ctrlModeName,
                                               preferredPos=aiming_system.getDesiredShotPoint(),
                                               turretYaw=aiming_system.turretYaw,
                                               gunPitch=aiming_system.gunPitch,
                                               aimingMode=input_handler.ctrl._aimingMode,
                                               closesDist = False,
                                               curVehicleID = self.avatar.playerVehicleID)


ChangeCameraModeAfterShoot()


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
