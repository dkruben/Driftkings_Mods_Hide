# -*- coding: utf-8 -*-
import AvatarInputHandler
import BattleReplay
import BigWorld
import Math
import VehicleGunRotator
import aih_constants
from account_helpers.settings_core.settings_constants import GRAPHICS, SPGAim
from aih_constants import CTRL_MODE_NAME, GUN_MARKER_FLAG, GUN_MARKER_TYPE
from aih_constants import GUN_MARKER_TYPE
from constants import AIMING_MODE, ARENA_PERIOD, SERVER_TICK_LENGTH
from gui.Scaleform.daapi.view.battle.shared import SharedPage
from gui.Scaleform.daapi.view.battle.shared.crosshair import CrosshairPanelContainer, gm_factory
from gui.Scaleform.daapi.view.battle.shared.crosshair import CrosshairPanelContainer, settings
from gui.Scaleform.daapi.view.battle.shared.crosshair import gm_factory
from gui.Scaleform.daapi.view.battle.shared.crosshair.gm_components import DefaultGunMarkerComponent, SPGGunMarkerComponent
from gui.Scaleform.daapi.view.battle.shared.crosshair.gm_components import GunMarkersComponents
from gui.Scaleform.daapi.view.battle.shared.crosshair.gm_factory import _GunMarkersFactory
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import _SETTINGS_KEYS, _SETTINGS_VIEWS, _SETTINGS_KEY_TO_VIEW_ID
from gui.Scaleform.daapi.view.external_components import ExternalFlashSettings
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.Scaleform.genConsts.GUN_MARKER_VIEW_CONSTANTS import GUN_MARKER_VIEW_CONSTANTS
from gui.Scaleform.locale.SETTINGS import SETTINGS
from gui.battle_control.battle_constants import CROSSHAIR_VIEW_ID
from gui.shared.utils.plugins import PluginsCollection
from helpers import dependency
from helpers import dependency
from helpers import i18n
from skeletons.account_helpers.settings_core import ISettingsCache, ISettingsCore
from skeletons.account_helpers.settings_core import ISettingsCore

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, calculate_version, logWarning

DEFAULT_GUN_MARKER_LINKAGES = gm_factory._GUN_MARKER_LINKAGES

CUSTOM_ARCADE_GUN_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.ARCADE_GUN_MARKER_NAME + '-SERVER'
CUSTOM_SNIPER_GUN_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.SNIPER_GUN_MARKER_NAME + '-SERVER'
CUSTOM_DUAL_GUN_ARCADE_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.DUAL_GUN_ARCADE_MARKER_NAME + '-SERVER'
CUSTOM_DUAL_GUN_SNIPER_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.DUAL_GUN_SNIPER_MARKER_NAME + '-SERVER'
CUSTOM_SPG_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.SPG_GUN_MARKER_NAME + '-SERVER'

CUSTOM_GUN_MARKER_LINKAGES = {
   CUSTOM_ARCADE_GUN_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.GUN_MARKER_LINKAGE,
   CUSTOM_SNIPER_GUN_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.GUN_MARKER_LINKAGE,
   CUSTOM_DUAL_GUN_ARCADE_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.DUAL_GUN_ARCADE_MARKER_LINKAGE,
   CUSTOM_DUAL_GUN_SNIPER_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.DUAL_GUN_SNIPER_MARKER_LINKAGE,
   CUSTOM_SPG_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.GUN_MARKER_SPG_LINKAGE
}

CUSTOM_GUN_MARKER_LINKAGES.update(DEFAULT_GUN_MARKER_LINKAGES)

