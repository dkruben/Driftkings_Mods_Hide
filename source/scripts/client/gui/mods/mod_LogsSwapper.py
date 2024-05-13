# -*- coding: utf-8 -*-
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import _LogViewComponent, DamageLogPanel
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE as _ETYPE

from DriftkingsCore import SimpleConfigInterface, Analytics, override

BASE_WG_LOGS = (DamageLogPanel._addToTopLog, DamageLogPanel._updateTopLog, DamageLogPanel._updateBottomLog, DamageLogPanel._addToBottomLog)
validated = {}


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.version = '1.4.0 (%(file_compile_date)s)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'logSwapper': True,
            'wgLogHideCritics': True,
            'wgLogHideBlock': True,
            'wgLogHideAssist': True,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': sum(int(x) * (10 ** i) for i, x in enumerate(reversed(self.version.split(' ')[0].split('.')))),
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


@override(_LogViewComponent, 'addToLog')
def new__addToLog(func, self, event):
    if config.data['enabled']:
        return func(self, [e for e in event if not validated.get(e.getType(), False)])
    return func(self, event)


validated.update({
        _ETYPE.RECEIVED_CRITICAL_HITS: config.data['wgLogHideCritics'],
        _ETYPE.BLOCKED_DAMAGE: config.data['wgLogHideBlock'],
        _ETYPE.ASSIST_DAMAGE: config.data['wgLogHideAssist'],
        _ETYPE.STUN: config.data['wgLogHideAssist']
    })
DamageLogPanel._addToTopLog, DamageLogPanel._updateTopLog, DamageLogPanel._updateBottomLog,\
DamageLogPanel._addToBottomLog = reversed(BASE_WG_LOGS) if config.data['logSwapper'] else BASE_WG_LOGS
