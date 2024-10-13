# -*- coding: utf-8 -*-
import BigWorld
from BattleReplay import g_replayCtrl
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import _LogViewComponent, DamageLogPanel
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE as _ETYPE
from gui.battle_control.controllers import debug_ctrl
# from constants import ATTACK_REASONS, SPECIAL_VEHICLE_HEALTH
# from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin
# from gui.battle_control import avatar_getter
# from helpers import dependency
# from PlayerEvents import g_playerEvents
# from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, calculate_version  # , xvmInstalled


class ConfigInterface(DriftkingsConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.version = '1.4.0 (%(file_compile_date)s)'
        self.data = {
            'enabled': True,
            'logSwapper': True,
            'wgLogHideCritics': True,
            'wgLogHideBlock': True,
            'wgLogHideAssist': True,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_logSwapper_text': 'Enable Reverse Log.',
            'UI_setting_logSwapper_tooltip': 'Reverses the position of the damage log.',
            'UI_setting_wgLogHideCritics_text': 'WG Log Hide Critics',
            'UI_setting_wgLogHideCritics_tooltip': '',
            'UI_setting_wgLogHideBlock_text': 'WG Log Hide Block',
            'UI_setting_wgLogHideBlock_tooltip': '',
            'UI_setting_wgLogHideAssist_text': 'WG Log Hide Assist',
            'UI_setting_wgLogHideAssist_tooltip': ''
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('logSwapper'),
                self.tb.createControl('wgLogHideCritics'),
                self.tb.createControl('wgLogHideBlock'),
                self.tb.createControl('wgLogHideAssist')
            ],
            'column2': []}


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


debug_ctrl._UPDATE_INTERVAL = 0.4


@override(debug_ctrl.DebugController, 'setViewComponents')
def setViewComponents(func, self, *args):
    self._debugPanelUI = args


@override(debug_ctrl.DebugController, '_update')
def updateDebug(func, self):
    fps = BigWorld.getFPS()[1]
    if g_replayCtrl.isPlaying:
        fpsReplay = g_replayCtrl.fps
        ping = g_replayCtrl.ping
        isLaggingNow = g_replayCtrl.isLaggingNow
    else:
        fpsReplay = -1
        isLaggingNow = BigWorld.statLagDetected()
        ping = BigWorld.statPing()
        self.statsCollector.update()
        if g_replayCtrl.isRecording:
            g_replayCtrl.setFpsPingLag(fps, ping, isLaggingNow)

    try:
        ping = int(ping)
        fps = int(fps)
        fpsReplay = int(fpsReplay)
    except (ValueError, OverflowError):
        fps = ping = fpsReplay = 0

    if self._debugPanelUI is not None:
        for control in self._debugPanelUI:
            control.updateDebugInfo(ping, fps, isLaggingNow, fpsReplay=fpsReplay)


class WGLogs(object):
    BASE_WG_LOGS = (DamageLogPanel._addToTopLog, DamageLogPanel._updateTopLog,
                    DamageLogPanel._updateBottomLog, DamageLogPanel._addToBottomLog)

    def __init__(self):
        self.validated = {}
        override(_LogViewComponent, 'addToLog', self.new__addToLog)

    def new__addToLog(self, func, component, event):
        if config.data['enabled']:
            return func(component, [e for e in event if not self.validated.get(e.getType(), False)])
        return func(component, event)

    @staticmethod
    def validateSettings():
        return {
            _ETYPE.RECEIVED_CRITICAL_HITS: config.data['wgLogHideCritics'],
            _ETYPE.BLOCKED_DAMAGE: config.data['wgLogHideBlock'],
            _ETYPE.ASSIST_DAMAGE: config.data['wgLogHideAssist'],
            _ETYPE.STUN: config.data['wgLogHideAssist']
        }


g_logs = WGLogs()

DamageLogPanel._addToTopLog, DamageLogPanel._updateTopLog, DamageLogPanel._updateBottomLog, DamageLogPanel._addToBottomLog = reversed(g_logs.BASE_WG_LOGS) if config.data['logSwapper'] else g_logs.BASE_WG_LOGS

# class Squad(object):
#    sessionProvider = dependency.descriptor(IBattleSessionProvider)
#    __slots__ = ('__squad_mans',)

#    def __init__(self):
#        self.__squad_mans = set()

#    def start(self):
#        g_playerEvents.onAvatarReady += self.updateSquadMans
#        dynSquads = self.sessionProvider.dynamic.dynSquads
#        if dynSquads is not None:
#            dynSquads.onDynSquadCreatedOrJoined += self.updateSquadMans

#    def stop(self):
#        g_playerEvents.onAvatarReady -= self.updateSquadMans
#        dynSquads = self.sessionProvider.dynamic.dynSquads
#        if dynSquads is not None:
#            dynSquads.onDynSquadCreatedOrJoined -= self.updateSquadMans

#    def updateSquadMans(self, *args):
#        self.__squad_mans.clear()
#        arenaDP = self.sessionProvider.getArenaDP()
#        playerVehicleID = avatar_getter.getPlayerVehicleID()
#        playerSquad = arenaDP.getVehicleInfo(playerVehicleID).squadIndex
#        if not playerSquad:
#            self.__squad_mans.add(playerVehicleID)
#        else:
#            for vInfo in arenaDP.getVehiclesInfoIterator():
#                if not vInfo.isEnemy() and playerSquad == vInfo.squadIndex:
#                    self.__squad_mans.add(vInfo.vehicleID)

#    @property
#    def members(self):
#        return self.__squad_mans


# squad_controller = Squad()


# squad damage fix
# @override(VehicleMarkerPlugin, "_updateVehicleHealth")
# def new__updateVehicleHealth(func, self, vehicleID, handle, newHealth, aInfo, attackReasonID):
#    if xvmInstalled:
#        return func(self, vehicleID, handle, newHealth, aInfo, attackReasonID)
#    if newHealth < 0 and not SPECIAL_VEHICLE_HEALTH.IS_AMMO_BAY_DESTROYED(newHealth):
#        newHealth = 0
#    if g_replayCtrl.isPlaying and g_replayCtrl.isTimeWarpInProgress:
#        self._invokeMarker(handle, 'setHealth', newHealth)
#    else:
#        members = squad_controller.members
#        yellow = False if aInfo is None or not members else aInfo.vehicleID in members
#        self._invokeMarker(handle, 'updateHealth', newHealth, yellow, ATTACK_REASONS[attackReasonID])