CUSTOM_AIMING_CIRCLE_SHAPE_OPTIONS = [
    i18n.makeString(SETTINGS.AIM_MIXING_TYPE0),
    i18n.makeString(SETTINGS.AIM_MIXING_TYPE1),
    i18n.makeString(SETTINGS.AIM_MIXING_TYPE2),
    i18n.makeString(SETTINGS.AIM_MIXING_TYPE3)
]
CUSTOM_CROSSHAIR_SHAPE_OPTIONS = [
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE0),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE1),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE2),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE3),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE4),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE5),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE6),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE7),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE8),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE9),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE10),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE11),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE12),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE13),
    i18n.makeString(SETTINGS.AIM_GUNTAG_TYPE14)
]


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.reticleScaleFactor = 1
        self.initialized = False
        self.reticleFlashObject = None
        self.primaryReticle = None
        self.customServerReticle = None
        self.customServerReticleSettings = {'gunTag': 0, 'gunTagType': 0, 'mixing': 0, 'mixingType': 0}
        self.enableSpgStrategicReticle = False
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'gunMarkerMinimumSize': 0,
            'percentCorrection': 100,
            'showClientAndServerReticleBeta': False,
            'showServerSpgStrategicReticle': False,
            'serverReticleAimingCircleShape': 0,
            'serverReticleAimingCircleOpacity': 50,
            'serverReticleGunMarkerShape': 0,
            'serverReticleGunMarkerOpacity': 50
        }
        self.i18n = {
            'UI_description': 'Reticle',
            'UI_version': calculate_version(self.version),
            'UI_setting_showClientAndServerReticleBeta_text': 'Client and Server Reticle (Beta)',
            'UI_setting_showClientAndServerReticleBeta_tooltip': 'Show both client and server reticle simultaneously',
            'UI_setting_showServerSpgStrategicReticle_text': 'SPG Strategic Reticle',
            'UI_setting_showServerSpgStrategicReticle_tooltip': 'Enable server reticle for SPG strategic mode',
            'UI_setting_gunMarkerMinimumSize_text': 'Gun Marker Minimum Size',
            'UI_setting_gunMarkerMinimumSize_tooltip': 'Minimum size of the gun marker in pixels',
            'UI_setting_percentCorrection_text': 'Reticle Size Correction',
            'UI_setting_percentCorrection_tooltip': 'Adjust the scale factor of the reticle',
            'UI_setting_serverReticleAimingCircleShape_text': 'Aiming Circle Shape',
            'UI_setting_serverReticleAimingCircleShape_tooltip': 'Select the shape of the server aiming circle',
            'UI_setting_serverReticleAimingCircleOpacity_text': 'Aiming Circle Opacity',
            'UI_setting_serverReticleAimingCircleOpacity_tooltip': 'Adjust the opacity of the server aiming circle',
            'UI_setting_serverReticleGunMarkerShape_text': 'Gun Marker Shape',
            'UI_setting_serverReticleGunMarkerShape_tooltip': 'Select the shape of the server gun marker',
            'UI_setting_serverReticleGunMarkerOpacity_text': 'Gun Marker Opacity',
            'UI_setting_serverReticleGunMarkerOpacity_tooltip': 'Adjust the opacity of the server gun marker'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showClientAndServerReticleBeta'),
                self.tb.createControl('showServerSpgStrategicReticle')
            ],
            'column2': [
                self.tb.createSlider('gunMarkerMinimumSize', 0, 32, 1, '{{value}}px'),
                self.tb.createSlider('percentCorrection', 0, 100, 1, '{{value}}%'),
                self.tb.createOptions('serverReticleAimingCircleShape', CUSTOM_AIMING_CIRCLE_SHAPE_OPTIONS),
                self.tb.createSlider('serverReticleAimingCircleOpacity', 0, 100, 1, '{{value}}%'),
                self.tb.createOptions('serverReticleGunMarkerShape', CUSTOM_CROSSHAIR_SHAPE_OPTIONS),
                self.tb.createSlider('serverReticleGunMarkerOpacity', 0, 100, 1, '{{value}}%')
            ]
        }

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)
        if self.data['enabled']:
            aih_constants.GUN_MARKER_MIN_SIZE = aih_constants.GUN_MARKER_MIN_SIZE
            self.reticleScaleFactor = 1
            self.data['showClientAndServerReticle'] = False
        else:
            aih_constants.GUN_MARKER_MIN_SIZE = self.data['gunMarkerMinimumSize']
            correctionFactor = self.data['percentCorrection'] / 100
            self.reticleScaleFactor = 1.71 * correctionFactor + (1 - correctionFactor)
            self.data['showClientAndServerReticle'] = self.data['showClientAndServerReticleBeta']
        if self.data['showClientAndServerReticle']:
            gm_factory._GUN_MARKER_LINKAGES = CUSTOM_GUN_MARKER_LINKAGES
        else:
            gm_factory._GUN_MARKER_LINKAGES = DEFAULT_GUN_MARKER_LINKAGES
        self.customServerReticleSettings['gunTag'] = self.data['serverReticleGunMarkerOpacity']
        self.customServerReticleSettings['gunTagType'] = self.data['serverReticleGunMarkerShape']
        self.customServerReticleSettings['mixing'] = self.data['serverReticleAimingCircleOpacity']
        self.customServerReticleSettings['mixingType'] = self.data['serverReticleAimingCircleShape']
        self.enableSpgStrategicReticle = self.data['showServerSpgStrategicReticle']


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'G-B7Z425MJ3L')


