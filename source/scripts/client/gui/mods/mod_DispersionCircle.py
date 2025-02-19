# -*- coding: utf-8 -*-
import aih_constants
from AvatarInputHandler import gun_marker_ctrl
from BattleReplay import g_replayCtrl
from Event import SafeEvent
from VehicleGunRotator import VehicleGunRotator
from account_helpers.settings_core.settings_constants import GAME
from constants import SERVER_TICK_LENGTH
from gui.Scaleform.daapi.view.battle.shared.crosshair import gm_factory
from gui.Scaleform.daapi.view.battle.shared.crosshair.container import CrosshairPanelContainer
from gui.Scaleform.genConsts.GUN_MARKER_VIEW_CONSTANTS import GUN_MARKER_VIEW_CONSTANTS as _CONSTANTS
from gui.battle_control.controllers.crosshair_proxy import CrosshairDataProxy
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, calculate_version, isReplay


CLIENT = gun_marker_ctrl._MARKER_TYPE.CLIENT
SERVER = gun_marker_ctrl._MARKER_TYPE.SERVER
DUAL_ACC = gun_marker_ctrl._MARKER_TYPE.DUAL_ACC
EMPTY = gun_marker_ctrl._MARKER_TYPE.UNDEFINED

DEV_FACTORIES_COLLECTION = (
    gm_factory._DevControlMarkersFactory,
    gm_factory._OptionalMarkersFactory,
    gm_factory._EquipmentMarkersFactory
)
LINKAGES = {
    _CONSTANTS.DEBUG_SPG_GUN_MARKER_NAME: _CONSTANTS.GUN_MARKER_SPG_LINKAGE,
    _CONSTANTS.DEBUG_ARCADE_GUN_MARKER_NAME: _CONSTANTS.GUN_MARKER_LINKAGE,
    _CONSTANTS.DEBUG_SNIPER_GUN_MARKER_NAME: _CONSTANTS.GUN_MARKER_LINKAGE,
    _CONSTANTS.DEBUG_DUAL_GUN_ARCADE_MARKER_NAME: _CONSTANTS.DUAL_GUN_ARCADE_MARKER_LINKAGE,
    _CONSTANTS.DEBUG_DUAL_GUN_SNIPER_MARKER_NAME: _CONSTANTS.DUAL_GUN_SNIPER_MARKER_LINKAGE
}

gm_factory._GUN_MARKER_LINKAGES.update(LINKAGES)

aih_constants.GUN_MARKER_MIN_SIZE = 14.0
aih_constants.SPG_GUN_MARKER_MIN_SIZE = 24.0

REPLACE = {CLIENT, DUAL_ACC}

base_before_override = {}


def cancelOverride(orig, prop, replaced_name):
    class_name = orig.__name__
    if prop.startswith('__'):
        prop = '_{0}{1}'.format(class_name, prop)
    full_name_with_class = '{0}.{1}*{2}'.format(class_name, prop, replaced_name)
    if full_name_with_class in base_before_override:
        setattr(orig, prop, base_before_override.pop(full_name_with_class))
        print 'cancelOverrode: override {} removed'.format(full_name_with_class)


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.onModSettingsChanged = SafeEvent()
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.0.0 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'replaceOriginalCircle': True,
            'useServerDispersion': True,
            'dispersionCircleScale': 1.0,
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
            'UI_setting_dispersionCircleScale_format': 'x'
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
                self.tb.createSlider('dispersionCircleScale', 1.0, 100.0, 1.0, '{{value}}%s' % scale)
            ]
        }

    # noinspection PyProtectedMember
    # def onApplySettings(self, settings):
    #    super(ConfigInterface, self).onApplySettings(settings)



def getSetting(gunMakerType):
    replace = config.data['replaceOriginalCircle']
    if gunMakerType == SERVER:
        return config.data['useServerDispersion'] or replace
    elif gunMakerType in REPLACE:
        return replace
    return False


class _DefaultGunMarkerController(gun_marker_ctrl._DefaultGunMarkerController):

    def __init__(self, gunMakerType, dataProvider, **kwargs):
        super(_DefaultGunMarkerController, self).__init__(gunMakerType, dataProvider, **kwargs)
        self.__scaleConfig = float(config.data['dispersionCircleScale']) if getSetting(gunMakerType) else 1.0

    def __updateScreenRatio(self):
        super(_DefaultGunMarkerController, self).__updateScreenRatio()
        self.__screenRatio *= self.__scaleConfig


class _DualAccMarkerController(_DefaultGunMarkerController):

    def _replayReader(self, replayCtrl):
        return replayCtrl.getDualAccMarkerSize

    def _replayWriter(self, replayCtrl):
        return replayCtrl.setDualAccMarkerSize


class SPGController(gun_marker_ctrl._SPGGunMarkerController):

    def __init__(self, gunMakerType, dataProvider, **kwargs):
        super(SPGController, self).__init__(gunMakerType, dataProvider, **kwargs)
        self.__scaleConfig = float(config.data['dispersionCircleScale']) if getSetting(gunMakerType) else 1.0

    def _updateDispersionData(self):
        self._size *= self.__scaleConfig
        dispersionAngle = self._gunRotator.dispersionAngle * self.__scaleConfig
        isServerAim = self._gunMarkerType == SERVER
        if g_replayCtrl.isRecording and (g_replayCtrl.isServerAim and isServerAim or not isServerAim):
            g_replayCtrl.setSPGGunMarkerParams(dispersionAngle, 0.0)
        self._dataProvider.setupConicDispersion(dispersionAngle)


