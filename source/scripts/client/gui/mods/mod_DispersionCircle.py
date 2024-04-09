# -*- coding: utf-8 -*-
import aih_constants
from AvatarInputHandler import gun_marker_ctrl
from BattleReplay import BattleReplay, g_replayCtrl
from Event import SafeEvent
from VehicleGunRotator import VehicleGunRotator
from constants import SERVER_TICK_LENGTH
from gui.Scaleform.daapi.view.battle.shared.crosshair import gm_factory
from gui.Scaleform.daapi.view.battle.shared.crosshair.container import CrosshairPanelContainer
from gui.Scaleform.genConsts.GUN_MARKER_VIEW_CONSTANTS import GUN_MARKER_VIEW_CONSTANTS as _CONSTANTS
from gui.battle_control.controllers.crosshair_proxy import CrosshairDataProxy

from DriftkingsCore import SimpleConfigInterface, Analytics, override, getPlayer

#
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
aih_constants.GUN_MARKER_MIN_SIZE = 10.0
aih_constants.SPG_GUN_MARKER_MIN_SIZE = 20.0


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.7.5 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': False,
            'replaceOriginalCircle': True,
            'useServerDispersion': True,
            'dispersionCircleScale': 1.0,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_replaceOriginalCircle_text': 'Replace Original Circle',
            'UI_setting_replaceOriginalCircle_tooltip': '',
            'UI_setting_useServerDispersion_text': 'Enable server scope (extra lap)',
            'UI_setting_useServerDispersion_tooltip': 'Enabling the feature will create an extra server lapping circle.',
            'UI_setting_dispersionCircleScale_text': 'Circle size multiplier 30-100% (0.3-1.0)',
            'UI_setting_dispersionCircleScale_tooltip': 'This parameter affects what the additional summation circle will be in the result.\n '
                                                        'If the value is 0.3 (30%), then the circle will be the minimum possible,\n '
                                                        'and at 1.0 (100%) - the maximum, i.e. without changes.\n'
                                                        'It is not recommended to set a value lower than 65%.',
            'UI_setting_scale_size': '%'
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


class Events(object):
    def __init__(self):
        self.onModSettingsChanged = SafeEvent()
        super(Events, self).__init__()


g_events = Events()
config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


def getSetting(gunMakerType):
    if gunMakerType == CLIENT:
        return config.data['replaceOriginalCircle']
    elif gunMakerType == SERVER:
        return config.data['useServerDispersion']
    return False


class _DefaultGunMarkerController(gun_marker_ctrl._DefaultGunMarkerController):

    def __init__(self, gunMakerType, dataProvider, **kwargs):
        super(_DefaultGunMarkerController, self).__init__(gunMakerType, dataProvider, **kwargs)
        self.__scaleConfig = float(config.data['dispersionCircleScale']) if getSetting(gunMakerType) else 1.0

    def __updateScreenRatio(self):
        super(_DefaultGunMarkerController, self).__updateScreenRatio()
        self.__screenRatio *= self.__scaleConfig


class SPGController(gun_marker_ctrl._SPGGunMarkerController):

    def __init__(self, gunMakerType, dataProvider, **kwargs):
        super(SPGController, self).__init__(gunMakerType, dataProvider, **kwargs)
        self.__scaleConfig = float(config.data['dispersionCircleScale']) if getSetting(gunMakerType) else 1.0

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


class DispersionCircle(object):

    def __init__(self):
        self.enabled = False
        self.server = False
        g_events.onModSettingsChanged += self.onModSettingsChanged
        override(BattleReplay, 'setUseServerAim', self.replaySetUseServerAim)
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

    def replaySetUseServerAim(self, func, replay, enabled):
        return func(replay, False if self.server else enabled)

    def createOverrideComponents(self, func, *args):
        if not self.server:
            return func(*args)
        player = getPlayer()
        player.enableServerAim(True)
        if len(args) == 2:
            return gm_factory._GunMarkersFactories(*DEV_FACTORIES_COLLECTION).create(*args)
        return gm_factory._GunMarkersFactories(*DEV_FACTORIES_COLLECTION).override(*args)

    def createGunMarker(self, func, isStrategic):
        if not self.enabled:
            return func(isStrategic)
        factory = gun_marker_ctrl._GunMarkersDPFactory()
        if isStrategic:
            client = SPGController(CLIENT, factory.getClientSPGProvider())
            server = SPGController(SERVER, factory.getServerSPGProvider())
            dual = gun_marker_ctrl._EmptyGunMarkerController(EMPTY, None)
        else:
            client = _DefaultGunMarkerController(CLIENT, factory.getClientProvider())
            server = _DefaultGunMarkerController(SERVER, factory.getServerProvider())
            dual = gun_marker_ctrl._DualAccMarkerController(DUAL_ACC, factory.getDualAccuracyProvider())
        return gun_marker_ctrl._GunMarkersDecorator(client, server, dual)

    def useDefaultGunMarkers(self, func, *args, **kwargs):
        return not self.server or func(*args, **kwargs)

    def useGunMarker(self, func, *args, **kwargs):
        return self.server or func(*args, **kwargs)

    def applySettings(self, func, *args, **kwargs):
        return None if self.server else func(*args, **kwargs)

    def setShotPosition(self, func, bSelf, vehicleID, sPos, sVec, dispersionAngle, forceValueRefresh=False):
        func(bSelf, vehicleID, sPos, sVec, dispersionAngle, forceValueRefresh=forceValueRefresh)
        if not self.server:
            return
        m_position = bSelf._VehicleGunRotator__getGunMarkerPosition(sPos, sVec, bSelf.getCurShotDispersionAngles())
        endPos, direction, diameter, idealDiameter, dualAccDiameter, dualAccIdealDiameter, collData = m_position
        size = (diameter, idealDiameter)
        bSelf._avatar.inputHandler.updateServerGunMarker(endPos, direction, size, SERVER_TICK_LENGTH, collData)

    def onServerGunMarkerStateChanged(self, func, *args, **kwargs):
        return None if self.server else func(*args, **kwargs)

    def setGunMarkerColor(self, func, cr_panel, markerType, color):
        if self.server and markerType == CLIENT:
            func(cr_panel, SERVER, color)
        return func(cr_panel, markerType, color)

    def onModSettingsChanged(self):
        self.enabled = config.data['enabled'] and not g_replayCtrl.isPlaying
        if self.enabled:
            self.server = config.data['useServerDispersion']
        else:
            self.server = False


dispersion_circle = DispersionCircle()
