# -*- coding: utf-8 -*-
import aih_constants
from AvatarInputHandler import gun_marker_ctrl
from AvatarInputHandler.gun_marker_ctrl import _GunMarkersDPFactory, _EmptyGunMarkerController, _DualAccMarkerController, _GunMarkersDecorator, _SPGGunMarkerController, _DefaultGunMarkerController, _MARKER_TYPE
from BattleReplay import g_replayCtrl
from Event import SafeEvent
from VehicleGunRotator import VehicleGunRotator
from constants import SERVER_TICK_LENGTH
from gui.Scaleform.daapi.view.battle.shared.crosshair import gm_factory
from gui.Scaleform.daapi.view.battle.shared.crosshair.container import CrosshairPanelContainer
from gui.Scaleform.daapi.view.battle.shared.crosshair.gm_factory import _GunMarkersFactories, _GUN_MARKER_LINKAGES, _DevControlMarkersFactory, _OptionalMarkersFactory, _EquipmentMarkersFactory
from gui.Scaleform.genConsts.GUN_MARKER_VIEW_CONSTANTS import GUN_MARKER_VIEW_CONSTANTS as _CONSTANTS
from gui.battle_control.controllers.crosshair_proxy import CrosshairDataProxy

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, calculate_version

CLIENT = _MARKER_TYPE.CLIENT
SERVER = _MARKER_TYPE.SERVER
DUAL_ACC = _MARKER_TYPE.DUAL_ACC
EMPTY = _MARKER_TYPE.UNDEFINED

DEV_FACTORIES_COLLECTION = (
    _DevControlMarkersFactory,
    _OptionalMarkersFactory,
    _EquipmentMarkersFactory
)
LINKAGES = {
    _CONSTANTS.DEBUG_SPG_GUN_MARKER_NAME: _CONSTANTS.GUN_MARKER_SPG_LINKAGE,
    _CONSTANTS.DEBUG_ARCADE_GUN_MARKER_NAME: _CONSTANTS.GUN_MARKER_LINKAGE,
    _CONSTANTS.DEBUG_SNIPER_GUN_MARKER_NAME: _CONSTANTS.GUN_MARKER_LINKAGE,
    _CONSTANTS.DEBUG_DUAL_GUN_ARCADE_MARKER_NAME: _CONSTANTS.DUAL_GUN_ARCADE_MARKER_LINKAGE,
    _CONSTANTS.DEBUG_DUAL_GUN_SNIPER_MARKER_NAME: _CONSTANTS.DUAL_GUN_SNIPER_MARKER_LINKAGE
}

_GUN_MARKER_LINKAGES.update(LINKAGES)
aih_constants.GUN_MARKER_MIN_SIZE = 10.0
aih_constants.SPG_GUN_MARKER_MIN_SIZE = 20.0


class ConfigInterface(DriftkingsConfigInterface):
    
    def __init__(self):
        self.onModSettingsChanged = SafeEvent()
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.9.0 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'replaceOriginalCircle': True,
            'useServerDispersion': False,
            'dispersionCircleScale': 1.0
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_replaceOriginalCircle_text': 'Replace aiming circle to dispersion circle',
            'UI_setting_replaceOriginalCircle_tooltip': 'Replace the original aiming circle to dispersion circle (To improve accuracy)',
            'UI_setting_useServerDispersion_text': 'Use server side circle of dispersion',
            'UI_setting_useServerDispersion_tooltip': 'Change client to server circle of dispersion(not working in replays)',
            'UI_setting_dispersionCircleScale_text': 'Scale dispersion circle (UI)',
            'UI_setting_dispersionCircleScale_tooltip': '',
            'UI_setting_scale_size': 'X'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        percent = self.i18n['UI_setting_scale_size']
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('replaceOriginalCircle'),
                self.tb.createControl('useServerDispersion')
            ],
            'column2': [
                self.tb.createSlider('dispersionCircleScale', 1.0, 100.0, 1.0, '{{value}}%s' % percent)
            ]
        }


def getSetting(gunMakerType):
    if gunMakerType == CLIENT:
        return config.data['replaceOriginalCircle']
    elif gunMakerType == SERVER:
        return config.data['useServerDispersion']
    return False


class DefaultGunMarkerController(_DefaultGunMarkerController):

    def __init__(self, gunMakerType, dataProvider, **kwargs):
        super(DefaultGunMarkerController, self).__init__(gunMakerType, dataProvider, **kwargs)
        self.__scaleConfig = float(config.data['dispersionCircleScale']) if getSetting(gunMakerType) else 1.0

    def __updateScreenRatio(self):
        super(DefaultGunMarkerController, self).__updateScreenRatio()
        self.__screenRatio *= self.__scaleConfig