class CustomCrosshairContainer(CrosshairPanelContainer):
    def __init__(self, createMarkers, overrideMarkers, customSettings, enableSpgStrategicReticle):
        super(CrosshairPanelContainer, self).__init__(ExternalFlashSettings(BATTLE_VIEW_ALIASES.CROSSHAIR_PANEL, settings.CROSSHAIR_CONTAINER_SWF, settings.CROSSHAIR_ROOT_PATH, settings.CROSSHAIR_INIT_CALLBACK))
        self._CrosshairPanelContainer__plugins = PluginsCollection(self)
        self._CrosshairPanelContainer__plugins.addPlugins(self._getPlugins())
        self._CrosshairPanelContainer__gunMarkers = None
        self._CrosshairPanelContainer__viewID = CROSSHAIR_VIEW_ID.UNDEFINED
        self._CrosshairPanelContainer__zoomFactor = 0.0
        self._CrosshairPanelContainer__scale = 1.0
        self._CrosshairPanelContainer__distance = 0
        self._CrosshairPanelContainer__hasAmmo = True
        self._CrosshairPanelContainer__callbackDelayer = None
        self._CrosshairPanelContainer__isFaded = False
        self.createMarkers = createMarkers
        self.overrideMarkers = overrideMarkers
        self.customSettings = customSettings
        self.enableSpgStrategicReticle = enableSpgStrategicReticle

    def createGunMarkers(self, markersInfo, vehicleInfo):
        if self._CrosshairPanelContainer__gunMarkers is not None:
            logWarning(config.ID, 'Set of gun markers is already created.')
            return
        else:
            self._CrosshairPanelContainer__setGunMarkers(self.createMarkers(markersInfo, vehicleInfo, self.enableSpgStrategicReticle))
            return

    def invalidateGunMarkers(self, markersInfo, vehicleInfo):
        if self._CrosshairPanelContainer__gunMarkers is None:
            logWarning(config.ID, 'Set of gun markers is not created')
            return
        else:
            newSet = self.overrideMarkers(self._CrosshairPanelContainer__gunMarkers, markersInfo, vehicleInfo, self.enableSpgStrategicReticle)
            self._CrosshairPanelContainer__clearGunMarkers()
            self._CrosshairPanelContainer__setGunMarkers(newSet)
            return

    def setSettings(self, _):
        self.as_setSettingsS(self.getSettingsVo())

    def getSettingsVo(self):
        settingsCore = dependency.instance(ISettingsCore)
        getter = settingsCore.getSetting
        data = {}
        for mode in _SETTINGS_KEYS:
            data[_SETTINGS_KEY_TO_VIEW_ID[mode]] = {
                'centerAlphaValue': 0,
                'centerType': 0,
                'netAlphaValue': 0,
                'netType': 0,
                'reloaderAlphaValue': 0,
                'conditionAlphaValue': 0,
                'cassetteAlphaValue': 0,
                'reloaderTimerAlphaValue': 0,
                'zoomIndicatorAlphaValue': 0,
                'gunTagAlpha': self.customSettings['gunTag'] / 100.0,
                'gunTagType': self.customSettings['gunTagType'],
                'mixingAlpha': self.customSettings['mixing'] / 100.0,
                'mixingType': self.customSettings['mixingType']
            }
        for view in _SETTINGS_VIEWS:
            commonSettings = data.get(view, None)
            if commonSettings is None:
                commonSettings = {}
                data[view] = commonSettings
            commonSettings.update({
                'spgScaleWidgetEnabled': getter(SPGAim.SPG_SCALE_WIDGET),
                'isColorBlind': settingsCore.getSetting(GRAPHICS.COLOR_BLIND)
            })
        return data


