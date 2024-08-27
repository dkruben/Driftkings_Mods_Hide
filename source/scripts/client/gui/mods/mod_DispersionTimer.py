# -*- coding: utf-8 -*-
from collections import defaultdict
from math import ceil, log

from VehicleGunRotator import VehicleGunRotator
from aih_constants import CTRL_MODE_NAME
from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.avatar_getter import getInputHandler
from gui.shared.personality import ServicesLocator
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import SimpleConfigInterface, Analytics, override, logDebug, calculateVersion
from DriftkingsInject import DispersionTimerMeta, DriftkingsInjector, g_events

AS_INJECTOR = 'DispersionTimerInjector'
AS_BATTLE = 'DispersionTimerView'
AS_SWF = 'DispersionTimer.swf'


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'align': 'left',
            'red': 'FE0E00',
            'orange': 'FE7903',
            'yellow': 'F8F400',
            'green': 'A6FFA6',
            'blue': '02C9B3',
            'purple': 'D042F3',
            'template': '<font color=\'#%(color)s\'>%(timer).1fs. - %(percent)d%%</font>',
            'x': 60,
            'y': 110
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculateVersion(self.version),
            'UI_setting_template_text': 'Template',
            'UI_setting_template_tooltip': 'Macros \'%(color)s\', %(timer).1fs, %(percent)d%%',
            'UI_setting_colorRed_text': 'Choose Color for dispersion timer bad:',
            'UI_setting_red_text': '<font color=\'#%(red)s\'>Current color: #%(red)s</font>',
            'UI_setting_red_tooltip': '',
            'UI_setting_colorOrange_text': 'Choose Color for dispersion timer low:',
            'UI_setting_orange_text': '<font color=\'#%(orange)s\'>Current color: #%(orange)s</font>',
            'UI_setting_orange_tooltip': '',
            'UI_setting_colorYellow_text': 'Choose Color for dispersion timer normal:',
            'UI_setting_yellow_text': '<font color=\'#%(yellow)s\'>Current color: #%(yellow)s</font>',
            'UI_setting_yellow_tooltip': '',
            'UI_setting_colorGreen_text': 'Choose Color for dispersion timer good:',
            'UI_setting_green_text': '<font color=\'#%(green)s\'>Current color: #%(green)s</font>',
            'UI_setting_green_tooltip': '',
            'UI_setting_colorBlue_text': 'Choose Color for dispersion timer very good:',
            'UI_setting_blue_text': '<font color=\'#%(blue)s\'>Current color: #%(blue)s</font>',
            'UI_setting_blue_tooltip': '',
            'UI_setting_colorPurple_text': 'Choose Color for dispersion timer great:',
            'UI_setting_purple_text': '<font color=\'#%(purple)s\'>Current color: #%(purple)s</font>',
            'UI_setting_purple_tooltip': '',
            'UI_setting_x_text': 'Position X',
            'UI_setting_x_tooltip': '',
            'UI_setting_y_text': 'Position Y',
            'UI_setting_y_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        colorLabelRed = self.tb.createControl('red', self.tb.types.ColorChoice)
        colorLabelRed['text'] = self.tb.getLabel('colorRed')
        colorLabelRed['tooltip'] %= {'red': self.data['red']}
        colorLabelOrange = self.tb.createControl('orange', self.tb.types.ColorChoice)
        colorLabelOrange['text'] = self.tb.getLabel('colorOrange')
        colorLabelOrange['tooltip'] %= {'orange': self.data['orange']}
        colorLabelYellow = self.tb.createControl('yellow', self.tb.types.ColorChoice)
        colorLabelYellow['text'] = self.tb.getLabel('colorYellow')
        colorLabelYellow['tooltip'] %= {'yellow': self.data['yellow']}
        colorLabelGreen = self.tb.createControl('green', self.tb.types.ColorChoice)
        colorLabelGreen['text'] = self.tb.getLabel('colorGreen')
        colorLabelGreen['tooltip'] %= {'green': self.data['green']}
        colorLabelBlue = self.tb.createControl('blue', self.tb.types.ColorChoice)
        colorLabelBlue['text'] = self.tb.getLabel('colorBlue')
        colorLabelBlue['tooltip'] %= {'blue': self.data['blue']}
        colorLabelPurple = self.tb.createControl('purple', self.tb.types.ColorChoice)
        colorLabelPurple['text'] = self.tb.getLabel('colorPurple')
        colorLabelPurple['tooltip'] %= {'purple': self.data['purple']}
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                colorLabelRed,
                colorLabelOrange,
                colorLabelYellow,
                colorLabelGreen,
                colorLabelBlue,
                colorLabelPurple
            ],
            'column2': [
                self.tb.createControl('template', self.tb.types.TextInput, 400),
                self.tb.createSlider('x', -2000, 2000, 1, '{{value}}%s' % ' X'),
                self.tb.createSlider('y', -2000, 2000, 1, '{{value}}%s' % ' Y')

            ]
        }

    @staticmethod
    def onBattleLoaded():
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class DispersionTimer(DispersionTimerMeta):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        super(DispersionTimer, self).__init__(config.ID)
        self.macro = defaultdict(lambda: 'macros not found', timer=0, percent=0)
        self.min_angle = 1.0
        self.isPostmortem = False

    def getSettings(self):
        return config.data

    def _populate(self):
        super(DispersionTimer, self)._populate()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged += self.as_onCrosshairPositionChangedS
        handler = getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
        g_events.onDispersionAngleChanged += self.updateDispersion

    def _dispose(self):
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged -= self.as_onCrosshairPositionChangedS
        handler = getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        g_events.onDispersionAngleChanged -= self.updateDispersion
        super(DispersionTimer, self)._dispose()

    def onCameraChanged(self, ctrlMode, _=None):
        self.isPostmortem = ctrlMode in {CTRL_MODE_NAME.KILL_CAM, CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM, CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION}
        if self.isPostmortem:
            self.min_angle = 1.0
            self.as_updateTimerTextS('')

    def updateDispersion(self, gunRotator):
        type_descriptor = gunRotator._avatar.vehicleTypeDescriptor
        if type_descriptor is None or self.isPostmortem:
            return self.as_updateTimerTextS('')
        aiming_angle = gunRotator.dispersionAngle
        if self.min_angle > aiming_angle:
            self.min_angle = aiming_angle
            logDebug(config.ID, False, 'DispersionTimer - renew min dispersion angle {}', self.min_angle)

        diff = self.min_angle / aiming_angle
        percent = int(ceil(diff * 100))
        self.macro['timer'] = round(type_descriptor.gun.aimingTime * abs(log(diff)), 2)
        self.macro['color'] = self.getColor(percent)
        self.macro['percent'] = percent
        self.as_updateTimerTextS(config.data['template'] % self.macro)

    @staticmethod
    def getColor(percent):
        value = percent
        if value < 15:
            color = config.data['red']
        elif value < 35:
            color = config.data['orange']
        elif value < 50:
            color = config.data['yellow']
        elif value < 75:
            color = config.data['green']
        elif value < 90:
            color = config.data['blue']
        else:
            color = config.data['purple']
        return color


# update gun dispersion
@override(VehicleGunRotator, 'updateRotationAndGunMarker')
def new_updateRotationAndGunMarker(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    g_events.onDispersionAngleChanged(self)


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, DispersionTimer, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
