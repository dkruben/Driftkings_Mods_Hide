# -*- coding: utf-8 -*-
from collections import defaultdict

from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
from gui.shared.personality import ServicesLocator

from DriftkingsCore import SimpleConfigInterface, Analytics, percentToRGB, getPercent
from DriftkingsInject import DriftkingsInjector, DamageLogsMeta, cachedVehicleData, g_events

AS_INJECTOR = 'DamageLogsInjector'
AS_BATTLE = 'DamageLogsView'
AS_SWF = 'DamageLogs.swf'

_EVENT_TO_TOP_LOG_MACROS = {
    FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY: ('tankAvgDamage', 'tankDamageAvgColor', 'playerDamage'),
    FEEDBACK_EVENT_ID.PLAYER_USED_ARMOR: ('tankAvgBlocked', 'tankBlockedAvgColor', 'blockedDamage'),
    FEEDBACK_EVENT_ID.PLAYER_ASSIST_TO_KILL_ENEMY: ('tankAvgAssist', 'tankAssistAvgColor', 'assistDamage'),
    FEEDBACK_EVENT_ID.PLAYER_ASSIST_TO_STUN_ENEMY: ('tankAvgStun', 'tankStunAvgColor', 'stun'),
    FEEDBACK_EVENT_ID.PLAYER_SPOTTED_ENEMY: (None, None, 'spottedTanks')
}


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        self.version_int = 1.00
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'separate': '  ',
            'settings': {
                'align': 'right',
                'inCenter': True,
                'x': -260,
                'y': 0
            },
            'avgColor': {
                'brightness': 1.0,
                'saturation': 0.5
            },
            'icons': {
                'assistIcon': '<img src=\'img://gui/maps/icons/DamageLogs/efficiency/help.png\' width=\'16\' height=\'16\' vspace=\'-4\'>',
                'blockedIcon': '<img src=\'img://gui/maps/icons/DamageLogs/efficiency/armor.png\' width=\'16\' height=\'16\' vspace=\'-4\'>',
                'damageIcon': '<img src=\'img://gui/maps/icons/DamageLogs/efficiency/damage.png\' width=\'16\' height=\'16\' vspace=\'-4\'>',
                'spottedIcon': '<img src=\'img://gui/maps/icons/DamageLogs/efficiency/detection.png\' width=\'16\' height=\'16\' vspace=\'-4\'>',
                'stunIcon': '<img src=\'img://gui/maps/icons/DamageLogs/efficiency/stun.png\' width=\'16\' height=\'16\' vspace=\'-4\'>'
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
            'UI_setting_colour_text': '',
            'UI_setting_colour_tooltip': '',
            'UI_setting_isModel_text': '',
            'UI_setting_isModel_tooltip': '',
            #
            'UI_setting_reversLog_text': 'Enable Reverse Log.',
            'UI_setting_reversLog_tooltip': 'Reverses the position of the damage log.',
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
            'modDisplayName': self.ID,
            'settingsVersion': 1,
            'enabled': self.data['enabled'],
            'column1': [], 'column2': []}

    @staticmethod
    def onBattleLoaded():
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class DamageLogs(DamageLogsMeta):

    def __init__(self):
        super(DamageLogs, self).__init__(config.ID)
        self._is_top_log_enabled = False
        self.top_log = defaultdict(int)
        self.top_log_template = ''

    def getSettings(self):
        return config.data

    def _populate(self):
        # noinspection PyProtectedMember
        super(DamageLogs, self)._populate()
        feedback = self.sessionProvider.shared.feedback
        if feedback is None:
            return
        feedback.onPlayerFeedbackReceived += self.__onPlayerFeedbackReceived
        self._is_top_log_enabled = config.data['enabled']
        if self._is_top_log_enabled:
            self.as_createTopLogS(config.data['settings'])
            self.update_top_log_start_params()
            self.as_updateTopLogS(self.top_log_template % self.top_log)

    def update_top_log_start_params(self):
        template = config.data['templateMainDMG']
        self.top_log.update(
            config.data['icons'],
            tankDamageAvgColor='#FFFFFF',
            tankAssistAvgColor='#FFFFFF',
            tankBlockedAvgColor='#FFFFFF',
            tankStunAvgColor='#FFFFFF',
            tankAvgDamage=cachedVehicleData.efficiencyAvgData.damage,
            tankAvgAssist=cachedVehicleData.efficiencyAvgData.assist,
            tankAvgStun=cachedVehicleData.efficiencyAvgData.stun,
            tankAvgBlocked=cachedVehicleData.efficiencyAvgData.blocked
        )
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
        super(DamageLogs, self)._dispose()

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
        """Shared feedback player events"""
        if self.isPlayerVehicle:
            for event in events:
                self.parseEvent(event)

    @staticmethod
    def getAVGColor(percent):
        return percentToRGB(percent, **config.data['avgColor']) if percent else '#FFFFFF'


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, DamageLogs, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