class _CustomServerControlMarkersFactory(_GunMarkersFactory):
    def create(self, enableSpgStrategicReticle):
        if self._vehicleInfo.isSPG():
            markers = self._createSPGMarkers(enableSpgStrategicReticle)
        elif self._vehicleInfo.isDualGunVehicle():
            markers = self._createDualGunMarkers()
        else:
            markers = self._createDefaultMarkers()
        return markers

    def _createDualGunMarkers(self):
        return (
         self._createArcadeMarker(CUSTOM_DUAL_GUN_ARCADE_MARKER_NAME),
         self._createSniperMarker(CUSTOM_DUAL_GUN_SNIPER_MARKER_NAME))

    def _createDefaultMarkers(self):
        return (
         self._createArcadeMarker(CUSTOM_ARCADE_GUN_MARKER_NAME),
         self._createSniperMarker(CUSTOM_SNIPER_GUN_MARKER_NAME))

    def _createSPGMarkers(self, enableSpgStrategicReticle):
        if enableSpgStrategicReticle:
            return (self._createArcadeMarker(CUSTOM_ARCADE_GUN_MARKER_NAME), self._createSPGMarker(CUSTOM_SPG_MARKER_NAME))
        else:
            return (self._createArcadeMarker(CUSTOM_ARCADE_GUN_MARKER_NAME),)

    def _createArcadeMarker(self, name):
        dataProvider = self._getMarkerDataProvider(GUN_MARKER_TYPE.SERVER)
        return self._createMarker(DefaultGunMarkerComponent, CROSSHAIR_VIEW_ID.ARCADE, GUN_MARKER_TYPE.SERVER, dataProvider, name)

    def _createSniperMarker(self, name):
        dataProvider = self._getMarkerDataProvider(GUN_MARKER_TYPE.SERVER)
        return self._createMarker(DefaultGunMarkerComponent, CROSSHAIR_VIEW_ID.SNIPER, GUN_MARKER_TYPE.SERVER, dataProvider, name)

    def _createSPGMarker(self, name):
        dataProvider = self._getSPGDataProvider(GUN_MARKER_TYPE.SERVER)
        return self._createMarker(SPGGunMarkerComponent, CROSSHAIR_VIEW_ID.STRATEGIC, GUN_MARKER_TYPE.SERVER, dataProvider, name)


def _createComponents(markersInfo, vehiclesInfo, enableSpgStrategicReticle):
    return GunMarkersComponents(_CustomServerControlMarkersFactory(markersInfo, vehiclesInfo, None).create(enableSpgStrategicReticle))


def _overrideComponents(components, markersInfo, vehiclesInfo, enableSpgStrategicReticle):
    return GunMarkersComponents(_CustomServerControlMarkersFactory(markersInfo, vehiclesInfo, components).create(enableSpgStrategicReticle))


def GetCustomServerCrosshair(customSettings, enableSpgStrategicReticle):
    return CustomCrosshairContainer(_createComponents, _overrideComponents, customSettings, enableSpgStrategicReticle)