class SPGController(_SPGGunMarkerController):

    def __init__(self, gunMakerType, dataProvider, **kwargs):
        super(SPGController, self).__init__(gunMakerType, dataProvider, **kwargs)
        self.__scaleConfig = float(config.data['dispersionCircleScale']) if getSetting(
            gunMakerType) else 1.0

    def _updateDispersionData(self):
        self._size *= self.__scaleConfig
        dispersionAngle = self._gunRotator.dispersionAngle * self.__scaleConfig
        isServerAim = self._gunMarkerType == SERVER
        if g_replayCtrl.isPlaying and g_replayCtrl.isClientReady:
            d, s = g_replayCtrl.getSPGGunMarkerParams()
            if d != -1 and s != -1:
                dispersionAngle = d
        elif g_replayCtrl.isRecording and (g_replayCtrl.isServerAim and isServerAim or not isServerAim):
            g_replayCtrl.setSPGGunMarkerParams(dispersionAngle, 0)
        self._dataProvider.setupConicDispersion(dispersionAngle)


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class DispersionCircle(object):

    def __init__(self):
        self.enabled = False
        self.server = False
        config.onModSettingsChanged += self.onModSettingsChanged
        override(gm_factory, 'createComponents', self.createOverrideComponents)
        override(gm_factory, 'overrideComponents', self.createOverrideComponents)
        override(gun_marker_ctrl, 'createGunMarker', self.createGunMarker)
        override(gun_marker_ctrl, 'useDefaultGunMarkers', self.useDefaultGunMarkers)
        override(gun_marker_ctrl, 'useClientGunMarker', self.useGunMarker)
        override(gun_marker_ctrl, 'useServerGunMarker', self.useGunMarker)
        override(VehicleGunRotator, 'applySettings', self.applySettings)
        override(VehicleGunRotator, 'setShotPosition', self.setShotPosition)
        override(CrosshairDataProxy, '__onServerGunMarkerStateChanged', self.onServerGunMarkerStateChanged)
        override(CrosshairPanelContainer, 'setGunMarkerColor', self.setGunMarkerColor)

    def createOverrideComponents(self, func, *args):
        if not self.server:
            return func(*args)
        player = getPlayer()
        player.enableServerAim(True)
        if len(args) == 2:
            return _GunMarkersFactories(*DEV_FACTORIES_COLLECTION).create(*args)
        return _GunMarkersFactories(*DEV_FACTORIES_COLLECTION).override(*args)

    def useDefaultGunMarkers(self, func, *args, **kwargs):
        return not self.server or func(*args, **kwargs)

    def useGunMarker(self, func, *args, **kwargs):
        return self.server or func(*args, **kwargs)

    def applySettings(self, func, *args, **kwargs):
        return None if self.server else func(*args, **kwargs)

    def setShotPosition(self, func, b_self, vehicleID, sPos, sVec, dispersionAngle, forceValueRefresh=False):
        func(b_self, vehicleID, sPos, sVec, dispersionAngle, forceValueRefresh=forceValueRefresh)
        if not self.server:
            return
        m_position = b_self._VehicleGunRotator__getGunMarkerPosition(sPos, sVec, b_self.getCurShotDispersionAngles())
        endPos, direction, diameter, idealDiameter, dualAccDiameter, dualAccIdealDiameter, collData = m_position
        size = (diameter, idealDiameter)
        b_self._avatar.inputHandler.updateServerGunMarker(endPos, direction, size, SERVER_TICK_LENGTH, collData)

    def onServerGunMarkerStateChanged(self, func, *args, **kwargs):
        return None if self.server else func(*args, **kwargs)

    def setGunMarkerColor(self, func, b_self, markerType, color):
        if self.server and markerType == CLIENT:
            func(b_self, SERVER, color)
        return func(b_self, markerType, color)

    def onModSettingsChanged(self):
        self.enabled = config.data['enabled'] and not g_replayCtrl.isPlaying
        if self.enabled:
            self.server = config.data['useServerDispersion']
        else:
            self.server = False

    def createGunMarker(self, func, b_self):
        if not self.enabled:
            return func(b_self)
        factory = _GunMarkersDPFactory()
        if b_self:
            client = SPGController(CLIENT, factory.getClientSPGProvider())
            server = SPGController(SERVER, factory.getServerSPGProvider())
            dual = _EmptyGunMarkerController(EMPTY, None)
        else:
            client = DefaultGunMarkerController(CLIENT, factory.getClientProvider())
            server = DefaultGunMarkerController(SERVER, factory.getServerProvider())
            dual = _DualAccMarkerController(DUAL_ACC, factory.getDualAccuracyProvider())
        return _GunMarkersDecorator(client, server, dual)
