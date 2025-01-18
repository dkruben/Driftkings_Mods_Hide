# -*- coding: utf-8 -*-
import math

import BattleReplay
import GUI
import Math
import math_utils
from Avatar import PlayerAvatar
from AvatarInputHandler import gun_marker_ctrl
from AvatarInputHandler.AimingSystems.SniperAimingSystem import SniperAimingSystem
from AvatarInputHandler.gun_marker_ctrl import _DefaultGunMarkerController, _GunMarkerController, _GunMarkersDPFactory, _GunMarkersDecorator, _MARKER_FLAG, _MARKER_TYPE, _SPGGunMarkerController, _calcScale, _makeWorldMatrix
from VehicleGunRotator import VehicleGunRotator
from constants import SERVER_TICK_LENGTH
from gui.Scaleform.daapi.view.battle.shared.crosshair import gm_factory
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, calculate_version


class ConfigInterface(DriftkingsConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.9.5 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'replaceOriginalCircle': True,
            'useServerDispersion': True,
            'dispersionCircleScale': 1.0,
            'horizontalStabilizer': False,
            'version': calculate_version(self.version),
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_replaceOriginalCircle_text': 'Replace aiming circle to dispersion circle',
            'UI_setting_replaceOriginalCircle_tooltip': 'Replace the original aiming circle to dispersion circle (To improve accuracy)',
            'UI_setting_useServerDispersion_text': 'Use server side circle of dispersion',
            'UI_setting_useServerDispersion_tooltip': 'Change client to server circle of dispersion(not working in replays)',
            'UI_setting_dispersionCircleScale_text': 'Scale dispersion circle (UI)',
            'UI_setting_dispersionCircleScale_format': 'x',
            'UI_setting_horizontalStabilizer_text': 'Activate: Horizontal sight stabilization',
            'UI_setting_horizontalStabilizer_tooltip': ''
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        scale = 'UI_setting_dispersionCircleScale_format'
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('replaceOriginalCircle'),
                self.tb.createControl('useServerDispersion')
            ],
            'column2': [
                self.tb.createSlider('dispersionCircleScale', 1.0, 100.0, 1.0, '{{value}}%s' % scale),
                self.tb.createControl('horizontalStabilizer')
            ]
        }

    # noinspection PyProtectedMember
    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)
        if not self.data['replaceOriginalCircle']:
            gun_marker_ctrl.useClientGunMarker = lambda: True
            gun_marker_ctrl.useServerGunMarker = lambda: True
            gun_marker_ctrl.useDefaultGunMarkers = lambda: False
            gm_factory._FACTORIES_COLLECTION = (gm_factory._DevControlMarkersFactory, gm_factory._OptionalMarkersFactory, gm_factory._EquipmentMarkersFactory)


class NewDefaultGunMarkerController(_GunMarkerController):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self, gunMakerType, dataProvider, enabledFlag=_MARKER_FLAG.UNDEFINED):
        super(NewDefaultGunMarkerController, self).__init__(gunMakerType, dataProvider, enabledFlag=enabledFlag)
        self.__replSwitchTime = 0.0
        self.__curSize = 0.0
        self.__screenRatio = 0.0

    def enable(self):
        super(NewDefaultGunMarkerController, self).enable()
        self.__updateScreenRatio()
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.isClientReady:
            self.__replSwitchTime = 0.2

    def update(self, markerType, pos, direction, sizeVector, relaxTime, collData):
        super(NewDefaultGunMarkerController, self).update(markerType, pos, direction, sizeVector, relaxTime, collData)
        positionMatrix = Math.Matrix()
        positionMatrix.setTranslate(pos)
        self._updateMatrixProvider(positionMatrix, relaxTime)
        size = sizeVector[0]
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.isClientReady:
            s = replayCtrl.getArcadeGunMarkerSize()
            if s != -1.0:
                size = s
        elif replayCtrl.isRecording:
            if replayCtrl.isServerAim and self._gunMarkerType == _MARKER_TYPE.SERVER:
                replayCtrl.setArcadeGunMarkerSize(size)
            elif self._gunMarkerType == _MARKER_TYPE.CLIENT:
                replayCtrl.setArcadeGunMarkerSize(size)
        worldMatrix = _makeWorldMatrix(positionMatrix)
        self.__curSize = _calcScale(worldMatrix, size) * self.__screenRatio * config.data['dispersionCircleScale'] / 2.3
        if self.__replSwitchTime > 0.0:
            self.__replSwitchTime -= relaxTime
            self._dataProvider.updateSize(self.__curSize, 0.0)
        else:
            self._dataProvider.updateSize(self.__curSize, relaxTime)

    def onRecreateDevice(self):
        self.__updateScreenRatio()

    def __updateScreenRatio(self):
        self.__screenRatio = GUI.screenResolution()[0] * 0.5