@override(AvatarInputHandler.AvatarInputHandler, 'updateClientGunMarker')
def new_AvatarInputHandler_updateClientGunMarker(_, self, pos, direction, size, sizeOffset, relaxTime, collData):
    if self.ctrlModeName in (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.SNIPER):
        size /= config.reticleScaleFactor
    self.ctrl.updateGunMarker(GUN_MARKER_TYPE.CLIENT, pos, direction, size, sizeOffset, relaxTime, collData)


@override(AvatarInputHandler.AvatarInputHandler, 'updateServerGunMarker')
def new_AvatarInputHandler_updateServerGunMarker(_, self, pos, direction, size, sizeOffset, relaxTime, collData):
    if self.ctrlModeName in (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.SNIPER):
        size /= config.reticleScaleFactor
    self.ctrl.updateGunMarker(GUN_MARKER_TYPE.SERVER, pos, direction, size, sizeOffset, relaxTime, collData)


@override(AvatarInputHandler.AvatarInputHandler, 'updateDualAccGunMarker')
def new_AvatarInputHandler_updateDualAccGunMarker(func, self, pos, direction, size, sizeOffset, relaxTime, collData):
    if self.ctrlModeName in (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.SNIPER):
        size /= config.reticleScaleFactor
    func(self, pos, direction, size, sizeOffset, relaxTime, collData)


@override(SharedPage, '__init__')
def new_SharedPage_init(func, self, components=None, external=None):
    func(self, components, external)
    if config.data['showClientAndServerReticle'] is True:
        ensureServerAimingIsEnabled()
        for item in self._external:
            if isinstance(item, CrosshairPanelContainer):
                config.primaryReticle = item

        config.customServerReticle = GetCustomServerCrosshair(config.customServerReticleSettings, config.enableSpgStrategicReticle)
        self._external.append(config.customServerReticle)


def ensureServerAimingIsEnabled():
    settingsCache = dependency.instance(ISettingsCache)
    if not settingsCache.isSynced():
        settingsCache.onSyncCompleted += enableServerAimingViaCallback
    else:
        enableServerAiming()


def enableServerAiming():
    settingsCore = dependency.instance(ISettingsCore)
    if settingsCore.getSetting('useServerAim') is 0:
        settingsCore.isChangesConfirmed = True
        settingsCore.applySettings({'useServerAim': True})
        confirmators = settingsCore.applyStorages(True)
        settingsCore.confirmChanges(confirmators)
        settingsCore.clearStorages()


def enableServerAimingViaCallback():
    settingsCache = dependency.instance(ISettingsCache)
    settingsCache.onSyncCompleted -= enableServerAimingViaCallback
    enableServerAiming()


@override(AvatarInputHandler.AvatarInputHandler, 'showClientGunMarkers')
def new_AvatarInputHandler_showClientGunMarkers(func, self, isShown):
    if config.data['showClientAndServerReticle'] is True:
        self.ctrl.setGunMarkerFlag(isShown, GUN_MARKER_FLAG.CLIENT_MODE_ENABLED)
        self.ctrl.setGunMarkerFlag(isShown, GUN_MARKER_FLAG.SERVER_MODE_ENABLED)
    else:
        func(self, isShown)


@override(AvatarInputHandler.AvatarInputHandler, 'showServerGunMarker')
def new_AvatarInputHandler_showServerGunMarker(func, self, isShown):
    if config.data['showClientAndServerReticle'] is True:
        if not BattleReplay.isPlaying():
            BattleReplay.g_replayCtrl.setUseServerAim(False)
            self.ctrl.setGunMarkerFlag(isShown, GUN_MARKER_FLAG.SERVER_MODE_ENABLED)
    else:
        func(self, isShown)