def disable_server_aim():
    settingsCore = dependency.instance(ISettingsCore)
    if settingsCore.getSetting(GAME.ENABLE_SERVER_AIM):
        settingsCore.applySettings({GAME.ENABLE_SERVER_AIM: 0})
        settingsCore.applyStorages(False)
        settingsCore.clearStorages()


class DispersionCircle(object):

    def __init__(self):
        config.onModSettingsChanged += self.onModSettingsChanged

    def addServerCrossOverrides(self):
        override(gm_factory, 'createComponents', self.createOverrideComponents)
        override(gm_factory, 'overrideComponents', self.createOverrideComponents)
        override(gun_marker_ctrl, 'useDefaultGunMarkers', self.useDefaultGunMarkers)
        override(gun_marker_ctrl, 'useClientGunMarker', self.useGunMarker)
        override(gun_marker_ctrl, 'useServerGunMarker', self.useGunMarker)
        override(VehicleGunRotator, 'applySettings', self.onPass)
        override(VehicleGunRotator, 'setShotPosition', self.setShotPosition)
        override(CrosshairDataProxy, '__onServerGunMarkerStateChanged', self.onPass)
        override(CrosshairPanelContainer, 'setGunMarkerColor', self.setGunMarkerColor)

    @staticmethod
    def cancelServerCrossOverride():
        cancelOverride(gm_factory, 'createComponents', 'createOverrideComponents')
        cancelOverride(gm_factory, 'overrideComponents', 'createOverrideComponents')
        cancelOverride(gun_marker_ctrl, 'useDefaultGunMarkers', 'useDefaultGunMarkers')
        cancelOverride(gun_marker_ctrl, 'useClientGunMarker', 'useGunMarker')
        cancelOverride(gun_marker_ctrl, 'useServerGunMarker', 'useGunMarker')
        cancelOverride(VehicleGunRotator, 'applySettings', 'onPass')
        cancelOverride(VehicleGunRotator, 'setShotPosition', 'setShotPosition')
        cancelOverride(CrosshairDataProxy, '__onServerGunMarkerStateChanged', 'onPass')
        cancelOverride(CrosshairPanelContainer, 'setGunMarkerColor', 'setGunMarkerColor')

    @staticmethod
    def createOverrideComponents(base, *args):
        disable_server_aim()
        getPlayer().cell.setServerMarker(True)
        if len(args) == 2:
            return gm_factory._GunMarkersFactories(*DEV_FACTORIES_COLLECTION).create(*args)
        return gm_factory._GunMarkersFactories(*DEV_FACTORIES_COLLECTION).override(*args)

    @staticmethod
    def useDefaultGunMarkers(*args, **kwargs):
        return False

    @staticmethod
    def useGunMarker(*args, **kwargs):
        return True

    @staticmethod
    def onPass(*args, **kwargs):
        pass

    @staticmethod
    def setShotPosition(func, self, vehicleID, sPos, sVec, dispersionAngle, _=False):
        m_position = self._VehicleGunRotator__getGunMarkerPosition(sPos, sVec, self.getCurShotDispersionAngles())
        mPos, mDir, mSize, dualAccSize, mSizeOffset, collData = m_position
        self._avatar.inputHandler.updateServerGunMarker(mPos, mDir, mSize, mSizeOffset, SERVER_TICK_LENGTH, collData)

    @staticmethod
    def setGunMarkerColor(func, self, markerType, color):
        if markerType == CLIENT:
            func(self, SERVER, color)
        return func(self, markerType, color)

    def onModSettingsChanged(self):
        if isReplay():
            return
        replace = config.data['enabled'] and config.data['replaceOriginalCircle']
        server = config.data['enabled'] and config.data['useServerDispersion']
        if replace or server:
            override(gun_marker_ctrl, 'createGunMarker', self.createGunMarker)
        else:
            cancelOverride(gun_marker_ctrl, 'createGunMarker', 'createGunMarker')
        if server:
            self.addServerCrossOverrides()
        else:
            self.cancelServerCrossOverride()

    @staticmethod
    def createGunMarker(_, isStrategic):
        factory = gun_marker_ctrl._GunMarkersDPFactory()
        if isStrategic:
            client = SPGController(CLIENT, factory.getClientSPGProvider())
            server = SPGController(SERVER, factory.getServerSPGProvider())
            dual = gun_marker_ctrl._EmptyGunMarkerController(EMPTY, None)
        else:
            client = _DefaultGunMarkerController(CLIENT, factory.getClientProvider())
            server = _DefaultGunMarkerController(SERVER, factory.getServerProvider())
            dual = _DualAccMarkerController(DUAL_ACC, factory.getDualAccuracyProvider())
        return gun_marker_ctrl._GunMarkersDecorator(client, server, dual)


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')
dispersion_circle = DispersionCircle()
dispersion_circle.onModSettingsChanged()


def fini():
    config.onModSettingsChanged -= dispersion_circle.onModSettingsChanged
