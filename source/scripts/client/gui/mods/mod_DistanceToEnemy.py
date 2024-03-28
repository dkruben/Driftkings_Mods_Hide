# -*- coding: utf-8 -*-
from collections import defaultdict

from PlayerEvents import g_playerEvents
from aih_constants import CTRL_MODE_NAME
from constants import ARENA_PERIOD, ARENA_PERIOD_NAMES
from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.avatar_getter import getDistanceToTarget
from gui.battle_control.avatar_getter import getInputHandler
from gui.battle_control.battle_constants import PLAYER_GUI_PROPS
from gui.shared.personality import ServicesLocator

from DriftkingsCore import SimpleConfigInterface, Analytics, logDebug
from DriftkingsInject import DriftkingsInjector, DistanceMeta, CyclicTimerEvent, g_events

AS_INJECTOR = 'DistanceInjector'
AS_BATTLE = 'DistanceView'
AS_SWF = 'DistanceToEnemy.swf'


class ConfigInterface(SimpleConfigInterface):

    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 %(file_compile_date)s'
        self.author = 'by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': False,
            'align': 'center',
            'template': '<font color=\'#f5ff8f\' size=\'18\'>%(distance).1f to %(name)s</font>',
            'x': 0,
            'y': 150
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_template_text': 'Template',
            'UI_setting_template_tooltip': 'Macros \'%(distance).1f\', %(name)s',
            'UI_setting_x_text': 'Position X',
            'UI_setting_x_tooltip': '',
            'UI_setting_y_text': 'Position Y',
            'UI_setting_y_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'settingsVersion': 1,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('template', self.tb.types.TextInput, 400),
                self.tb.createSlider('x', -2000, 2000, 1, '{{value}} X'),
                self.tb.createSlider('y', -2000, 2000, 1, '{{value}} Y')
            ],
            'column2': []
        }

    @staticmethod
    def onBattleLoaded():
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class Distance(DistanceMeta):

    def __init__(self):
        super(Distance, self).__init__(config.ID)
        self.macrosDict = defaultdict(lambda: 'Macros not found', distance=0, name='')
        self.timeEvent = None
        self.isPostmortem = False
        self.vehicles = {}

    def getSettings(self):
        return config.data

    def _populate(self):
        super(Distance, self)._populate()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged += self.as_onCrosshairPositionChangedS
        g_playerEvents.onArenaPeriodChange += self.onArenaPeriodChange
        handler = getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
        feedback = self.sessionProvider.shared.feedback
        if feedback is not None:
            feedback.onVehicleMarkerAdded += self.onVehicleMarkerAdded
            feedback.onVehicleMarkerRemoved += self.onVehicleMarkerRemoved
        arena = self._arenaVisitor.getArenaSubscription()
        if arena is not None:
            arena.onVehicleKilled += self.onVehicleMarkerRemoved

    def _dispose(self):
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged -= self.as_onCrosshairPositionChangedS
        g_playerEvents.onArenaPeriodChange -= self.onArenaPeriodChange
        if self.timeEvent is not None:
            self.timeEvent.stop()
            self.timeEvent = None
        handler = getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        feedback = self.sessionProvider.shared.feedback
        if feedback is not None:
            feedback.onVehicleMarkerAdded -= self.onVehicleMarkerAdded
            feedback.onVehicleMarkerRemoved -= self.onVehicleMarkerRemoved
        arena = self._arenaVisitor.getArenaSubscription()
        if arena is not None:
            arena.onVehicleKilled -= self.onVehicleMarkerRemoved
        super(Distance, self)._dispose()

    def onArenaPeriodChange(self, period, *_):
        if period == ARENA_PERIOD.BATTLE and self.timeEvent is None:
            self.timeEvent = CyclicTimerEvent(0.5, self.updateDistance)
            self.timeEvent.start()
        elif self.timeEvent is not None:
            self.timeEvent.stop()
            self.timeEvent = None
        logDebug(True, 'Distance: onArenaPeriodChange: {}', ARENA_PERIOD_NAMES[period])

    def onVehicleMarkerAdded(self, vProxy, vInfo, guiProps):
        if self.isPostmortem:
            return
        if guiProps == PLAYER_GUI_PROPS.enemy and vProxy.isAlive():
            self.vehicles[vInfo.vehicleID] = vProxy

    def onVehicleMarkerRemoved(self, vehicleID, *_, **__):
        if vehicleID in self.vehicles:
            self.vehicles.pop(vehicleID)

    def updateDistance(self):
        distance = None
        vehicle_name = None
        for entity in self.vehicles.itervalues():
            dist = getDistanceToTarget(entity)
            if distance is None or dist < distance:
                distance = dist
                vehicle_name = entity.typeDescriptor.type.shortUserString
        if distance is None:
            return self.as_setDistanceS('')
        self.macrosDict['name'] = vehicle_name
        self.macrosDict['distance'] = distance
        self.as_setDistanceS(config.data['template'] % self.macrosDict)

    def onCameraChanged(self, ctrlMode, *_, **__):
        self.isPostmortem = ctrlMode in {CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM, CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION}
        if self.isPostmortem:
            if self.timeEvent is not None:
                self.timeEvent.stop()
            self.vehicles.clear()
            self.as_setDistanceS('')


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, Distance, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
