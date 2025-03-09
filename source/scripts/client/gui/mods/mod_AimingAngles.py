# -*- coding: utf-8 -*-
import math
from functools import partial

import BigWorld
from Avatar import PlayerAvatar
from AvatarInputHandler import AvatarInputHandler, MapCaseMode
from AvatarInputHandler.DynamicCameras.ArcadeCamera import ArcadeCamera
from AvatarInputHandler.DynamicCameras.ArtyCamera import ArtyCamera
from AvatarInputHandler.DynamicCameras.SniperCamera import SniperCamera
from AvatarInputHandler.DynamicCameras.StrategicCamera import StrategicCamera
from AvatarInputHandler.cameras import FovExtended
from Vehicle import Vehicle
from account_helpers.settings_core import settings_constants
from account_helpers.settings_core.options import InterfaceScaleSetting
from aih_constants import CTRL_MODE_NAME
from gambiter import g_guiFlash
from gambiter.flash import COMPONENT_ALIGN, COMPONENT_TYPE
from gui.Scaleform.daapi.view.battle.shared.crosshair import plugins
from gui.shared.personality import ServicesLocator

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, callback, cancelCallback, calculate_version

ARCADE_MODE = 'arc'
SNIPER_MODE = 'sn'
STRATEGIC_MODE = 'str'
ARTY_MODE = 'arty'
SHIFT = 0.0775
COUNT_STEPS = 3.0
STEP = 1.0 / COUNT_STEPS
TIME_STEP = 0.1 / COUNT_STEPS
YAW_STEP_CORNER = math.pi / 512
COORDINATE_OFF_SCREEN = 20000


class ConfigsInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.aimMode = ARCADE_MODE
        self.y = 0.0
        self.yVert = 0
        self.dataHor = [-COORDINATE_OFF_SCREEN, COORDINATE_OFF_SCREEN]
        self.dataVert = [COORDINATE_OFF_SCREEN, -COORDINATE_OFF_SCREEN]
        self.scaleHor = 0
        self.scaleVert = 0
        self.smoothingID = None
        self.isMapCase = False
        self.visible = True
        self.pitchStep = 0
        self.yaw = self.old_yaw = 0.0
        self.pitch = self.old_pitch = 0.0
        self.old_multiplier = 1.0
        self.leftLimits, self.rightLimits = 0, 0
        self.maxPitch = 0
        self.minPitch = 0
        self.maxBound = 0
        self.minBound = 0
        self.currentStepYaw = 0
        self.currentStepPitch = 0
        self.isAlive = False
        self.showHorCorners = False
        self.showVerCorners = False
        self.showCorners = False
        self.old_gunAnglesPacked = 0
        self.turretPitch = 0.0
        self.gunJointPitch = 0.0
        self.rotation = 0.0
        super(ConfigsInterface, self).__init__()
        override(AvatarInputHandler, 'onControlModeChanged', self.AvatarInputHandler_onControlModeChanged)
        override(InterfaceScaleSetting, 'setSystemValue', self.InterfaceScaleSetting_setSystemValue)
        override(PlayerAvatar, 'onEnterWorld', self.Vehicle_onEnterWorld)
        override(plugins, '_makeSettingsVO', self.plugins_makeSettingsVO)
        override(MapCaseMode, 'activateMapCase', self.anglesAiming_activateMapCase)
        override(MapCaseMode, 'turnOffMapCase', self.anglesAiming_turnOffMapCase)
        override(ArcadeCamera, 'enable', self.ArcadeAimingSystem_enable)
        override(SniperCamera, 'enable', self.SniperAimingSystem_enable)
        override(ArtyCamera, 'enable', self.ArtyAimingSystem_enable)
        override(StrategicCamera, 'enable', self.StrategicAimingSystem_enable)
        override(StrategicCamera, '__cameraUpdate', self.StrategicAimingSystem_cameraUpdate)
        override(Vehicle, '_Vehicle__onAppearanceReady', self.Vehicle__onAppearanceReady)
        override(Vehicle, '_Vehicle__onVehicleDeath', self.Vehicle__onVehicleDeath)
        override(Vehicle, 'set_gunAnglesPacked', self.set_gunAnglesPacked)
        override(FovExtended, 'setFovByMultiplier', self.setFovByMultiplier)
        g_guiFlash.createComponent(self.ID, COMPONENT_TYPE.PANEL, {'x': 0, 'y': 0, 'alignX': COMPONENT_ALIGN.CENTER, 'alignY': COMPONENT_ALIGN.CENTER, 'width': 0, 'height': 0, 'limit': False})
        g_guiFlash.createComponent(self.ID + '.L', COMPONENT_TYPE.IMAGE, {'alignX': COMPONENT_ALIGN.CENTER, 'alignY': COMPONENT_ALIGN.CENTER, 'limit': False})
        g_guiFlash.createComponent(self.ID + '.R', COMPONENT_TYPE.IMAGE, {'alignX': COMPONENT_ALIGN.CENTER, 'alignY': COMPONENT_ALIGN.CENTER, 'limit': False})
        g_guiFlash.createComponent(self.ID + '.lo', COMPONENT_TYPE.IMAGE, {'x': 0, 'alignX': COMPONENT_ALIGN.CENTER, 'alignY': COMPONENT_ALIGN.CENTER, 'limit': False})
        g_guiFlash.createComponent(self.ID + '.hi', COMPONENT_TYPE.IMAGE, {'x': 0, 'alignX': COMPONENT_ALIGN.CENTER, 'alignY': COMPONENT_ALIGN.CENTER, 'limit': False})

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.1.0 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'vertical': 0,
            'horizontal': 0,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_horizontal_text': 'Horizontal marker type',
            'UI_setting_horizontal_tooltip': ('Type of markers to the left and right of the crosshair showing horizontal edge positions of your gun.\n\n' + '\t'.join(' '.join("<img src='img://gui/AimingAngles/%s/%s.png'>" % (i, side) for side in ('Left', 'Right')) for i in xrange(1, 7))),
            'UI_setting_horizontal_0': 'Disabled',
            'UI_setting_horizontal_1': 'Corners',
            'UI_setting_horizontal_2': 'Square brackets',
            'UI_setting_horizontal_3': 'Large semicircle',
            'UI_setting_horizontal_4': 'Semicircle',
            'UI_setting_horizontal_5': 'Octagon',
            'UI_setting_horizontal_6': 'ktulho',
            'UI_setting_vertical_text': 'Vertical marker type',
            'UI_setting_vertical_tooltip': ('Type of markers above and below the crosshair showing vertical edge positions of your gun.\n\n' + '\t'.join("<img src='img://gui/AimingAngles/%s/Bottom.png'>" % (i) for i in xrange(1, 7))),
            'UI_setting_vertical_0': 'Disabled',
            'UI_setting_vertical_1': 'Vertical dash',
            'UI_setting_vertical_2': 'Dot',
            'UI_setting_vertical_3': 'Triangle',
            'UI_setting_vertical_4': 'Diode',
            'UI_setting_vertical_5': 'Octagon',
            'UI_setting_vertical_6': 'ktulho',
        }
        super(ConfigsInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createOptions('horizontal', [self.i18n['UI_setting_horizontal_%s' % i] for i in xrange(7)], self.tb.types.RadioButtonGroup)
            ],
            'column2': [
                self.tb.createOptions('vertical', [self.i18n['UI_setting_vertical_%s' % i] for i in xrange(7)], self.tb.types.RadioButtonGroup)
            ]}

    def updateHor(self):
        rotation = 0
        if self.aimMode == STRATEGIC_MODE:
            if ServicesLocator.settingsCore.getSetting(settings_constants.SPGAim.SPG_STRATEGIC_CAM_MODE) == 0:
                rotation = self.rotation
        g_guiFlash.updateComponent(self.ID, {'rotation': rotation}, {'duration': 0.05})
        marker = self.data['horizontal']
        if not marker:
            g_guiFlash.updateComponent(self.ID + '.L', {'image': ''})
            g_guiFlash.updateComponent(self.ID + '.R', {'image': ''})
            return
        y = self.aim_y()
        L = self.anglesAiming_left()
        R = self.anglesAiming_right()
        g_guiFlash.updateComponent(self.ID + '.L', {'x': L, 'y': y, 'image': '../AimingAngles/%s/Left%s.png' % (marker, ('_limit' if L > -5 else ''))}, {'duration': 0.05})
        g_guiFlash.updateComponent(self.ID + '.R', {'x': R, 'y': y, 'image': '../AimingAngles/%s/Right%s.png' % (marker, ('_limit' if R < 5 else ''))}, {'duration': 0.05})

    def ON_AIM_MODE(self):
        self.updateHor()

    def ON_ANGLES_AIMING(self):
        self.updateHor()
        marker = self.data['vertical']
        if not marker:
            g_guiFlash.updateComponent(self.ID + '.lo', {'image': ''})
            g_guiFlash.updateComponent(self.ID + '.hi', {'image': ''})
            return
        lo = self.anglesAiming_bottom(12)
        hi = self.anglesAiming_top(-12)
        g_guiFlash.updateComponent(self.ID + '.lo', {
            'y': lo, 'alpha': max(350 - lo, 0) / 100.0, 'image': '../AimingAngles/%s/Bottom%s.png' % (
                marker, ('_limit' if not int(lo - self.yVert - 12) else ''))}, {'duration': 0.05})
        g_guiFlash.updateComponent(self.ID + '.hi', {
            'y': hi, 'alpha': max(350 + hi, 0) / 100.0, 'image': '../AimingAngles/%s/Top%s.png' % (
                marker, ('_limit' if not int(hi - self.yVert + 12) else ''))}, {'duration': 0.05})

    def AvatarInputHandler_onControlModeChanged(self, func, b_self, eMode, *a, **k):
        result = func(b_self, eMode, *a, **k)
        try:
            oldAimMMode = self.aimMode
            if b_self._AvatarInputHandler__isArenaStarted:
                if eMode == CTRL_MODE_NAME.ARCADE:
                    self.y = - BigWorld.screenHeight() * SHIFT
                    self.yVert = - BigWorld.screenHeight() * SHIFT
                    self.aimMode = ARCADE_MODE
                elif eMode in {CTRL_MODE_NAME.SNIPER, CTRL_MODE_NAME.DUAL_GUN}:
                    self.y = 0.0
                    self.yVert = 0.0
                    self.aimMode = SNIPER_MODE
                elif eMode == CTRL_MODE_NAME.STRATEGIC:
                    self.y = 0.0
                    self.yVert = 0.0
                    self.aimMode = STRATEGIC_MODE
                elif eMode == CTRL_MODE_NAME.ARTY:
                    self.y = 0.0
                    self.yVert = 0.0
                    self.aimMode = ARTY_MODE
                else:
                    self.aimMode = None
            if oldAimMMode != self.aimMode:
                self.ON_AIM_MODE()
        finally:
            return result

    def InterfaceScaleSetting_setSystemValue(self, func, b_self, value, *args, **kwargs):
        try:
            self.y = - BigWorld.screenHeight() * SHIFT if self.aimMode == ARCADE_MODE else 0.0
            self.ON_AIM_MODE()
        finally:
            return func(b_self, value, *args, **kwargs)

    def Vehicle_onEnterWorld(self, func, b_self, prereqs, *args, **kwargs):
        result = func(b_self, prereqs, *args, **kwargs)
        try:
            if not b_self.isVehicleAlive:
                return
            self.y = - BigWorld.screenHeight() * SHIFT
            self.yVert = - BigWorld.screenHeight() * SHIFT
            self.aimMode = ARCADE_MODE
            self.ON_AIM_MODE()
        finally:
            return result

    def plugins_makeSettingsVO(self, func, b_self, *args, **kwargs):
        data = func(b_self, *args, **kwargs)
        try:
            self.ON_AIM_MODE()
        finally:
            return data

    def aim_y(self, shift=0.0):
        return int(self.y + shift)

    def hideCorners(self):
        self.dataHor = [-COORDINATE_OFF_SCREEN, COORDINATE_OFF_SCREEN]
        self.dataVert = [COORDINATE_OFF_SCREEN, -COORDINATE_OFF_SCREEN]

    def anglesAiming_activateMapCase(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        try:
            self.isMapCase = True
            self.hideCorners()
            self.ON_ANGLES_AIMING()
        finally:
            return result

    def anglesAiming_turnOffMapCase(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        try:
            self.isMapCase = False
        finally:
            return result

    def updateCoordinates(self):
        if self.isMapCase:
            return
        if self.smoothingID is not None:
            cancelCallback(self.smoothingID)
            self.smoothingID = None
        verticalFov = BigWorld.projection().fov
        horizontalFov = verticalFov * BigWorld.getAspectRatio()
        screenW = BigWorld.screenWidth()
        screenH = BigWorld.screenHeight()
        self.scaleHor = screenW / horizontalFov if horizontalFov else screenW
        self.scaleVert = screenH / verticalFov if verticalFov else screenH
        self.dataHor, self.dataVert = self.coordinate(self.yaw, self.pitch)
        self.updateLabels()

    def updateLabels(self):
        halfScreenW = BigWorld.screenWidth() / 2
        halfScreenH = BigWorld.screenHeight() / 2
        left, right = self.dataHor
        lo, hi = self.dataVert
        old_visible = self.visible
        self.visible = not (hi < -halfScreenH) or not (lo > halfScreenH)
        if self.showHorCorners:
            self.visible |= not (left < - halfScreenW) or not (right > halfScreenW)
        if self.visible or old_visible:
            self.ON_ANGLES_AIMING()

    def ArcadeAimingSystem_enable(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        try:
            self.updateCoordinates()
        finally:
            return result

    def SniperAimingSystem_enable(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        try:
            self.updateCoordinates()
        finally:
            return result

    def ArtyAimingSystem_enable(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        try:
            self.updateCoordinates()
        finally:
            return result

    def StrategicAimingSystem_enable(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        try:
            self.updateCoordinates()
        finally:
            return result

    def StrategicAimingSystem_cameraUpdate(self, func, b_self, *args, **kwargs):
        result = func(b_self, *args, **kwargs)
        try:
            vehicle = getPlayer().getVehicleAttached()
            diff = b_self.aimingSystem.planePosition - vehicle.position
            rotation = math.degrees(math.atan2(diff.x, diff.z))
            if rotation != self.rotation:
                self.rotation = rotation
            self.updateCoordinates()
        finally:
            return result

    def Vehicle__onAppearanceReady(self, func, b_self, *args, **kwargs):
        result = func(b_self, *args, **kwargs)
        try:
            if not b_self.isPlayerVehicle:
                return
            self.smoothingID = None
            self.yaw = self.old_yaw = 0.0
            self.pitch = self.old_pitch = 0.0
            self.old_multiplier = 1.0
            self.old_gunAnglesPacked = 0
            self.isAlive = b_self.isAlive
            gun = b_self.typeDescriptor.gun
            self.minBound, self.maxBound = gun.pitchLimits['absolute']
            self.pitchStep = (self.maxBound - self.minBound) / 63.0
            self.showHorCorners = not ((gun.staticTurretYaw is not None) or (gun.turretYawLimits is None))
            if self.showHorCorners:
                self.leftLimits, self.rightLimits = gun.turretYawLimits
            else:
                self.leftLimits, self.rightLimits = None, None
            self.showVerCorners = not gun.staticPitch
            self.showCorners = self.showHorCorners or self.showVerCorners
            self.isMapCase = False
            self.maxPitch = gun.pitchLimits['maxPitch']
            self.minPitch = gun.pitchLimits['minPitch']
            self.visible = True
            self.turretPitch = b_self.typeDescriptor.hull.turretPitches[0]
            self.gunJointPitch = b_self.typeDescriptor.turret.gunJointPitch
            self.updateCoordinates()
        finally:
            return result

    def Vehicle__onVehicleDeath(self, func, b_self, *args, **kwargs):
        result = func(b_self, *args, **kwargs)
        try:
            if not b_self.isPlayerVehicle:
                return
            self.isAlive = False
            self.hideCorners()
            self.showCorners = False
            self.ON_ANGLES_AIMING()
        finally:
            return result

    def set_gunAnglesPacked(self, func, b_self, *args, **kwargs):
        result = func(b_self, *args, **kwargs)
        try:
            if not b_self.isPlayerVehicle or b_self.gunAnglesPacked == self.old_gunAnglesPacked or not self.showCorners or self.isMapCase:
                return
            if getPlayer() is None or getPlayer().isObserver():
                self.hideCorners()
                return
            _pitch = b_self.gunAnglesPacked & 63
            if ((self.old_gunAnglesPacked & 63) == _pitch) and not self.showHorCorners:
                return
            self.old_gunAnglesPacked = b_self.gunAnglesPacked
            self.yaw = YAW_STEP_CORNER * (b_self.gunAnglesPacked >> 6 & 1023) - math.pi
            self.pitch = self.minBound + _pitch * self.pitchStep
            self.currentStepPitch = (self.pitch - self.old_pitch) * STEP
            self.currentStepYaw = (self.yaw - self.old_yaw) * STEP
            if self.smoothingID is not None:
                cancelCallback(self.smoothingID)
                self.smoothingID = None
            self.smoothing(self.old_yaw + self.currentStepYaw, self.old_pitch + self.currentStepPitch, STEP)
            self.old_yaw = 0 if not self.showHorCorners else self.yaw
            self.old_pitch = self.pitch
        finally:
            return result

    def smoothing(self, stepYaw, stepPitch, step):
        self.dataHor, self.dataVert = self.coordinate(stepYaw, stepPitch)
        if (step + STEP) < 1.001:
            self.smoothingID = callback(TIME_STEP, partial(self.smoothing, stepYaw + self.currentStepYaw, stepPitch + self.currentStepPitch, step + STEP))
        else:
            self.smoothingID = None
        self.updateLabels()

    def setFovByMultiplier(self, func, b_self, multiplier, *args, **kwargs):
        result = func(b_self, multiplier, *args, **kwargs)
        try:
            if self.old_multiplier == multiplier or not self.showCorners or self.isMapCase:
                return
            self.old_multiplier = multiplier
            self.updateCoordinates()
        finally:
            return result

    def coordinate(self, _yaw, _pitch):
        if self.showHorCorners:
            dif_yaw = self.leftLimits - _yaw
            xLeft = int(self.scaleHor * dif_yaw) if dif_yaw < -YAW_STEP_CORNER else 0
            dif_yaw = self.rightLimits - _yaw
            xRight = int(self.scaleHor * dif_yaw) if dif_yaw > YAW_STEP_CORNER else 0
        else:
            xLeft = - COORDINATE_OFF_SCREEN
            xRight = COORDINATE_OFF_SCREEN
        if self.showVerCorners:
            pHi, pLo = BigWorld.wg_calcGunPitchLimits(_yaw, self.minPitch, self.maxPitch, self.turretPitch, self.gunJointPitch)
            dif_pitch = pLo - _pitch
            yLo = int((self.scaleVert * dif_pitch + self.yVert) if dif_pitch > self.pitchStep else self.yVert)
            dif_pitch = pHi - _pitch
            yHi = int((self.scaleVert * dif_pitch + self.yVert) if dif_pitch < -self.pitchStep else self.yVert)
        else:
            yLo = COORDINATE_OFF_SCREEN
            yHi = -COORDINATE_OFF_SCREEN
        return [xLeft, xRight], [yLo, yHi]

    def anglesAiming_left(self, x=0):
        return (self.dataHor[0] + x) if self.isAlive else -COORDINATE_OFF_SCREEN

    def anglesAiming_right(self, x=0):
        return (self.dataHor[1] + x) if self.isAlive else COORDINATE_OFF_SCREEN

    def anglesAiming_bottom(self, _y=0):
        return (self.dataVert[0] + _y) if self.isAlive else COORDINATE_OFF_SCREEN

    def anglesAiming_top(self, _y=0):
        return (self.dataVert[1] + _y) if self.isAlive else -COORDINATE_OFF_SCREEN


config = ConfigsInterface()
analytics = Analytics(config.ID, config.version, 'G-B7Z425MJ3L')