@override(AvatarInputHandler.AvatarInputHandler, '_AvatarInputHandler__onArenaStarted')
def new_AvatarInputHandler_onArenaStarted(func, self, period, *args):
    if config.data['showClientAndServerReticle'] is True:
        isBattle = period == ARENA_PERIOD.BATTLE
        self._AvatarInputHandler__isArenaStarted = isBattle
        self.ctrl.setGunMarkerFlag(isBattle, GUN_MARKER_FLAG.CONTROL_ENABLED)
        self.showServerGunMarker(isBattle)
        self.showClientGunMarkers(isBattle)
    else:
        func(self, period, *args)


@override(gm_factory._ControlMarkersFactory, '_getMarkerType')
def new_ControlMarkersFactory_getMarkerType(func, self):
    if config.data['showClientAndServerReticle'] is True:
        return GUN_MARKER_TYPE.CLIENT
    else:
        return func(self)


# @override(VehicleGunRotator.VehicleGunRotator, 'clientMode', (lambda self: self._VehicleGunRotator__clientMode))
@override(VehicleGunRotator.VehicleGunRotator, 'clientMode')
def new_VehicleGunRotator_clientMode_setter(func, self, value):
    if config.data['showClientAndServerReticle'] is True:
        if self.clientMode == value:
            return
        self._VehicleGunRotator__clientMode = value
        if not self._VehicleGunRotator__isStarted:
            return
        if self.clientMode:
            self._VehicleGunRotator__time = BigWorld.time()
            self.stopTrackingOnServer()
    else:
        func.fset(self, value)


@override(VehicleGunRotator.VehicleGunRotator, 'setShotPosition')
def new_VehicleGunRotator_setShotPosition(func, self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh=False):
    if config.data['showClientAndServerReticle'] is True:
        if self.clientMode and not self.showServerMarker and not forceValueRefresh:
            return
        else:
            dispersionAngles = self._VehicleGunRotator__dispersionAngles[:]
            dispersionAngles[0] = dispersionAngle
            if not self.clientMode and VehicleGunRotator.VehicleGunRotator.USE_LOCK_PREDICTION:
                lockEnabled = BigWorld.player().inputHandler.getAimingMode(AIMING_MODE.TARGET_LOCK)
                if lockEnabled:
                    predictedTargetPos = self.predictLockedTargetShotPoint()
                    if predictedTargetPos is None:
                        return
                    dirToTarget = predictedTargetPos - shotPos
                    dirToTarget.normalise()
                    shotDir = Math.Vector3(shotVec)
                    shotDir.normalise()
                    if shotDir.dot(dirToTarget) > 0.0:
                        return
            markerPosition = self._VehicleGunRotator__getGunMarkerPosition(shotPos, shotVec, dispersionAngles)
            mPos, mDir, mSize, _, mSizeOffset, collData = markerPosition
            if self.clientMode and self.showServerMarker:
                self._avatar.inputHandler.updateServerGunMarker(mPos, mDir, mSize, mSizeOffset, SERVER_TICK_LENGTH, collData)
            return

    else:
        func(self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh)
    return


@override(VehicleGunRotator.VehicleGunRotator, 'updateRotationAndGunMarker')
def new_VehicleGunRotator_updateRotationAndGunMarker(func, self, shotPoint, timeDiff):
    func(self, shotPoint, timeDiff)
    if config.data['showClientAndServerReticle'] and not self.clientMode:
        shotPos, shotVec = self.getCurShotPosition()
        markerPosition = self._VehicleGunRotator__getGunMarkerPosition(shotPos, shotVec, self._VehicleGunRotator__dispersionAngles)
        mPos, mDir, mSize, _, mSizeOffset, collData = markerPosition
        relaxTime = 0.001
        if not (BattleReplay.g_replayCtrl.isPlaying and BattleReplay.g_replayCtrl.isUpdateGunOnTimeWarp):
            relaxTime = self._VehicleGunRotator__ROTATION_TICK_LENGTH
        self._avatar.inputHandler.updateServerGunMarker(mPos, mDir, mSize, mSizeOffset, relaxTime, collData)
