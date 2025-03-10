# -*- coding: utf-8 -*-
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import _LogViewComponent, DamageLogPanel
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE as _ETYPE

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, calculate_version


class ConfigInterface(DriftkingsConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.version = '1.4.5 (%(file_compile_date)s)'
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
analytics = Analytics(config.ID, config.version)


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