class DispersionCircle(object):

    # noinspection PyProtectedMember
    @staticmethod
    def gunMarkersDecoratorSetPosition(func, position, markerType):
        if not config.data['replaceOriginalCircle']:
            if markerType == _MARKER_TYPE.CLIENT:
                func._GunMarkersDecorator__clientMarker.setPosition(position)
            if config.data['useServerDispersion']:
                if markerType == _MARKER_TYPE.SERVER:
                    func._GunMarkersDecorator__serverMarker.setPosition(position)
            elif markerType == _MARKER_TYPE.CLIENT:
                func._GunMarkersDecorator__serverMarker.setPosition(position)
        else:
            if config.data['useServerDispersion']:
                if markerType == _MARKER_TYPE.SERVER:
                    func._GunMarkersDecorator__clientMarker.setPosition(position)
            elif markerType == _MARKER_TYPE.CLIENT:
                func._GunMarkersDecorator__clientMarker.setPosition(position)
            if markerType == _MARKER_TYPE.SERVER:
                func._GunMarkersDecorator__serverMarker.setPosition(position)

    # noinspection PyProtectedMember
    @staticmethod
    def gunMarkersDecoratorUpdate(func, markerType, position, direction, size, relaxTime, collData):
        if not config.data['replaceOriginalCircle']:
            if markerType == _MARKER_TYPE.CLIENT:
                func._GunMarkersDecorator__clientState = (position, direction, collData)
                if func._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.CLIENT_MODE_ENABLED:
                    func._GunMarkersDecorator__clientMarker.update(markerType, position, direction, size, relaxTime, collData)
            if config.data['useServerDispersion']:
                if markerType == _MARKER_TYPE.SERVER:
                    func._GunMarkersDecorator__serverState = (position, direction, collData)
                    if func._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.SERVER_MODE_ENABLED:
                        func._GunMarkersDecorator__serverMarker.update(markerType, position, direction, size, relaxTime, collData)
            elif markerType == _MARKER_TYPE.CLIENT:
                func._GunMarkersDecorator__serverState = (position, direction, collData)
                if func._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.SERVER_MODE_ENABLED:
                    func._GunMarkersDecorator__serverMarker.update(markerType, position, direction, size, relaxTime, collData)
        else:
            if config.data['useServerDispersion']:
                if markerType == _MARKER_TYPE.SERVER:
                    func._GunMarkersDecorator__clientState = (position, direction, collData)
                    if func._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.CLIENT_MODE_ENABLED:
                        func._GunMarkersDecorator__clientMarker.update(markerType, position, direction, size, relaxTime, collData)
            elif markerType == _MARKER_TYPE.CLIENT:
                func._GunMarkersDecorator__clientState = (position, direction, collData)
                if func._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.CLIENT_MODE_ENABLED:
                    func._GunMarkersDecorator__clientMarker.update(markerType, position, direction, size, relaxTime, collData)
            if markerType == _MARKER_TYPE.SERVER:
                func._GunMarkersDecorator__serverState = (position, direction, collData)
                if func._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.SERVER_MODE_ENABLED:
                    func._GunMarkersDecorator__serverMarker.update(markerType, position, direction, size, relaxTime, collData)

    @staticmethod
    def createGunMarker(isStrategic):
        factory = _GunMarkersDPFactory()
        if isStrategic:
            clientMarker = _SPGGunMarkerController(_MARKER_TYPE.CLIENT, factory.getClientSPGProvider())
            serverMarker = _SPGGunMarkerController(_MARKER_TYPE.SERVER, factory.getServerSPGProvider())
        else:
            clientMarker = _DefaultGunMarkerController(_MARKER_TYPE.CLIENT, factory.getClientProvider()) if not config.data['replaceOriginalCircle'] else NewDefaultGunMarkerController(_MARKER_TYPE.CLIENT, factory.getClientProvider())
            serverMarker = NewDefaultGunMarkerController(_MARKER_TYPE.SERVER, factory.getServerProvider())
        return _GunMarkersDecorator(clientMarker, serverMarker)

    # noinspection PyProtectedMember
    @staticmethod
    def enableHorizontalStabilizerRuntime(func):
        yawConstraint = math.pi * 2.1 if config.data['horizontalStabilizer'] else 0.0
        func._SniperAimingSystem__yprDeviationConstraints.x = yawConstraint

    # noinspection PyProtectedMember
    @staticmethod
    def glide(func, posDelta):
        func._InputInertia__deltaEasing.reset(posDelta, Math.Vector3(0.0), 0.001)

    # noinspection PyProtectedMember
    @staticmethod
    def glideFov(func, newRelativeFocusDist):
        minMulti, maxMulti = func._InputInertia__minMaxZoomMultiplier
        endMulti = math_utils.lerp(minMulti, maxMulti, newRelativeFocusDist)
        func._InputInertia__zoomMultiplierEasing.reset(func._InputInertia__zoomMultiplierEasing.value, endMulti, 0.001)


