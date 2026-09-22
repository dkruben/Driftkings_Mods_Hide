# -*- coding: utf-8 -*-
from functools import partial
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import _LogViewComponent, DamageLogPanel
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, calculate_version


class ConfigInterface(DriftkingsConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.version = '1.5.6 (%(file_compile_date)s)'
        self.data = {
            'enabled': True,
            'logSwapper': True,
            'wgLogHideCritics': True,
            'wgLogHideBlock': True,
            'wgLogHideAssist': True
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_logSwapper_text': 'Enable Reverse Log.',
            'UI_setting_logSwapper_tooltip': 'Reverses the position of the damage log in the battle interface.',
            'UI_setting_wgLogHideCritics_text': 'WG Log Hide Critics',
            'UI_setting_wgLogHideCritics_tooltip': 'Hides critical hit messages in the standard WG battle log.',
            'UI_setting_wgLogHideBlock_text': 'WG Log Hide Block',
            'UI_setting_wgLogHideBlock_tooltip': 'Hides blocked damage messages in the standard WG battle log.',
            'UI_setting_wgLogHideAssist_text': 'WG Log Hide Assist',
            'UI_setting_wgLogHideAssist_tooltip': 'Hides damage assist messages in the standard WG battle log.'
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
            'column2': []
        }


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


class WGLogs(object):
    def __init__(self):
        override(_LogViewComponent, 'addToLog', self.new__addToLog)
        # Route the final Flash calls, preserving BattleOptions and other log hooks.
        for top, bottom in (('as_addDetailMessageTopS', 'as_addDetailMessageBottomS'),
                            ('as_detailStatsTopS', 'as_detailStatsBottomS')):
            originalTop = getattr(DamageLogPanel, top)
            originalBottom = getattr(DamageLogPanel, bottom)
            override(DamageLogPanel, top, partial(self.routeLog, originalBottom))
            override(DamageLogPanel, bottom, partial(self.routeLog, originalTop))

    def routeLog(self, opposite, func, panel, *args, **kwargs):
        target = opposite if config.data['enabled'] and config.data['logSwapper'] else func
        return target(panel, *args, **kwargs)

    def new__addToLog(self, func, component, event):
        if not config.data['enabled']:
            return func(component, event)
        validated = self.getFilters()
        filtered_events = [e for e in event if not validated.get(e.getType(), False)]
        return func(component, filtered_events)

    @staticmethod
    def getFilters():
        return {
            PERSONAL_EFFICIENCY_TYPE.RECEIVED_CRITICAL_HITS: config.data['wgLogHideCritics'],
            PERSONAL_EFFICIENCY_TYPE.BLOCKED_DAMAGE: config.data['wgLogHideBlock'],
            PERSONAL_EFFICIENCY_TYPE.ASSIST_DAMAGE: config.data['wgLogHideAssist'],
            PERSONAL_EFFICIENCY_TYPE.STUN: config.data['wgLogHideAssist']
        }


g_logs = WGLogs()
