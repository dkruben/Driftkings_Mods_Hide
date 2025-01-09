# -*- coding: utf-8 -*-
from collections import defaultdict

from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
from gui.shared.personality import ServicesLocator

from DriftkingsCore import DriftkingsConfigInterface, Analytics, percentToRgb, getPercent, calculate_version
from DriftkingsInject import DriftkingsInjector, TotalLogMeta, cachedVehicleData, g_events

AS_INJECTOR = 'TotalLogInjector'
AS_BATTLE = 'TotalLogView'
AS_SWF = 'TotalLog.swf'

_EVENT_TO_TOP_LOG_MACROS = {
    FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY: ('tankAvgDamage', 'tankDamageAvgColor', 'playerDamage'),
    FEEDBACK_EVENT_ID.PLAYER_USED_ARMOR: ('tankAvgBlocked', 'tankBlockedAvgColor', 'blockedDamage'),
    FEEDBACK_EVENT_ID.PLAYER_ASSIST_TO_KILL_ENEMY: ('tankAvgAssist', 'tankAssistAvgColor', 'assistDamage'),
    FEEDBACK_EVENT_ID.PLAYER_ASSIST_TO_STUN_ENEMY: ('tankAvgStun', 'tankStunAvgColor', 'stun'),
    FEEDBACK_EVENT_ID.PLAYER_SPOTTED_ENEMY: (None, None, 'spottedTanks')
}


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'separate': '  ',
            'align': 'center',
            'inCenter': True,
            'alignX': 'left',
            'alignY': 'top',
            'x': 250,
            'y': 50,
            'avgColor': {
                'brightness': 1.0,
                'saturation': 0.5
            },
            'icons': {
                'assistIcon': '<img src=\'img://gui/maps/icons/TotalLog/efficiency/help.png\' width=\'16\' height=\'16\' vspace=\'-4\'>',
                'blockedIcon': '<img src=\'img://gui/maps/icons/TotalLog/efficiency/armor.png\' width=\'16\' height=\'16\' vspace=\'-4\'>',
                'damageIcon': '<img src=\'img://gui/maps/icons/TotalLog/efficiency/damage.png\' width=\'16\' height=\'16\' vspace=\'-4\'>',
                'spottedIcon': '<img src=\'img://gui/maps/icons/TotalLog/efficiency/detection.png\' width=\'16\' height=\'16\' vspace=\'-4\'>',
                'stunIcon': '<img src=\'img://gui/maps/icons/TotalLog/efficiency/stun.png\' width=\'16\' height=\'16\' vspace=\'-4\'>'
            },
            'templateMainDMG': [
                '%(damageIcon)s<font color=\'%(tankDamageAvgColor)s\'>%(playerDamage)s</font>',
                '%(blockedIcon)s<font color=\'%(tankBlockedAvgColor)s\'>%(blockedDamage)s</font>',
                '%(assistIcon)s<font color=\'%(tankAssistAvgColor)s\'>%(assistDamage)s</font>',
                '%(spottedIcon)s%(spottedTanks)s',
                '%(stunIcon)s<font color=\'%(tankStunAvgColor)s\'>%(stun)s</font>'
            ]
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_separate_text': 'Separate',
            'UI_setting_separate_tooltip': '',
            'UI_setting_inCenter_text': 'In Center',
            'UI_setting_inCenter_tooltip': 'Display the log in the middle of the screen',
            #
            'UI_setting_x_text': 'Position X',
            'UI_setting_x_tooltip': 'Horizontal position',
            'UI_setting_y_text': 'Position Y',
            'UI_setting_y_tooltip': 'Vertical position',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('separate', self.tb.types.TextInput, 400),
                self.tb.createControl('inCenter')

            ],
            'column2': [
                self.tb.createSlider('x', -2000, 2000, 1, '{{value}}%s' % ' X'),
                self.tb.createSlider('y', -2000, 2000, 1, '{{value}}%s' % ' Y')
            ]
        }

    def onBattleLoaded(self):
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if not self.data['enabled'] and app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class TotalLog(TotalLogMeta):

    def __init__(self):
        super(TotalLog, self).__init__(config.ID)
        self._is_top_log_enabled = False
        self.top_log = defaultdict(int)
        self.top_log_template = ''

    def getSettings(self):
        return config.data

    def _populate(self):
        # noinspection PyProtectedMember
        super(TotalLog, self)._populate()
        feedback = self.sessionProvider.shared.feedback
        if feedback is None:
            return
        feedback.onPlayerFeedbackReceived += self.__onPlayerFeedbackReceived
        self._is_top_log_enabled = config.data['enabled']
        if self._is_top_log_enabled:
            self.as_createTopLogS(config.data)
            self.update_top_log_start_params()
            self.as_updateTopLogS(self.top_log_template % self.top_log)

    def update_top_log_start_params(self):
        template = config.data['templateMainDMG']
        self.top_log.update(config.data['icons'], tankDamageAvgColor='#FFFFFF', tankAssistAvgColor='#FFFFFF', tankBlockedAvgColor='#FFFFFF', tankStunAvgColor='#FFFFFF', tankAvgDamage=cachedVehicleData.efficiencyAvgData.damage, tankAvgAssist=cachedVehicleData.efficiencyAvgData.assist, tankAvgStun=cachedVehicleData.efficiencyAvgData.stun, tankAvgBlocked=cachedVehicleData.efficiencyAvgData.blocked)
        if not self.isSPG():
            self.top_log.update(stun='', stunIcon='')
            template = [line for line in template if 'stunIcon' not in line]
        self.top_log_template = config.data['separate'].join(template)

    def isTopLogEventEnabled(self, eventType):
        return self._is_top_log_enabled and eventType in _EVENT_TO_TOP_LOG_MACROS

    def _dispose(self):
        feedback = self.sessionProvider.shared.feedback
        if feedback is not None:
            feedback.onPlayerFeedbackReceived -= self.__onPlayerFeedbackReceived
            if self._is_top_log_enabled:
                self.top_log.clear()
        # noinspection PyProtectedMember
        super(TotalLog, self)._dispose()

    def parseEvent(self, event):
        """wg Feedback event parser"""
        eType = event.getType()
        extra = event.getExtra()
        if self.isTopLogEventEnabled(eType):
            self.addToTopLog(eType, event, extra)

    def addToTopLog(self, e_type, event, extra):
        avg_value_macros, avg_color_macros, value_macros = _EVENT_TO_TOP_LOG_MACROS[e_type]
        if e_type == FEEDBACK_EVENT_ID.PLAYER_ASSIST_TO_STUN_ENEMY and not self.top_log['stunIcon']:
            self.top_log_template = config.data['separate'].join(config.data['templateMainDMG'])
            self.top_log['stunIcon'] = config.data['icons']['stunIcon']
            self.top_log[value_macros] = 0
        self.top_log[value_macros] += self.unpackTopLogValue(e_type, event, extra)
        if avg_value_macros is not None:
            value = self.top_log[value_macros]
            avg_value = self.top_log[avg_value_macros]
            self.top_log[avg_color_macros] = self.getAVGColor(getPercent(value, avg_value))
        self.as_updateTopLogS(self.top_log_template % self.top_log)

    @staticmethod
    def unpackTopLogValue(e_type, event, extra):
        if e_type == FEEDBACK_EVENT_ID.PLAYER_SPOTTED_ENEMY:
            return event.getCount()
        return extra.getDamage()

    def __onPlayerFeedbackReceived(self, events):
        if self.isPlayerVehicle:
            for event in events:
                self.parseEvent(event)

    @staticmethod
    def getAVGColor(percent):
        return percentToRgb(percent, **config.data['avgColor']) if percent else '#FFFFFF'


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, TotalLog, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