config = ConfigInterface()
dispersionCircle = DispersionCircle()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(_GunMarkerController, 'update')
def new__gunMarkerControllerUpdate(func, self, markerType, position, direction, size, relaxTime, collData):
    if config.data['enabled']:
        self._position = position
        return
    func(self, markerType, position, direction, size, relaxTime, collData)


@override(_GunMarkersDecorator, 'setPosition')
def new__gunMarkersDecoratorSetPosition(func, self, position, markerType=_MARKER_TYPE.CLIENT):
    if config.data['enabled']:
        dispersionCircle.gunMarkersDecoratorSetPosition(self, position, markerType)
        return
    func(self, position, markerType)


@override(_GunMarkersDecorator, 'update')
def new__gunMarkersDecoratorUpdate(func, self, markerType, position, direction, size, relaxTime, collData):
    if config.data['enabled']:
        dispersionCircle.gunMarkersDecoratorUpdate(self, markerType, position, direction, size, relaxTime, collData)
        return
    func(self, markerType, position, direction, size, relaxTime, collData)


@override(gun_marker_ctrl, 'createGunMarker')
def new__createGunMarker(func, isStrategic):
    return dispersionCircle.createGunMarker(isStrategic) if config.data['enabled'] else func(isStrategic)


@override(SniperAimingSystem, 'enableHorizontalStabilizerRuntime')
def new__enableHorizontalStabilizerRuntime(func, self, enable):
    if config.data['enabled']:
        dispersionCircle.enableHorizontalStabilizerRuntime(self)
        return
    func(self, enable)


@override(VehicleGunRotator, 'setShotPosition')
def new__setShotPosition(func, self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh=False):
    if config.data['enabled'] and config.data['UseServerDispersion']:
        if self._VehicleGunRotator__clientMode and self._VehicleGunRotator__showServerMarker:
            return func(self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh)
        markerPos, markerDir, markerSize, idealMarkerSize, collData = self._VehicleGunRotator__getGunMarkerPosition(shotPos, shotVec, self._VehicleGunRotator__dispersionAngles)
        self._avatar.inputHandler.updateGunMarker2(markerPos, markerDir, (markerSize, idealMarkerSize), SERVER_TICK_LENGTH, collData)
        return
    func(self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh)


@override(PlayerAvatar, 'enableServerAim')
def new__enableServerAim(func, self, enable):
    if config.data['enabled']:
        func(self, config.data['UseServerDispersion'])
        return
    func(self, enable)


@override(VehicleGunRotator, 'applySettings')
def new__enableServerAim(func, self, diff):
    if config.data['enabled']:
        func(self, {})
        return
    func(self, diff)


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(func, *args):
    func(*args)
    if config.data['enabled']:
        getPlayer().enableServerAim(config.data['UseServerDispersion'])
