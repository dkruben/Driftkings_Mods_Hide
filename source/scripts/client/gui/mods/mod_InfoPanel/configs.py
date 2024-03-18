# -*- coding: utf-8 -*-
import Keys

from DriftkingsCore import SimpleConfigInterface, Analytics
from . import __date__, __modID__


class ConfigInterface(SimpleConfigInterface):
    def init(self):
        self.ID = __modID__
        self.version = '1.3.0 (%s)' % __date__
        self.author = 'orig. Kotyarko_O'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.defaultKeys = {'altKey': [Keys.KEY_LALT]}
        self.data = {
            'enabled': True,
            'showFor': 0,
            'aliveOnly': False,
            'textLock': False,
            'delay': 5,
            'altKey': self.defaultKeys['altKey'],
            'compareValues': {'moreThan': {'delim': '&gt;', 'color': '#FF0000'}, 'equal': {'delim': '=', 'color': '#FFFFFF'}, 'lessThan': {'delim': '&lt;', 'color': '#00FF00'}},
            'format': '<font color=\'#F0F0F0\'><b>{{vehicle_name}}</b></font><br><textformat tabstops=\'[80]\'><font color=\'#14AFF1\'>{{gun_reload_equip}} sec.</font><tab><font color=\'#96CC29\'>{{vision_radius}} mt.</font></textformat>',
            'textStyle': {'size': 14, 'font': '$TitleFont', 'align': 'left'},
            # flash
            'textPosition': [632.0, 577.0],
            'textShadow': {'distance': 0, 'angle': 90, 'color': '#000000', 'alpha': 0.8, 'blurX': 2, 'blurY': 2, 'strength': 2, 'quality': 2}
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_textLock_text': 'Disable text mouse dragging',
            'UI_setting_textLock_tooltip': 'This setting controls whether you are able to move text window with a mouse or not.',
            'UI_setting_showFor_text': 'Show For',
            'UI_setting_showFor_tooltip': (
                            ' • <b>Ally</b> - Just show to \'ALLY\' players tanks.\n'
                            ' • <b>Enemy</b> - Just show to \'ENEMY\' players tanks.\n'
                            ' • <b>All</b> - Show to \'ALL\' players tanks.'
            ),
            'UI_showFor_ally': 'Ally',
            'UI_showFor_enemy': 'Enemy',
            'UI_showFor_all': 'All',
            'UI_setting_aliveOnly_text': 'Alive Only',
            'UI_setting_aliveOnly_tooltip': 'Show only for alive players.',
            'UI_setting_altKey_text': 'Alt. Key',
            'UI_setting_altKey_tooltip': 'Key for self vehicle information display.',
            'UI_setting_delay_text': 'Delay',
            'UI_setting_delay_tooltip': 'Hide panel delay (in seconds)',
            'UI_delay_format': ' sec.'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        xFormat = self.i18n['UI_delay_format']
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('textLock'),
                self.tb.createSlider('delay', 1.0, 10, 1.0, '{{value}}%s' % xFormat),
                self.tb.createControl('aliveOnly'),
                self.tb.createHotKey('altKey'),
                self.tb.createOptions('showFor', [self.i18n['UI_showFor_' + x] for x in ('all', 'ally', 'enemy')])
            ],
            'column2': []
        }

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)


g_config = ConfigInterface()
statistic_mod = Analytics(g_config.ID, g_config.version, 'UA-121940539-1')
