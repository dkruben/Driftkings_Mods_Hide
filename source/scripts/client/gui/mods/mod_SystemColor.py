# -*- coding: utf-8 -*-
import BigWorld
from Account import PlayerAccount
from Avatar import PlayerAvatar
from gui.Scaleform.daapi.view.battle.shared.messages.fading_messages import FadingMessages
from helpers.EdgeDetectColorController import g_instance, _OVERLAY_TARGET_INDEXES

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.isSquad = False
        self.isTeamKill = False
        super(ConfigInterface, self).__init__()
        override(FadingMessages, '_populate', self.new_populate)
        override(g_instance, '_EdgeDetectColorController__changeColor', self.new__changeColor)
        override(PlayerAvatar, 'onEnterWorld', self.new__onEnterWorld)
        override(PlayerAvatar, 'targetFocus', self.new__targetFocus)

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.4.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.data = {
            'enabled': False,
            'allyDead': '2C9AFF',
            'enemyDead': '96FF00',
            'squadManAlive': 'FFB964',
            'enemyAlive': '2C9AFF',
            'teamKillerAlive': '00EAFF',
            'allyAlive': '96FF00'
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_colorCheckAllyDead_text': 'Choose Color to Ally Dead:',
            'UI_setting_allyDead_text': '<font color=\'#{}\'>{}</font>'.format(self.data['allyDead'], self.data['allyDead']),
            'UI_setting_allyDead_tooltip': 'Color applied to the Tank.',
            'UI_setting_colorCheckEnemyDead_text': 'Choose Color to Enemy Dead:',
            'UI_setting_enemyDead_text': '<font color=\'#{}\'>{}</font>'.format(self.data['enemyDead'], self.data['enemyDead']),
            'UI_setting_enemyDead_tooltip': 'Color applied to the Tank.',
            'UI_setting_colorCheckSquadManAlive_text': 'Choose Color to SquadMan Alive:',
            'UI_setting_squadManAlive_text': '<font color=\'#{}\'>{}</font>'.format(self.data['squadManAlive'], self.data['squadManAlive']),
            'UI_setting_squadManAlive_tooltip': 'Color applied to the Tank.',
            'UI_setting_colorCheckEnemyAlive_text': 'Choose Color to Enemy Alive:',
            'UI_setting_enemyAlive_text': '<font color=\'#{}\'>{}</font>'.format(self.data['enemyAlive'], self.data['enemyAlive']),
            'UI_setting_enemyAlive_tooltip': 'Color applied to the Tank.',
            'UI_setting_colorCheckAllyAlive_text': 'Choose Color to Ally Alive:',
            'UI_setting_allyAlive_text': '<font color=\'#{}\'>{}</font>'.format(self.data['allyAlive'], self.data['allyAlive']),
            'UI_setting_allyAlive_tooltip': 'Color applied to the Tank.',
            'UI_setting_colorCheckTeamKillerAlive_text': 'Choose Color to TeamKiller:',
            'UI_setting_teamKillerAlive_text': '<font color=\'#{}\'>{}</font>'.format(self.data['teamKillerAlive'], self.data['teamKillerAlive']),
            'UI_setting_teamKillerAlive_tooltip': 'Color applied to the Tank.'
        }
        super(ConfigInterface, self).init()

    # noinspection PyProtectedMember
    def createTemplate(self):
        colorLabelAllyDead = self.tb.createControl('allyDead', self.tb.types.ColorChoice)
        colorLabelAllyDead['text'] = self.tb.getLabel('colorCheckAllyDead')
        colorLabelAllyDead['tooltip'] %= {'allyDead': self.data['allyDead']}
        colorLabelEnemyDead = self.tb.createControl('enemyDead', self.tb.types.ColorChoice)
        colorLabelEnemyDead['text'] = self.tb.getLabel('colorCheckEnemyDead')
        colorLabelEnemyDead['tooltip'] %= {'enemyDead': self.data['enemyDead']}
        colorLabelSquadManAlive = self.tb.createControl('squadManAlive', self.tb.types.ColorChoice)
        colorLabelSquadManAlive['text'] = self.tb.getLabel('colorCheckSquadManAlive')
        colorLabelSquadManAlive['tooltip'] %= {'squadManAlive': self.data['squadManAlive']}
        colorLabelEnemyAlive = self.tb.createControl('enemyAlive', self.tb.types.ColorChoice)
        colorLabelEnemyAlive['text'] = self.tb.getLabel('colorCheckEnemyAlive')
        colorLabelEnemyAlive['tooltip'] %= {'enemyAlive': self.data['enemyAlive']}
        colorLabelAllyAlive = self.tb.createControl('allyAlive', self.tb.types.ColorChoice)
        colorLabelAllyAlive['text'] = self.tb.getLabel('colorCheckAllyAlive')
        colorLabelAllyAlive['tooltip'] %= {'allyAlive': self.data['allyAlive']}
        colorLabelTeamKillerAlive = self.tb.createControl('teamKillerAlive', self.tb.types.ColorChoice)
        colorLabelTeamKillerAlive['text'] = self.tb.getLabel('colorCheckTeamKillerAlive')
        colorLabelTeamKillerAlive['tooltip'] %= {'teamKillerAlive': self.data['teamKillerAlive']}
        return {
            'modDisplayName': self.i18n['UI_description'],
            'settingsVersion': 1,
            'enabled': self.data['enabled'],
            'column1': [
                colorLabelAllyDead,
                colorLabelEnemyDead
            ],
            'column2': [
                colorLabelSquadManAlive,
                colorLabelEnemyAlive,
                colorLabelAllyAlive,
                colorLabelTeamKillerAlive
            ]}

    @staticmethod
    def to_html_color(value):
        return '#{}'.format(value[2:]) if value[:2] == '0x' else value

    @staticmethod
    def color_vector(color, default):
        try:
            color = '#{}{}'.format(color[-6:], 'FF')
            return tuple(int(color[i:i + 2], 16) / 255.0 for i in (0, 2, 4, 6))
        except ValueError:
            return default

    def new_populate(self, func, orig):
        func(orig)
        ally_dead = self.to_html_color(self.data.get('allyDead', None))
        enemy_dead = self.to_html_color(self.data.get('enemyDead', None))
        for k, v in orig._messages.iteritems():
            if k[:6] == 'DEATH_':
                message, colors = v
                if 'red' in colors and enemy_dead is not None:
                    orig._messages[k] = '<font color=\'#%s\'>%s</font>' % (enemy_dead, message), colors
                elif 'green' in colors and ally_dead is not None:
                    orig._messages[k] = '<font color=\'#%s\'>%s</font>' % (ally_dead, message), colors

    def new__changeColor(self, base, diff):
        if 'isColorBlind' not in diff:
            return
        cType = 'colorBlind' if diff['isColorBlind'] else 'common'
        isHangar = isinstance(getPlayer(), PlayerAccount)
        colors = g_instance._EdgeDetectColorController__colors[cType]
        if self.isSquad:
            friend = self.color_vector(config.data.get('squadmanAlive', 'FFB964'), colors['friend'])
            enemy = self.color_vector(config.data.get('enemyAlive', '2C9AFF'), colors['enemy'])
        elif self.isTeamKill:
            currentColor = config.data.get('teamKillerAlive', '00EAFF')
            friend = self.color_vector(currentColor, colors['friend'])
            enemy = self.color_vector(currentColor, colors['enemy'])
        else:
            friend = self.color_vector(config.data.get('allyAlive', '96FF00'), colors['friend'])
            enemy = self.color_vector(config.data.get('enemyAlive', '2C9AFF'), colors['enemy'])
        colorsSet = (colors['hangar'] if isHangar else colors['self'], enemy, friend, colors['flag'])
        i = 0
        for c in colorsSet:
            BigWorld.wgSetEdgeDetectEdgeColor(i, c)
            i += 1
        for target, idx in _OVERLAY_TARGET_INDEXES.iteritems():
            BigWorld.wgSetEdgeDetectSolidColors(idx, *colors['overlaySolidColors'][target]['packed'])
            BigWorld.wgSetEdgeDetectPatternColors(idx, *colors['overlayPatternColors'][target]['packed'])

    def new__onEnterWorld(self, func, orig, prereqs):
        func(orig, prereqs)
        self.isSquad = False
        self.isTeamKill = False
        g_instance.updateColors()

    def new__targetFocus(self, func, orig, entity):
        func(orig, entity)
        if hasattr(orig, '_PlayerAvatar__vehicles') and entity in orig._PlayerAvatar__vehicles:
            prevIsSquad = self.isSquad
            prevIsTeamKill = self.isTeamKill
            getArenaDP = orig.guiSessionProvider.getArenaDP()
            self.isSquad = getArenaDP.isSquadMan(vID=entity.id)
            self.isTeamKill = getArenaDP.isTeamKiller(vID=entity.id)
            if (prevIsSquad != self.isSquad) or (prevIsTeamKill != self.isTeamKill):
                g_instance.updateColors()


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)
