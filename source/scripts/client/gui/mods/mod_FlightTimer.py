from collections import defaultdict

from aih_constants import CTRL_MODE_NAME
from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control import avatar_getter
from gui.shared.personality import ServicesLocator
from math_utils import VectorConstant

from DriftkingsCore import SimpleConfigInterface, Analytics, getPlayer, calculate_version
from DriftkingsInject import FlightTimeMeta, DriftkingsInjector, g_events

AS_INJECTOR = 'FlightTimerInjector'
AS_BATTLE = 'FlightTimerView'
AS_SWF = 'FlightTimer.swf'


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'align': 'left',
            'spgOnly': False,
            'template': "<font color='#f5ff8f'>%(flightTime).1fs. - %(distance)dm.</font>",
            'x': 100,
            'y': 100
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_template_text': 'Template',
            'UI_setting_template_tooltip': 'Macros \'%(flightTime).1fs\', %(distance)dm',
            #
            'UI_setting_spgOnly_text': 'Just for SPG?',
            'UI_setting_spgOnly_tooltip': 'If checked, then the timer will be visible only for SPG.',
            #
            'UI_setting_x_text': 'Position X',
            'UI_setting_x_tooltip': '',
            'UI_setting_y_text': 'Position Y',
            'UI_setting_y_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('template', self.tb.types.TextInput, 400),
                self.tb.createControl('spgOnly')
            ],
            'column2': [
                self.tb.createSlider('x', -2000, 2000, 1, '{{value}}%s' % ' X'),
                self.tb.createSlider('y', -2000, 2000, 1, '{{value}}%s' % ' Y')
            ]
        }

    def onBattleLoaded(self):
        if not self.data['enabled']:
            return
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class FlightTime(FlightTimeMeta):

    def __init__(self):
        super(FlightTime, self).__init__(config.ID)
        self.settings = config.data
        self.macrosDict = defaultdict(lambda: 'Macros not found', flightTime=0, distance=0)

    def isFlightTimeEnabled(self):
        enabled = self.settings['enabled']
        if self.settings['spgOnly']:
            return enabled and self.isSPG()
        return enabled

    def getSettings(self):
        if self.isFlightTimeEnabled():
            return self.settings

    def _populate(self):
        super(FlightTime, self)._populate()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged += self.as_onCrosshairPositionChangedS
            ctrl.onGunMarkerStateChanged += self.__onGunMarkerStateChanged
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged

    def _dispose(self):
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged -= self.as_onCrosshairPositionChangedS
            ctrl.onGunMarkerStateChanged -= self.__onGunMarkerStateChanged
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        super(FlightTime, self)._dispose()

    def onCameraChanged(self, ctrlMode, *_, **__):
        if ctrlMode in {CTRL_MODE_NAME.KILL_CAM, CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM, CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION, CTRL_MODE_NAME.LOOK_AT_KILLER}:
            self.as_flightTimeS('')

    def __onGunMarkerStateChanged(self, _, position, *__, **___):
        player = getPlayer()
        if player is None:
            return self.as_flightTimeS('')
        shotPos, shotVec = player.gunRotator.getCurShotPosition()
        flatDist = position.flatDistTo(shotPos)
        self.macrosDict['flightTime'] = flatDist / shotVec.flatDistTo(VectorConstant.Vector3Zero)
        self.macrosDict['distance'] = flatDist
        self.as_flightTimeS(config.data['template'] % self.macrosDict)


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, FlightTime, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
