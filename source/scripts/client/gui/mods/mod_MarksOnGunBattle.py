# -*- coding: utf-8 -*-
import datetime
import math
from collections import OrderedDict

import BattleReplay
import BigWorld
import GUI
import Keys
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from CurrentVehicle import g_currentVehicle
from Vehicle import Vehicle
from constants import ARENA_BONUS_TYPE
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK
from gui import InputHandler, g_guiResetters
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.battle_control.controllers import feedback_events
from gui.impl.lobby.crew.widget.crew_widget import CrewWidget
from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore

from DriftkingsCore import SimpleConfigInterface, Analytics, override, loadJson, checkKeys, getPlayer, callback, sendPanelMessage
from gambiter import g_guiFlash
from gambiter.flash import COMPONENT_TYPE, COMPONENT_ALIGN, COMPONENT_EVENT

DAMAGE_EVENTS = frozenset([BATTLE_EVENT_TYPE.RADIO_ASSIST, BATTLE_EVENT_TYPE.TRACK_ASSIST, BATTLE_EVENT_TYPE.STUN_ASSIST, BATTLE_EVENT_TYPE.DAMAGE, BATTLE_EVENT_TYPE.TANKING, BATTLE_EVENT_TYPE.RECEIVED_DAMAGE])


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        self.values = {}
        self.colors = OrderedDict([
            ('UI_color_red', '#FF0000'), ('UI_color_nice_red', '#FA8072'),
            ('UI_color_chocolate', '#D3691E'), ('UI_color_orange', '#FFA500'),
            ('UI_color_gold', '#FFD700'), ('UI_color_cream', '#FCF5C8'),
            ('UI_color_yellow', '#FFFF00'), ('UI_color_green_yellow', '#ADFF2E'),
            ('UI_color_lime', '#00FF00'), ('UI_color_green', '#008000'),
            ('UI_color_aquamarine', '#2AB157'), ('UI_color_emerald', '#28F09C'),
            ('UI_color_cyan', '#00FFFF'), ('UI_color_cornflower_blue', '#6595EE'),
            ('UI_color_blue', '#0000FF'), ('UI_color_purple', '#800080'),
            ('UI_color_hot_pink', '#FF69B5'), ('UI_color_pink', '#FFC0CB'),
            ('UI_color_brown', '#A52A2B'), ('UI_color_wg_colorBlind', '#8378FC'),
            ('UI_color_wg_enemy', '#DB0400'), ('UI_color_wg_ally', '#80D639'),
            ('UI_color_wg_squadMan', '#FFB964'), ('UI_color_wg_player', '#FFE041')
        ])
        self.ratings = OrderedDict([
            ('neutral', '#FFFFFF'), ('very_bad', '#FF6347'), ('bad', '#FE7903'),
            ('normal', '#F8F400'), ('good', '#60FF00'), ('very_good', '#02C9B3'),
            ('unique', '#D042F3')
        ])
        self.battleDamageRating0 = self.ratings['very_bad']
        self.battleDamageRating20 = self.ratings['very_bad']
        self.battleDamageRating40 = self.ratings['bad']
        self.battleDamageRating55 = self.ratings['bad']
        self.battleDamageRating65 = self.ratings['normal']
        self.battleDamageRating85 = self.ratings['good']
        self.battleDamageRating95 = self.ratings['very_good']
        self.battleDamageRating100 = self.ratings['unique']
        self.battleDamageRating = [self.battleDamageRating0, self.battleDamageRating20, self.battleDamageRating40,
                                   self.battleDamageRating55, self.battleDamageRating65, self.battleDamageRating85,
                                   self.battleDamageRating95, self.battleDamageRating100]
        self._marks = [
            '   ',
            "<font face='Arial' color='%s'><b>  &#11361;</b></font>" % self.ratings['good'],
            "<font face='Arial' color='%s'><b> &#11361;&#11361;</b></font>" % self.ratings['very_good'],
            "<font face='Arial' color='%s'><b>&#11361;&#11361;&#11361;</b></font>" % self.ratings['unique']
        ]
        self.assists = ['assistSpot', 'assistTrack', 'assistSpam']
        self.levels = [0.0, 20.0, 40.0, 55.0, 65.0, 85.0, 95.0, 100.0]
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.5.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (spoter mods)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.defaultKeys = {
            'buttonShow': [Keys.KEY_NUMPAD9, [Keys.KEY_LALT, Keys.KEY_RALT]],
            'buttonSizeUp': [Keys.KEY_PGUP, [Keys.KEY_LALT, Keys.KEY_RALT]],
            'buttonSizeDown': [Keys.KEY_PGDN, [Keys.KEY_LALT, Keys.KEY_RALT]],
            'buttonReset': [Keys.KEY_DELETE, [Keys.KEY_LCONTROL, Keys.KEY_RCONTROL], [Keys.KEY_LSHIFT, Keys.KEY_RSHIFT]]
        }
        self.data = {
            'enabled': True,
            'buttonShow': self.defaultKeys['buttonShow'],
            'buttonSizeUp': self.defaultKeys['buttonSizeUp'],
            'buttonSizeDown': self.defaultKeys['buttonSizeDown'],
            'buttonReset': self.defaultKeys['buttonReset'],
            'showInBattle': False,
            'showInBattleHalfPercents': False,
            'showInReplay': True,
            'showInStatistic': True,
            'showInHangar': True,
            'upColor': 18,
            'downColor': 21,
            'unknownColor': 16,
            'font': '$FieldFont',
            'background': True,
            'panelSize': {
                'widthAlt': 183.0,
                'heightAlt': 80.0,
                'widthNormal': 183.0,
                'heightNormal': 50.0
            },
            'panel': {
                'index': 10000,
                'x': 230.0,
                'y': -226.0,
                'width': 183.0,
                'height': 50.0,
                'drag': True,
                'border': True,
                'alignX': 'left',
                'alignY': 'bottom',
                'visible': True,
                'alpha': 1.0,
                'shadow': {'distance': 0, 'angle': 0, 'color': 0x000000, "alpha": 90, 'blurX': 1, 'blurY': 1, 'strength': 3000, 'quality': 1},
            },
            'battleMessage': '<font size=\"14\">{currentMarkOfGun}</font> <font size=\"10\">{damageCurrentPercent}</font><font size=\"14\"> ~ {c_nextMarkOfGun}</font> <font size=\"10\">{c_damageNextPercent}</font>\n'
                             '<font size=\"20\">{c_battleMarkOfGun}{status}</font><font size=\"14\">{c_damageCurrent}</font>',

            'battleMessageAlt': '<font size=\"14\">{currentMarkOfGun}</font> <font size=\"10\">{damageCurrentPercent}</font><font size=\"14\"> ~ {c_nextMarkOfGun}</font> <font size=\"10\">{c_damageNextPercent}</font>\n'
                                '<font size=\"20\">{c_battleMarkOfGun}{status}</font><font size=\"14\">{c_damageCurrent}</font>\n'
                                '{c_damageToMark65}{c_damageToMark85}\n'
                                '{c_damageToMark95}{c_damageToMark100}',
            'battleMessage{status}Up': '<img src=\"img://gui/maps/icons/messenger/status/24x24/chat_icon_user_is_online.png\" vspace=\"-5\"/> ',
            'battleMessage{c_status}Up': '+',
            'battleMessage{status}Down': '<img src=\"img://gui/maps/icons/messenger/status/24x24/chat_icon_user_is_busy.png\" vspace=\"-5\"/>',
            'battleMessage{c_status}Down': '-',
            'battleMessage{status}Unknown': '<img src=\"img://gui/maps/icons/messenger/status/24x24/chat_icon_user_is_busy_violet.png\" vspace=\"-5\"/>',
            'battleMessage{c_status}Unknown': '~',
            'battleMessage{battleMarkOfGun}': '%.2f%%',
            'battleMessage{c_battleMarkOfGun}': '%s',
            'battleMessage{currentMarkOfGun}': '%.2f%%',
            'battleMessage{c_currentMarkOfGun}': '%s',
            'battleMessage{nextMarkOfGun}': '%.1f%%',
            'battleMessage{c_nextMarkOfGun}': '%s',
            'battleMessage{damageCurrent}': '[<b>%.0f</b>]',
            'battleMessage{c_damageCurrent}': '%s',
            'battleMessage{damageCurrentPercent}': '[<b>%.0f</b>]',
            'battleMessage{c_damageCurrentPercent}': '%s',
            'battleMessage{damageNextPercent}': '[<b>%.0f</b>]',
            'battleMessage{c_damageNextPercent}': '%s',
            'battleMessage{damageToMark65}': '<b>65%%:%.0f</b>, ',
            'battleMessage{c_damageToMark65}': '%s',
            'battleMessage{damageToMark85}': '<b>85%%:%.0f</b>',
            'battleMessage{c_damageToMark85}': '%s',
            'battleMessage{damageToMark95}': '<b>95%%:%.0f</b>, ',
            'battleMessage{c_damageToMark95}': '%s',
            'battleMessage{damageToMark100}': '<b>100%%:%.0f</b>',
            'battleMessage{c_damageToMark100}': '%s',
            'battleMessage{damageToMarkInfo}': '%s',
            'battleMessage{c_damageToMarkInfo}': '%s',
            'battleMessage{damageToMarkInfoLevel}': '%s%%',
            'battleMessage{c_damageToMarkInfoLevel}': '%s',
            'battleMessageSizeInPercent': 100,
            'battleMessage{assistSpot}': '<img src=\"img://gui/maps/icons/library/efficiency/48x48/detection.png\" width=\"16\" height=\"16\" vspace=\"-5\"/>',
            'battleMessage{assistTrack}': '<img src=\"img://gui/maps/icons/library/efficiency/48x48/immobilized.png\" width=\"16\" height=\"16\" vspace=\"-5\"/>',
            'battleMessage{assistSpam}': '<img src=\"img://gui/maps/icons/library/efficiency/48x48/stun.png\" width=\"16\" height=\"16\" vspace=\"-5\"/>',
            'UI': 10
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_message': 'MoE change visual %s',
            'UI_setting_buttonShow_text': 'Button: Change Style',
            'UI_setting_buttonShow_tooltip': '',
            'UI_setting_buttonSizeUp_text': 'Button: Size +10%',
            'UI_setting_buttonSizeUp_tooltip': '',
            'UI_setting_buttonSizeDown_text': 'Button: Size -10%',
            'UI_setting_buttonSizeDown_tooltip': '',
            'UI_setting_buttonReset_text': 'Button: Reset Settings',
            'UI_setting_buttonReset_tooltip': '',
            'UI_setting_showInBattle_text': 'Battle: Hello message',
            'UI_setting_showInBattle_tooltip': '',
            'UI_setting_showInBattleHalfPercents_text': 'Battle: show damage to +0.5%',
            'UI_setting_showInBattleHalfPercents_tooltip': '',
            'UI_setting_showInReplay_text': 'Replay[test]: enabled',
            'UI_setting_showInReplay_tooltip': '{HEADER}Show in replay{/HEADER}{BODY}Not good, but useful for tests{/BODY}',
            'UI_setting_showInStatistic_text': 'Statistic: enabled',
            'UI_setting_showInStatistic_tooltip': '',
            'UI_setting_upColor_text': 'Battle: color when % mark up',
            'UI_setting_upColor_tooltip': '',
            'UI_setting_downColor_text': 'Battle: color when % mark down',
            'UI_setting_downColor_tooltip': '',
            'UI_setting_unknownColor_text': 'Battle: color when % mark unknown',
            'UI_setting_unknownColor_tooltip': '',
            'UI_setting_background_text': 'Battle: show background',
            'UI_setting_background_tooltip': '',
            'UI_setting_techTreeMarkOfGunPercentSize_value': '',
            'UI_setting_showInHangar_text': 'Hangar: Show MoE mod',
            'UI_setting_showInHangar_tooltip': '',

            'UI_setting_UI_text': 'UI in battle',
            'UI_setting_UI_tooltip': '{HEADER}UI in battle{/HEADER}{BODY}Extended:<br/>'
                                     '<img src=\"img://objects/ui_extended.png\"></img><br/>'
                                     'Simple:<br/><img src=\"img://objects/ui_simple.png\"></img><br/>'
                                     'Config:<br/>/mods/configs/marksOnGunExtended/marksOnGunExtended.json<br/> {/BODY}',
            'UI_menu_UIskill4ltu': '<font color=\"#60FF00\">@skill</font> choice [<font color=\"#60FF00\">twitch.tv/skill4ltu</font>]',
            'UI_menu_UIMyp': '<font color=\"#D042F3\">@Myp</font> choice [<font color=\"#D042F3\">twitch.tv/myp_</font>]',
            'UI_menu_UIspoter': '<font color=\"#6595EE\">@spoter</font> choice [<font color=\"#6595EE\">github.com/spoter</font>]',
            'UI_menu_UIspoterNew': 'new <font color=\"#6595EE\">@spoter</font> choice [<font color=\"#6595EE\">github.com/spoter</font>]',
            'UI_menu_UIcircon': '<font color=\"#02C9B3\">@Circon</font> choice [<font color=\"#02C9B3\">twitch.tv/circon</font>]',
            'UI_menu_UIoldskool': '<font color=\"#FFD700\">@Oldskool</font> choice [<font color=\"#FFD700\">twitch.tv/oldskool</font>]',
            'UI_menu_UIkorbenDallasNoMercy': '<font color=\"#e3256b\">@KorbenDallasNoMercy</font> choice [<font color=\"#e3256b\">youtube.com/c/KorbenDallasNoMercy</font>]',
            'UI_menu_UIReplayColor': 'Colored for Replays',
            'UI_menu_UIReplayColorDamage': 'Colored for Replays with damage',
            'UI_menu_UIReplay': 'for Replays',
            'UI_menu_UIReplayDamage': 'for Replays with damage',
            'UI_menu_UIConfig': 'Config',

            'UI_color_red': 'Red',
            'UI_color_nice_red': 'Nice red',
            'UI_color_chocolate': 'Chocolate',
            'UI_color_orange': 'Orange',
            'UI_color_gold': 'Gold',
            'UI_color_cream': 'Cream',
            'UI_color_yellow': 'Yellow',
            'UI_color_green_yellow': 'Green yellow',
            'UI_color_lime': 'Lime',
            'UI_color_green': 'Green',
            'UI_color_aquamarine': 'Aquamarine',
            'UI_color_emerald': 'Emerald',
            'UI_color_cyan': 'Cyan',
            'UI_color_cornflower_blue': 'Cornflower blue',
            'UI_color_blue': 'Blue',
            'UI_color_purple': 'Purple',
            'UI_color_hot_pink': 'Hot pink',
            'UI_color_pink': 'Pink',
            'UI_color_brown': 'Brown',
            'UI_color_wg_colorBlind': 'WG Color blind',
            'UI_color_wg_enemy': 'WG Enemy',
            'UI_color_wg_ally': 'WG Ally',
            'UI_color_wg_squadMan': 'WG Squadman',
            'UI_color_wg_player': 'WG Player',

            'UI_tooltips': '<font color=\"#FFFFFF\" size=\"12\">{currentMovingAvgDamage} current moving average damage</font>\n'
                           '<font color=\"#FFFFFF\" size=\"12\">{currentDamage} current summary damage</font>\n'
                           'To <font color=\"#FFFFFF\" size=\"12\">{nextPercent}% </font>   need <font color=\"#FFFFFF\" size=\"12\">{needDamage}</font> moving average damage\n'
                           'This statistic available to last battle on this vehicle\n'
                           'To <font color=\"#FFFFFF\" size=\"12\">20% </font>   need <font color=\"#F8F400\" size=\"12\">~{_20}</font> moving average damage\n'
                           'To <font color=\"#FFFFFF\" size=\"12\">40% </font>   need <font color=\"#F8F400\" size=\"12\">~{_40}</font> moving average damage\n'
                           'To <font color=\"#FFFFFF\" size=\"12\">55% </font>   need <font color=\"#F8F400\" size=\"12\">~{_55}</font> moving average damage\n'
                           'To <font color=\"#FFFFFF\" size=\"12\">65% </font>   need <font color=\"#60FF00\" size=\"12\">~{_65}</font> moving average damage\n'
                           'To <font color=\"#FFFFFF\" size=\"12\">85% </font>   need <font color=\"#02C9B3\" size=\"12\">~{_85}</font> moving average damage\n'
                           'To <font color=\"#FFFFFF\" size=\"12\">95% </font>   need <font color=\"#D042F3\" size=\"12\">~{_95}</font> moving average damage\n'
                           'To <font color=\"#FFFFFF\" size=\"12\">100% </font>  need <font color=\"#D042F3\" size=\"12\">~{_100}</font> moving average damage',

            'battleMessageSizeUp': 'MoE mod: Size <b>+10%</b>',
            'battleMessageSizeDown': 'MoE mod: Size <b>-10%</b>',
            'battleMessageSizeLimitMin': 'MoE mod: Reached <b>minimum[10%]</b>',
            'battleMessageSizeLimitMax': 'MoE mod: Reached <b>maximum[1000%]</b>',
            'battleMessageSizeReset': 'MoE mod: Reset Settings</b>',

            'NaN': '[<b>NaN</b>]',
            'UI_HangarStatsStart': '<b>{currentPercent}<font size=\"14\">[{currentDamage}]</font> </b>',
            'UI_HangarStatsEnd': '{c_damageToMark65}, {c_damageToMark85}\n{c_damageToMark95}, {c_damageToMark100}'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        textExamples = []
        UIKey = 'UI_menu_'
        UIList = ('UIConfig', 'UIskill4ltu', 'UIMyp', 'UIspoter', 'UIcircon', 'UIReplay', 'UIReplayDamage', 'UIReplayColor', 'UIReplayColorDamage', 'UIoldskool', 'UIspoterNew', 'UIkorbenDallasNoMercy')
        xColorUP = self.tb.createOptions('upColor', ("<font color='%s'>%s</font>" % (x[1], self.i18n[x[0]]) for x in self.colors.iteritems()))
        xColorUP['tooltip'] = xColorUP['tooltip'].replace('{/BODY}', '\n'.join(textExamples) + '{/BODY}')
        xColorDown = self.tb.createOptions('downColor', ("<font color='%s'>%s</font>" % (x[1], self.i18n[x[0]]) for x in self.colors.iteritems()))
        xColorDown['tooltip'] = xColorDown['tooltip'].replace('{/BODY}', '\n'.join(textExamples) + '{/BODY}')
        xColorUnknown = self.tb.createOptions('unknownColor', ("<font color='%s'>%s</font>" % (x[1], self.i18n[x[0]]) for x in self.colors.iteritems()))
        xColorUnknown['tooltip'] = xColorUnknown['tooltip'].replace('{/BODY}', '\n'.join(textExamples) + '{/BODY}')
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showInStatistic'),
                self.tb.createControl('showInReplay'),
                self.tb.createControl('showInBattle'),
                self.tb.createControl('background'),
                self.tb.createOptions('UI', [self.i18n[UIKey + x] for x in UIList]),
                xColorUP,
                xColorDown,
                xColorUnknown
            ],
            'column2': [
                self.tb.createHotKey('buttonShow'),
                self.tb.createHotKey('buttonReset'),
                self.tb.createHotKey('buttonSizeUp'),
                self.tb.createHotKey('buttonSizeDown')
            ]
        }

    # noinspection PyTypeChecker
    def onApplySettings(self, settings):
        if 'panel' in settings:
            settings['panel'].pop('text', None)
        if 'panel' in settings:
            if 'x' in settings['panel']:
                settings['panel']['x'] = self.data['panel']['x'] * 1.0
            if 'y' in settings['panel']:
                settings['panel']['y'] = self.data['panel']['y'] * 1.0
            if 'alpha' in settings['panel']:
                settings['panel']['alpha'] = self.data['panel']['alpha'] * 1.0
            if 'height' in settings['panel']:
                settings['panel']['height'] = self.data['panel']['height'] * 1.0
            if 'width' in settings['panel']:
                settings['panel']['width'] = self.data['panel']['width'] * 1.0
        super(ConfigInterface, self).onApplySettings(settings)

    def readCurrentSettings(self, quiet=True):
        self.values = loadJson(self.ID, self.ID + '_stats', self.values, self.configPath)
        loadJson(self.ID, self.ID + '_stats', self.values, self.configPath, True, quiet=quiet)


class Worker(object):

    def __init__(self):
        self.altMode = False
        self.movingAvgDamage = 0.0
        self.damageRating = 0.0
        self.battleDamage = 0.0
        self.battleCount = 0
        self.RADIO_ASSIST = 0.0
        self.TRACK_ASSIST = 0.0
        self.STUN_ASSIST = 0.0
        self.TANKING = 0.0
        self.killed = False
        self.level = False
        self.values = [0, 0, 0, 0, datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1, datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1]
        self.name = ''
        self.dossier = None
        self.initiated = False
        self.replay = False
        self.formatStrings = {'status': '', 'battleMarkOfGun': '', 'currentMarkOfGun': '', 'nextMarkOfGun': '', 'damageCurrent': '', 'damageCurrentPercent': '', 'damageNextPercent': '', 'damageToMark65': '', 'damageToMark85': '', 'damageToMark95': '', 'damageToMark100': '', 'damageToMarkInfo': '', 'damageToMarkInfoLevel': '', 'c_status': '', 'c_battleMarkOfGun': '', 'c_currentMarkOfGun': '', 'c__nextMarkOfGun': '', 'c_damageCurrent': '', 'c_damageCurrentPercent': '', 'c_damageNextPercent': '', 'c_damageToMark65': '', 'c_damageToMark85': '', 'c_damageToMark95': '', 'c_damageToMark100': '', 'c_damageToMarkInfo': '', 'c_damageToMarkInfoLevel': '', 'colorOpen': '<font color="{color}">', 'colorClose': '</font>', 'color': '', 'assistSpot': config.data['battleMessage{assistSpot}'], 'assistTrack': config.data['battleMessage{assistTrack}'], 'assistSpam': config.data['battleMessage{assistSpam}']}
        self.messages = {
            'battleMessageskill4ltu': '<font size=\"20\">{c_battleMarkOfGun} ({currentMarkOfGun}){status}</font>\n',
            'battleMessageskill4ltuAlt': '<font size=\"20\">{c_battleMarkOfGun} ({currentMarkOfGun}){status}</font>\n'
                                         '<font size=\"12\">{c_damageCurrent} ({damageCurrentPercent})</font>',
            'battleMessagesMyp': '<font size=\"20\">{c_battleMarkOfGun}{c_damageCurrent}{status}</font>\n',
            'battleMessagesMypAlt': '<font size=\"20\">{c_battleMarkOfGun}{c_damageCurrent}{status}</font>\n'
                                    '<font size=\"15\">{currentMarkOfGun}{damageCurrentPercent}</font>',
            'battleMessagesspoter': '<font size=\"20\">{c_battleMarkOfGun}:{c_damageCurrent}{assistCurrent}</font>\n'
                                    '<font size=\"15\">{c_nextMarkOfGun}:{c_damageNextPercent}\n'
                                    '{currentMarkOfGun}:{damageCurrentPercent}</font>',
            'battleMessagesspoterAlt': '<font size=\"20\">{c_battleMarkOfGun}:{c_damageCurrent}{assistCurrent}</font>\n'
                                       '<font size=\"15\">{c_nextMarkOfGun}:{c_damageNextPercent}\n'
                                       '{currentMarkOfGun}:{damageCurrentPercent}</font>\n'
                                       '<font size=\"12\">{c_damageToMark65}{c_damageToMark85}\n'
                                       '{c_damageToMark95}{c_damageToMark100}</font>',
            'battleMessagescircon': '<font size=\"14\">{currentMarkOfGun}</font> <font size=\"10\">{damageCurrentPercent}</font><font size=\"14\"> ~ {c_nextMarkOfGun}</font> <font size=\"10\">{c_damageNextPercent}</font>\n'
                                    '<font size=\"20\">{c_battleMarkOfGun}{status}</font><font size=\"14\">{c_damageCurrent}</font>',
            'battleMessagescirconAlt': '<font size=\"14\">{currentMarkOfGun}</font> <font size=\"10\">{damageCurrentPercent}</font><font size=\"14\"> ~ {c_nextMarkOfGun}</font> <font size=\"10\">{c_damageNextPercent}</font>\n'
                                       '<font size=\"20\">{c_battleMarkOfGun}{status}</font><font size=\"14\">{c_damageCurrent}</font>\n'
                                       '<font size=\"12\">{c_damageToMark65}{c_damageToMark85}\n'
                                       '{c_damageToMark95}{c_damageToMark100}</font>',
            'battleMessageReplay': '<font size=\"72\">{battleMarkOfGun}</font>',
            'battleMessageReplayAlt': '<font size=\"72\">{battleMarkOfGun}</font><font size=\"32\">{damageCurrent}</font>',
            'battleMessageReplayColor': '<font size=\"72\">{c_battleMarkOfGun}</font>',
            'battleMessageReplayColorAlt': '<font size=\"72\">{c_battleMarkOfGun}</font><font size=\"32\">{c_damageCurrent}</font>',
            'battleMessageoldskool': '<font size=\"15\">{c_battleMarkOfGun}\n{c_damageCurrent}{assistCurrent}</font>',
            'battleMessageoldskoolAlt': '<font size=\"15\">{c_battleMarkOfGun}<tab>{c_nextMarkOfGun}\n{c_damageCurrent}{assistCurrent}<tab>{c_damageNextPercent}</font>',
            'battleMessagesspoterNew': '<font size=\"32\">{c_battleMarkOfGun}{c_damageCurrent}</font>',
            'battleMessagesspoterNewAlt': '<font size=\"32\">{c_nextMarkOfGun}:{c_damageNextPercent}</font>\n<font size=\"32\">{c_damageToMark100}</font>',
            'battleMessageskorbenDallasNoMercy': '<p align=\"right\"><font size=\"54\"><font color=\"{status}\">{battleMarkOfGun}</font></font></p>\n'
                                                 '<p align=\"right\"><font size=\"22\">{damageCurrent}</font></p>\n'
                                                 '<p align=\"right\"><font size=\"22\">{damageCurrentPercent}</font></p>',
            'battleMessageskorbenDallasNoMercyAlt': '<p align=\"right\"><font size=\"54\"><font color=\"{status}\">{battleMarkOfGun}</font></font></p>\n'
                                                    '<p align=\"right\"><font size=\"22\">{damageCurrent}</font></p>\n'
                                                    '<p align=\"right\"><font size=\"22\">{damageCurrentPercent}</font></p>',

        }
        self.levels = []
        self.damages = []
        self.battleMessage = config.data['battleMessage'] if not self.altMode else config.data['battleMessageAlt']
        self.checkBattleMessage()
        self.health = {}
        self.battleDamageRatingIndex = []
        self.startCount = 0
        self.gunLevel = 0
        self.dateTime = datetime.datetime.toordinal(datetime.datetime.utcnow())

    def checkBattleMessage(self):
        if not config.data['UI']:
            self.battleMessage = config.data['battleMessage'] if not self.altMode else config.data['battleMessageAlt']
        if config.data['UI'] == 1:
            self.battleMessage = self.messages['battleMessageskill4ltu'] if not self.altMode else self.messages['battleMessageskill4ltuAlt']

        if config.data['UI'] == 2:
            self.battleMessage = self.messages['battleMessagesMyp'] if not self.altMode else self.messages['battleMessagesMypAlt']

        if config.data['UI'] == 3:
            self.battleMessage = self.messages['battleMessagesspoter'] if not self.altMode else self.messages['battleMessagesspoterAlt']

        if config.data['UI'] == 4:
            self.battleMessage = self.messages['battleMessagescircon'] if not self.altMode else self.messages['battleMessagescirconAlt']

        if config.data['UI'] == 5:
            self.battleMessage = self.messages['battleMessageReplay'] if not self.altMode else self.messages['battleMessageReplayAlt']

        if config.data['UI'] == 6:
            self.battleMessage = self.messages['battleMessageReplayAlt'] if not self.altMode else self.messages['battleMessageReplayAlt']

        if config.data['UI'] == 7:
            self.battleMessage = self.messages['battleMessageReplayColor'] if not self.altMode else self.messages['battleMessageReplayColorAlt']

        if config.data['UI'] == 8:
            self.battleMessage = self.messages['battleMessageReplayColorAlt'] if not self.altMode else self.messages['battleMessageReplayColorAlt']

        if config.data['UI'] == 9:
            self.battleMessage = self.messages['battleMessageoldskool'] if not self.altMode else self.messages['battleMessageoldskoolAlt']

        if config.data['UI'] == 10:
            self.battleMessage = self.messages['battleMessagesspoterNew'] if not self.altMode else self.messages['battleMessagesspoterNewAlt']

        if config.data['UI'] == 11:
            self.battleMessage = self.messages['battleMessageskorbenDallasNoMercy'] if not self.altMode else self.messages['battleMessageskorbenDallasNoMercyAlt']

    def clearData(self):
        self.altMode = False
        self.movingAvgDamage = 0.0
        self.damageRating = 0.0
        self.battleDamage = 0.0
        self.battleCount = 0
        self.RADIO_ASSIST = 0.0
        self.TRACK_ASSIST = 0.0
        self.STUN_ASSIST = 0.0
        self.TANKING = 0.0
        self.killed = False
        self.level = False
        self.values = [0, 0, 0, 0, datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1, datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1]
        self.name = ''
        self.initiated = False
        self.replay = False
        self.formatStrings = {'status': '', 'battleMarkOfGun': '', 'currentMarkOfGun': '', 'nextMarkOfGun': '', 'damageCurrent': '', 'damageCurrentPercent': '', 'damageNextPercent': '', 'damageToMark65': '', 'damageToMark85': '', 'damageToMark95': '', 'damageToMark100': '', 'damageToMarkInfo': '', 'damageToMarkInfoLevel': '', 'c_status': '', 'c_battleMarkOfGun': '', 'c_currentMarkOfGun': '', 'c__nextMarkOfGun': '', 'c_damageCurrent': '', 'c_damageCurrentPercent': '', 'c_damageNextPercent': '', 'c_damageToMark65': '', 'c_damageToMark85': '', 'c_damageToMark95': '', 'c_damageToMark100': '', 'c_damageToMarkInfo': '', 'c_damageToMarkInfoLevel': '', 'colorOpen': '<font color="{color}">', 'colorClose': '</font>', 'color': '', 'assistSpot': config.data['battleMessage{assistSpot}'], 'assistTrack': config.data['battleMessage{assistTrack}'], 'assistSpam': config.data['battleMessage{assistSpam}']}
        self.levels = []
        self.damages = []
        self.checkBattleMessage()
        self.health.clear()
        self.battleDamageRatingIndex = []
        self.dateTime = datetime.datetime.toordinal(datetime.datetime.utcnow())

    def getCurrentHangarData(self):
        if g_currentVehicle.item:
            self.damageRating = g_currentVehicle.getDossier().getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
            self.movingAvgDamage = g_currentVehicle.getDossier().getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
            self.battleCount = g_currentVehicle.getDossier().getRandomStats().getBattlesCountVer2()
            self.level = g_currentVehicle.item.level > 4
            self.name = '%s' % g_currentVehicle.item.name
            if self.level and self.movingAvgDamage:
                dBid = self.check_player_thread()
                if dBid not in config.values:
                    config.values[dBid] = {}
                if self.name in config.values[dBid]:
                    self.requestCurData(self.damageRating, self.movingAvgDamage)
                else:
                    self.requestNewData(self.damageRating, self.movingAvgDamage)

    def onBattleEvents(self, events):
        if not config.data['enabled']:
            return
        guiSessionProvider = getPlayer().guiSessionProvider
        if guiSessionProvider.shared.vehicleState.getControllingVehicleID() == getPlayer().playerVehicleID:
            for data in events:
                feedbackEvent = feedback_events.PlayerFeedbackEvent.fromDict(data)
                eventType = feedbackEvent.getBattleEventType()
                if eventType in DAMAGE_EVENTS:
                    extra = feedbackEvent.getExtra()
                    if extra:
                        if eventType == BATTLE_EVENT_TYPE.RADIO_ASSIST:
                            self.RADIO_ASSIST += float(extra.getDamage())
                        if eventType == BATTLE_EVENT_TYPE.TRACK_ASSIST:
                            self.TRACK_ASSIST += float(extra.getDamage())
                        if eventType == BATTLE_EVENT_TYPE.STUN_ASSIST:
                            self.STUN_ASSIST += float(extra.getDamage())
                        if eventType == BATTLE_EVENT_TYPE.TANKING:
                            self.TANKING += float(extra.getDamage())
                        if eventType == BATTLE_EVENT_TYPE.DAMAGE:
                            arenaDP = guiSessionProvider.getArenaDP()
                            if arenaDP.isEnemyTeam(arenaDP.getVehicleInfo(feedbackEvent.getTargetID()).team):
                                self.battleDamage += float(extra.getDamage())
            self.calc()

    def shots(self, avatar, newHealth, attackerID):
        if not config.data['enabled']:
            return
        if not avatar.isStarted:
            return
        if newHealth > 0 >= avatar.health:
            return
        player = getPlayer()
        if avatar.id not in self.health:
            self.health[avatar.id] = max(0, avatar.health)
        if not avatar.isPlayerVehicle and attackerID == player.playerVehicleID:
            arenaDP = player.guiSessionProvider.getArenaDP()
            vo = arenaDP.getVehicleInfo(avatar.id)
            if not arenaDP.isEnemyTeam(vo.team):
                self.battleDamage -= float(max(0, self.health[avatar.id] - newHealth))
                self.calc()
        self.health[avatar.id] = max(0, avatar.health)

    def initVehicle(self, avatar):
        if not avatar.isStarted:
            return
        self.health[avatar.id] = max(0, avatar.health)

    def requestNewData(self, damageRating, movingAvgDamage):
        p0 = 0
        d0 = 0
        p1 = damageRating
        d1 = movingAvgDamage
        t0 = datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1
        self.values = [p0, d0, p1, d1, t0, t0]
        config.values[self.check_player_thread()][self.name] = self.values
        self.initiated = False

    def requestCurData(self, damageRating, movingAvgDamage):
        self.values = config.values[self.check_player_thread()][self.name]
        if len(self.values) == 4:
            tm = datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1
            self.values.extend([tm, tm])
            config.values[self.check_player_thread()][self.name] = self.values
        if movingAvgDamage not in self.values or datetime.datetime.toordinal(datetime.datetime.utcnow()) >= self.values[5] + 1:
            p0 = self.values[2]
            d0 = self.values[3]
            t0 = self.values[5]
            p1 = damageRating
            d1 = movingAvgDamage
            t1 = datetime.datetime.toordinal(datetime.datetime.utcnow())
            self.values = [p0, d0, p1, d1, t0, t1]
            config.values[self.check_player_thread()][self.name] = self.values
        if self.values[0] == self.values[2] and self.values[1] == self.values[3]:
            self.values[3] += 10
            self.values[5] = datetime.datetime.toordinal(datetime.datetime.utcnow())
            config.values[self.check_player_thread()][self.name] = self.values
        EDn = self.battleDamage + max(self.RADIO_ASSIST, self.TRACK_ASSIST, self.STUN_ASSIST)
        k = 0.0198019801980198022206547392443098942749202251434326171875  # 2 / (100.0 + 1)
        EMA = k * EDn + (1 - k) * self.movingAvgDamage
        p0, d0, p1, d1, t0, t1 = self.values
        result = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0) if p0 != 100.0 or p1 != 100.0 else 100.0
        nextMark = round(min(100.0, result), 2) if result > 0 else 0.0
        self.initiated = self.values[1] and not nextMark >= self.damageRating and not self.damageRating - nextMark > 3

    def getColor(self, percent, damage):
        a = filter(lambda x: x <= round(percent, 2), self.levels)
        i = self.levels.index(a[-1]) if a else 0
        if config.data['showInBattleHalfPercents']:
            n = min(i + 1, len(self.levels) - 1)
        else:
            n = max(2, min(i + 1, len(self.levels) - 1))
        idx = filter(lambda x: x >= damage, self.battleDamageRatingIndex)
        colorNowDamage = config.battleDamageRating[self.battleDamageRatingIndex.index(idx[0])] if idx else config.battleDamageRating[-1]
        idx = filter(lambda x: x >= self.damages[n], self.battleDamageRatingIndex)
        colorNextDamage = config.battleDamageRating[self.battleDamageRatingIndex.index(idx[0])] if idx else config.battleDamageRating[-1]
        idx = filter(lambda x: x >= percent, config.levels)[0]
        colorNextPercent = self.battleDamageRatingIndex[config.levels.index(idx)] if idx else config.battleDamageRating[-1]
        levels = self.levels[n] if self.levels else 0
        damages = self.damages[n] if self.damages else 0
        return levels, damages, colorNowDamage, colorNextDamage, colorNextPercent

    def calcBattlePercents(self):
        if len(self.values) == 4:
            p0, d0, p1, d1 = self.values
        else:
            p0, d0, p1, d1, t0, t1 = self.values
        _, _, p20, p40, p55, p65, p85, p95, p100 = worker.calcStatistics(self.damageRating, self.movingAvgDamage)
        curPercent = p1
        limit = min(30000, p100 * 5)
        nextPercent = float(int(curPercent + 1))
        halfPercent = nextPercent - curPercent >= 0.5
        EDn = 0
        k = 0.0198019801980198022206547392443098942749202251434326171875  # 2 / (100.0 + 1)
        EMA = k * EDn + (1 - k) * d1
        start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(start)
        self.damages.append(EDn)
        while start <= curPercent < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        if config.data['UI'] == 11:
            self.formatStrings['damageCurrentPercent'] = '<b>%.0f</b>' % EDn if EDn < limit or self.replay else config.i18n['NaN']
        else:
            self.formatStrings['damageCurrentPercent'] = config.data['battleMessage{damageCurrentPercent}'] % EDn if EDn < limit or self.replay else config.i18n['NaN']
        self.levels.append(curPercent)
        self.damages.append(EDn)
        if halfPercent and config.data['showInBattleHalfPercents']:
            halfPercent = nextPercent - 0.5
            while start <= halfPercent < 100 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(halfPercent)
            self.damages.append(EDn)

        while start <= nextPercent < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent)
        self.damages.append(EDn)

        if config.data['showInBattleHalfPercents']:
            nextPercent_0_5 = nextPercent + 0.5
            while start <= nextPercent_0_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent_0_5)
            self.damages.append(EDn)

        nextPercent1 = nextPercent + 1.0
        while start <= nextPercent1 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent1)
        self.damages.append(EDn)

        if config.data['showInBattleHalfPercents']:
            nextPercent1_5 = nextPercent + 1.5
            while start <= nextPercent1_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent1_5)
            self.damages.append(EDn)

        nextPercent2 = nextPercent + 2.0
        while start <= nextPercent2 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent2)
        self.damages.append(EDn)

        if config.data['showInBattleHalfPercents']:
            nextPercent2_5 = nextPercent + 2.5
            while start <= nextPercent2_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent2_5)
            self.damages.append(EDn)

        nextPercent3 = nextPercent + 3.0
        while start <= nextPercent3 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent3)
        self.damages.append(EDn)
        if config.data['showInBattleHalfPercents']:
            nextPercent3_5 = nextPercent + 3.5
            while start <= nextPercent3_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent3_5)
            self.damages.append(EDn)

        nextPercent4 = nextPercent + 4.0
        while start <= nextPercent4 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent4)
        self.damages.append(EDn)
        if config.data['showInBattleHalfPercents']:
            nextPercent4_5 = nextPercent + 4.5
            while start <= nextPercent4_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent4_5)
            self.damages.append(EDn)

        nextPercent5 = nextPercent + 5.0
        while start <= nextPercent5 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent5)
        self.damages.append(EDn)
        if config.data['showInBattleHalfPercents']:
            nextPercent5_5 = nextPercent + 5.5
            while start <= nextPercent5_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent5_5)
            self.damages.append(EDn)
        if EDn >= min(30000, EDn * 5):
            self.initiated = False

        self.battleDamageRatingIndex = [0, p20, p40, p55, p65, p85, p95, p100]

        self.formatStrings['damageToMark65'] = config.data['battleMessage{damageToMark65}'] % p65
        self.formatStrings['c_damageToMark65'] = '<font color="%s">%s</font>' % (config.ratings['good'], self.formatStrings['damageToMark65'])

        self.formatStrings['damageToMark85'] = config.data['battleMessage{damageToMark85}'] % p85
        self.formatStrings['c_damageToMark85'] = '<font color="%s">%s</font>' % (config.ratings['very_good'], self.formatStrings['damageToMark85'])

        self.formatStrings['damageToMark95'] = config.data['battleMessage{damageToMark95}'] % p95
        self.formatStrings['c_damageToMark95'] = '<font color="%s">%s</font>' % (config.ratings['unique'], self.formatStrings['damageToMark95'])

        self.formatStrings['damageToMark100'] = config.data['battleMessage{damageToMark100}'] % p100
        self.formatStrings['c_damageToMark100'] = '<font color="%s">%s</font>' % (config.ratings['unique'], self.formatStrings['damageToMark100'])

        self.formatStrings['damageToMarkInfo'] = config.data['battleMessage{damageToMarkInfo}'] % self.formatStrings['damageToMark100']
        self.formatStrings['c_damageToMarkInfo'] = config.data['battleMessage{c_damageToMarkInfo}'] % self.formatStrings['damageToMarkInfo']
        self.formatStrings['damageToMarkInfoLevel'] = config.data['battleMessage{damageToMarkInfoLevel}'] % 100
        self.formatStrings['c_damageToMarkInfoLevel'] = config.data['battleMessage{c_damageToMarkInfo}'] % self.formatStrings['damageToMarkInfoLevel']

        for i in [65, 85, 95, 100]:
            if self.damageRating < i:
                self.formatStrings['damageToMarkInfo'] = config.data['battleMessage{damageToMarkInfo}'] % self.formatStrings['damageToMark%s' % i]
                self.formatStrings['c_damageToMarkInfo'] = config.data['battleMessage{c_damageToMarkInfo}'] % self.formatStrings['c_damageToMark%s' % i]
                self.formatStrings['damageToMarkInfoLevel'] = config.data['battleMessage{damageToMarkInfoLevel}'] % i
                self.formatStrings['c_damageToMarkInfoLevel'] = config.data['battleMessage{c_damageToMarkInfo}'] % self.formatStrings['damageToMarkInfoLevel']
                break

    def checkMark(self, nextMark):
        levels = [65.0, 85.0, 95.0, 100.0]
        for i in levels[self.gunLevel - 4:]:
            if self.damageRating < i <= nextMark:
                return True
        return

    def keyPressed(self, event):
        if not config.data['enabled']:
            return
        player = getPlayer()
        if not player.arena:
            return
        if player.arena.bonusType != ARENA_BONUS_TYPE.REGULAR:
            return
        if self.level and self.movingAvgDamage:
            isKeyDownTrigger = event.isKeyDown()

            if event.key in [Keys.KEY_LALT, Keys.KEY_RALT]:
                if isKeyDownTrigger:
                    self.altMode = True
                    self.checkBattleMessage()
                    g_flash.setupSize()
                    self.calc()
                if event.isKeyUp():
                    self.altMode = False
                    self.checkBattleMessage()
                    g_flash.setupSize()
                    self.calc()
            if checkKeys(config.data['buttonShow']) and isKeyDownTrigger:
                config.data['UI'] += 1
                if config.data['UI'] > 11:
                    config.data['UI'] = 1
                status = [config.i18n['UI_menu_UIConfig'], config.i18n['UI_menu_UIskill4ltu'], config.i18n['UI_menu_UIMyp'], config.i18n['UI_menu_UIspoter'], config.i18n['UI_menu_UIcircon'], config.i18n['UI_menu_UIReplay'], config.i18n['UI_menu_UIReplayDamage'], config.i18n['UI_menu_UIReplayColor'], config.i18n['UI_menu_UIReplayColorDamage'], config.i18n['UI_menu_UIoldskool'], config.i18n['UI_menu_UIspoterNew'], config.i18n['UI_menu_UIkorbenDallasNoMercy']]
                message = config.i18n['UI_message'] % status[config.data['UI']]
                # if config.data['showInBattle']:
                sendPanelMessage(message)
                self.checkBattleMessage()
                g_flash.setupSize()
                self.calc()
            if checkKeys(config.data['buttonReset']) and isKeyDownTrigger:
                config.data['battleMessageSizeInPercent'] = 100
                sendPanelMessage(config.i18n['battleMessageSizeReset'])
                # noinspection PyTypeChecker
                config.data['panel']['x'] = 230.0
                g_flash.data[COMPONENT_TYPE.LABEL]['x'] = 230.0
                # noinspection PyTypeChecker
                config.data['panel']['y'] = -228.0
                g_flash.data[COMPONENT_TYPE.LABEL]['y'] = -228.0
                self.altMode = True
                self.checkBattleMessage()
                g_flash.setupSize()
                self.altMode = False
                g_flash.setupSize()
                self.calc()
            if checkKeys(config.data['buttonSizeUp']) and isKeyDownTrigger:
                config.data['battleMessageSizeInPercent'] = min(1000, config.data['battleMessageSizeInPercent'] + 10)
                message = config.i18n['battleMessageSizeUp'] + '<b>[%s]</b>' % config.data['battleMessageSizeInPercent'] if config.data['battleMessageSizeInPercent'] < 1000 else config.i18n['battleMessageSizeLimitMax']
                sendPanelMessage(message)
                self.altMode = True
                self.checkBattleMessage()
                g_flash.setupSize()
                self.altMode = False
                g_flash.setupSize()
                self.calc()
            if checkKeys(config.data['buttonSizeDown']) and isKeyDownTrigger:
                config.data['battleMessageSizeInPercent'] = max(10, config.data['battleMessageSizeInPercent'] - 10)
                message = config.i18n['battleMessageSizeDown'] + '<b>[%s]</b>' % config.data['battleMessageSizeInPercent'] if config.data['battleMessageSizeInPercent'] > 10 else config.i18n['battleMessageSizeLimitMin']
                sendPanelMessage(message)
                self.altMode = True
                self.checkBattleMessage()
                g_flash.setupSize()
                self.altMode = False
                g_flash.setupSize()
                self.calc()

    def calc(self):
        if not config.data['enabled']:
            return
        if not self.level:
            return
        if not self.movingAvgDamage:
            return
        assists = (self.RADIO_ASSIST, self.TRACK_ASSIST, self.STUN_ASSIST)
        assistCurrent = config.assists[assists.index(max(assists))]
        EDn = self.battleDamage + max(assists)
        k = 0.0198019801980198022206547392443098942749202251434326171875  # 2 / (100.0 + 1)
        EMA = k * EDn + (1 - k) * self.movingAvgDamage
        p0, d0, p1, d1, t0, t1 = self.values
        result = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        nextMark = round(min(100.0, result), 2) if result > 0.0 else 0.0
        unknown = t0 < self.dateTime or t1 < self.dateTime
        if not unknown and d0 and self.initiated or self.replay:
            if nextMark >= self.damageRating:
                self.formatStrings['color'] = '%s' % config.colors.values()[config.data['upColor']]
                if self.checkMark(nextMark):
                    self.formatStrings['color'] = '#D042F3'
                self.formatStrings['status'] = config.data['battleMessage{status}Up'] if config.data['UI'] != 11 else "#228b22"
                self.formatStrings['c_status'] = '%s%s%s' % (self.formatStrings['colorOpen'], config.data['battleMessage{c_status}Up'], self.formatStrings['colorClose'])
            else:
                self.formatStrings['color'] = '%s' % config.colors.values()[config.data['downColor']]
                if self.checkMark(nextMark):
                    self.formatStrings['color'] = '#D042F3'
                self.formatStrings['status'] = config.data['battleMessage{status}Down'] if config.data['UI'] != 11 else "#af2b1e"
                self.formatStrings['c_status'] = '%s%s%s' % (self.formatStrings['colorOpen'], config.data['battleMessage{c_status}Down'], self.formatStrings['colorClose'])
        else:
            self.formatStrings['color'] = '%s' % config.colors.values()[config.data['unknownColor']]
            self.formatStrings['status'] = config.data['battleMessage{status}Unknown'] if config.data['UI'] != 11 else "#8378FC"
            self.formatStrings['c_status'] = '%s%s%s' % (self.formatStrings['colorOpen'], config.data['battleMessage{c_status}Unknown'], self.formatStrings['colorClose'])
            unknown = True
        self.formatStrings['battleMarkOfGun'] = config.data['battleMessage{battleMarkOfGun}'] % nextMark
        self.formatStrings['c_battleMarkOfGun'] = '%s%s%s' % (self.formatStrings['colorOpen'], self.formatStrings['battleMarkOfGun'], self.formatStrings['colorClose'])
        nextMarkOfGun, damage, colorNowDamage, colorNextDamage, colorNextPercent = self.getColor(nextMark, EDn)
        self.formatStrings['nextMarkOfGun'] = config.data['battleMessage{nextMarkOfGun}'] % nextMarkOfGun
        self.formatStrings['c_nextMarkOfGun'] = '%s%s%s' % ('<font color="%s">' % colorNextPercent if not unknown else self.formatStrings['colorOpen'], self.formatStrings['nextMarkOfGun'], self.formatStrings['colorClose'])
        if config.data['UI'] == 11:
            self.formatStrings['damageCurrent'] = "<b>%.0f</b>" % EDn
        else:
            self.formatStrings['damageCurrent'] = config.data['battleMessage{damageCurrent}'] % EDn
        if config.data['UI'] == 11:
            self.formatStrings['damageNextPercent'] = "<b>%.0f</b>" % damage if damage < 30000 or self.replay else config.i18n['NaN']
        else:
            self.formatStrings['damageNextPercent'] = config.data['battleMessage{damageNextPercent}'] % damage if damage < 30000 or self.replay else config.i18n['NaN']
        self.formatStrings['c_damageCurrent'] = '%s%s%s' % ('<font color="%s">' % colorNowDamage if not unknown else self.formatStrings['colorOpen'], self.formatStrings['damageCurrent'], self.formatStrings['colorClose'])
        self.formatStrings['c_damageCurrentPercent'] = '%s%s%s' % (self.formatStrings['colorOpen'], self.formatStrings['damageCurrentPercent'], self.formatStrings['colorClose'])
        self.formatStrings['c_damageNextPercent'] = '%s%s%s' % ('<font color="%s">' % colorNextDamage if not unknown else self.formatStrings['colorOpen'], self.formatStrings['damageNextPercent'], self.formatStrings['colorClose'])
        self.formatStrings['assistCurrent'] = self.formatStrings[assistCurrent] if max(assists) else self.formatStrings['assistTrack']
        g_flash.setVisible(True)
        g_flash.set_text(self.battleMessage.format(**self.formatStrings).format(color=self.formatStrings['color']))

    @staticmethod
    def isAvailable():
        vehicle = getPlayer().getVehicleAttached()
        if vehicle is None:
            return
        return vehicle.id == getPlayer().playerVehicleID

    # noinspection PyUnusedLocal
    def onVehicleKilled(self, target_id, *args):
        if target_id == getPlayer().playerVehicleID:
            self.killed = True
            self.calc()

    def startBattle(self):
        if not config.data['enabled']:
            return
        if config.data['showInBattle']:
            message = 'Mod: Marks of Excellence %s [by github.com/spoter]' % config.ID
            message += '\nRe-Worked for [Driftkings]'
            color = 'Purple'
            sendPanelMessage(message, color)
            status = [config.i18n['UI_menu_UIConfig'], config.i18n['UI_menu_UIskill4ltu'], config.i18n['UI_menu_UIMyp'], config.i18n['UI_menu_UIspoter'], config.i18n['UI_menu_UIcircon'], config.i18n['UI_menu_UIReplay'], config.i18n['UI_menu_UIReplayDamage'], config.i18n['UI_menu_UIReplayColor'], config.i18n['UI_menu_UIReplayColorDamage'], config.i18n['UI_menu_UIoldskool'], config.i18n['UI_menu_UIspoterNew'], config.i18n['UI_menu_UIkorbenDallasNoMercy']]
            message = config.i18n['UI_message'] % status[config.data['UI']]
            sendPanelMessage(message)
        self.replay = BattleReplay.isPlaying()
        if self.replay and not config.data['showInReplay']:
            return
        self.startCount = 0
        callback(1.0, self.treadStartBattle)

    def treadStartBattle(self):
        vehicle = getPlayer().getVehicleAttached()
        if not vehicle:
            self.startCount += 1
            if self.startCount < 10:
                return callback(1.0, self.treadStartBattle)
            else:
                return

        g_flash.setVisible(False)
        dBid = self.check_player_thread()
        self.gunLevel = vehicle.publicInfo['marksOnGun']
        self.name = vehicle.typeDescriptor.name
        self.level = vehicle.typeDescriptor.level > 4
        if dBid not in config.values:
            config.values[dBid] = {}
        if self.replay:
            test = None
            if self.name in config.values[dBid]:
                test = dBid
            else:
                for ids in config.values:
                    if self.name in config.values[ids]:
                        test = ids
                        break
            if test:
                values = config.values[test][self.name]
                self.damageRating = values[2]
                self.movingAvgDamage = values[3]
            else:
                self.damageRating = 94.0
                self.movingAvgDamage = 3500.0
                self.name = 'ReplayTest'

        if self.level and self.movingAvgDamage:
            InputHandler.g_instance.onKeyDown += self.keyPressed
            InputHandler.g_instance.onKeyUp += self.keyPressed
            getPlayer().arena.onVehicleKilled += self.onVehicleKilled
            self.formatStrings['currentMarkOfGun'] = config.data['battleMessage{currentMarkOfGun}'] % self.damageRating
            self.formatStrings['c_currentMarkOfGun'] = '%s%s%s' % (self.formatStrings['colorOpen'], self.formatStrings['currentMarkOfGun'], self.formatStrings['colorClose'])
            if self.name in config.values[dBid]:
                self.requestCurData(self.damageRating, self.movingAvgDamage)
            else:
                self.requestNewData(self.damageRating, self.movingAvgDamage)
            self.calcBattlePercents()
            g_flash.setupSize()
            self.calc()
            if 'ReplayTest' not in self.name:
                config.values = loadJson(config.ID, config.ID + '_stats', config.values, config.configPath, True, quiet=not self.values)

    def endBattle(self):
        if not config.data['enabled']:
            return
        if self.replay and not config.data['showInReplay']:
            return
        if self.level and self.movingAvgDamage:
            InputHandler.g_instance.onKeyDown -= self.keyPressed
            InputHandler.g_instance.onKeyUp -= self.keyPressed
            getPlayer().arena.onVehicleKilled -= self.onVehicleKilled

    @staticmethod
    def check_player_thread():
        player = getPlayer()
        if hasattr(player, 'databaseID'):
            return '%s' % player.databaseID
        return '%s' % player.arena.vehicles[player.playerVehicleID]['accountDBID']

    @staticmethod
    def getNormalizeDigits(value):
        return int(math.ceil(value))

    @staticmethod
    def calcPercent(ema, start, end, d, p):
        while start <= end < 100.001 and ema < 30000:
            ema += 0.1
            start = ema / d * p
        return ema

    @staticmethod
    def getNormalizeDigitsCoeff(value):
        return int(math.ceil(math.ceil(value / 10.0)) * 10)

    def calcStatisticsCoeff(self, p, d):
        pC = math.floor(p) + 1
        dC = self.calcPercent(d, p, pC, d, p)

        p20 = self.calcPercent(0, 0.0, 20.0, d, p)
        p40 = self.calcPercent(p20, 20.0, 40.0, d, p)
        p55 = self.calcPercent(p40, 40.0, 55.0, d, p)
        p65 = self.calcPercent(p55, 55.0, 65.0, d, p)
        p85 = self.calcPercent(p65, 65.0, 85.0, d, p)
        p95 = self.calcPercent(p85, 85.0, 95.0, d, p)
        p100 = self.calcPercent(p95, 95.0, 100.0, d, p)

        data = [0, p20, p40, p55, p65, p85, p95, p100]

        idx = filter(lambda x: x >= p, config.levels)[0]

        limit1 = data[config.levels.index(idx) - 1]
        limit2 = data[config.levels.index(idx)]

        check = config.levels.index(idx)

        delta = limit2 - limit1

        for value in xrange(len(data)):
            if data[value] == limit1 or data[value] == limit2:
                continue
            if 0 < value < check:
                data[value] -= delta
            if value > check:
                data[value] += delta

        if pC == 101:
            pC = 100
            dC = data[7]

        return pC, dC, data[1], data[2], data[3], data[4], data[5], data[6], data[7]

    def calcStatistics(self, p, d):
        pC = math.floor(p) + 1
        dC = self.calcPercent(d, p, pC, d, p)

        p20 = self.calcPercent(0, 0.0, 20.0, d, p)
        p40 = self.calcPercent(0, 0.0, 40.0, d, p)
        p55 = self.calcPercent(0, 0.0, 55.0, d, p)
        p65 = self.calcPercent(0, 0.0, 65.0, d, p)
        p85 = self.calcPercent(0, 0.0, 85.0, d, p)
        p95 = self.calcPercent(0, 0.0, 95.0, d, p)
        p100 = self.calcPercent(0, 0.0, 100.0, d, p)

        data = [0, p20, p40, p55, p65, p85, p95, p100]

        idx = filter(lambda x: x >= p, config.levels)[0]

        limit1 = dC
        limit2 = data[config.levels.index(idx)]

        check = config.levels.index(idx)

        delta = limit2 - limit1

        for value in xrange(len(data)):
            if data[value] == limit1 or data[value] == limit2:
                continue
            if value > check:
                data[value] = self.getNormalizeDigitsCoeff(data[value] + delta)

        if pC == 101:
            pC = 100
            dC = data[7]

        return pC, dC, data[1], data[2], data[3], data[4], data[5], data[6], data[7]


class Flash(object):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self):
        self.name = {}
        self.data = {}

    def startBattle(self):
        if not config.data['enabled']:
            return
        if BattleReplay.isPlaying() and not config.data['showInReplay']:
            return
        self.data = self.setup()
        COMPONENT_EVENT.UPDATED += self.update
        self.createObject(COMPONENT_TYPE.LABEL, self.data[COMPONENT_TYPE.LABEL])
        self.updateObject(COMPONENT_TYPE.LABEL, {'background': config.data['background']})
        g_guiResetters.add(self.screenResize)
        self.setupSize()

    def stopBattle(self):
        if not config.data['enabled']:
            return
        if BattleReplay.isPlaying() and not config.data['showInReplay']:
            return
        g_guiResetters.remove(self.screenResize)
        COMPONENT_EVENT.UPDATED -= self.update
        self.deleteObject(COMPONENT_TYPE.LABEL)

    def deleteObject(self, name):
        g_guiFlash.deleteComponent(self.name[name])

    def createObject(self, name, data):
        g_guiFlash.createComponent(self.name[name], name, data)

    def updateObject(self, name, data):
        g_guiFlash.updateComponent(self.name[name], data)

    def animateObject(self, name, data, time=1.0):
        g_guiFlash.animateComponent(self.name[name], time, data, True)

    # noinspection PyTypeChecker
    def update(self, alias, props):
        if str(alias) == str(config.ID):
            x = props.get('x', config.data['panel']['x'])
            if x and x != config.data['panel']['x']:
                config.data['panel']['x'] = x
                self.data[COMPONENT_TYPE.LABEL]['x'] = x
            y = props.get('y', config.data['panel']['y'])
            if y and y != config.data['panel']['y']:
                config.data['panel']['y'] = y
                self.data[COMPONENT_TYPE.LABEL]['y'] = y
            self.setupSize()
            print '%s Flash coordinates updated : y = %i, x = %i, props: %s' % (alias, config.data['panel']['y'], config.data['panel']['x'], props)

    def setup(self):
        self.name = {
            COMPONENT_TYPE.LABEL: '%s' % config.ID
        }
        self.data = {
            COMPONENT_TYPE.LABEL: {
                'index': 10000,
                'x': -226.0,
                'y': -226.0,
                'width': 183.0,
                'height': 50.0,
                'drag': True,
                'border': True,
                'alignX': 'left',
                'alignY': 'bottom',
                'visible': True,
                'text': '',
                'shadow': {'distance': 0, 'angle': 0, 'color': 0x000000, "alpha": 90, 'blurX': 1, 'blurY': 1, 'strength': 3000, 'quality': 1}
            },

        }
        for key, value in config.data['panel'].items():
            if key in self.data[COMPONENT_TYPE.LABEL]:
                self.data[COMPONENT_TYPE.LABEL][key] = value
        return self.data

    def setupSize(self, h=None, w=None):
        height = config.data['panelSize'].get('heightNormal', 50.0) if not worker.altMode else config.data['panelSize'].get('heightAlt', 80.0)
        width = config.data['panelSize'].get('widthNormal', 163.0) if not worker.altMode else config.data['panelSize'].get('widthAlt', 163.0)
        if config.data['UI'] == 1:
            height = 30.0 if not worker.altMode else 45.0
            width = 152.0 if not worker.altMode else 152.0
        if config.data['UI'] == 2:
            height = 30.0 if not worker.altMode else 50.0
            width = 130.0 if not worker.altMode else 130.0
        if config.data['UI'] == 3:
            height = 70.0 if not worker.altMode else 100.0
            width = 144.0 if not worker.altMode else 144.0
        if config.data['UI'] == 4:
            height = 50.0 if not worker.altMode else 80.0
            width = 163.0 if not worker.altMode else 163.0

        if config.data['UI'] in (5, 6, 7, 8):
            height = 82.0 if not worker.altMode else 82.0
            width = 343.0 if not worker.altMode else 343.0
        if config.data['UI'] == 9:
            height = 42.0 if not worker.altMode else 42.0
            width = 54.0 if not worker.altMode else 115.0
        if config.data['UI'] == 10:
            height = 50.0 if not worker.altMode else 90.0
            width = 183.0 if not worker.altMode else 183.0
        if config.data['UI'] == 11:
            height = 130.0 if not worker.altMode else 130.0
            width = 160.0 if not worker.altMode else 160.0
        if h is not None and w is not None:
            height = h
            width = w
        height = height * config.data['battleMessageSizeInPercent'] / 100.0
        width = width * config.data['battleMessageSizeInPercent'] / 100.0

        for name in self.data:
            self.data[name]['height'] = height
            self.data[name]['width'] = width
        self.data[COMPONENT_TYPE.LABEL]['height'] = height
        self.data[COMPONENT_TYPE.LABEL]['width'] = width
        self.screenResize()
        x = self.data[COMPONENT_TYPE.LABEL]['x']
        y = self.data[COMPONENT_TYPE.LABEL]['y']
        data = {'height': height, 'width': width, 'x': x, 'y': y}
        self.updateObject(COMPONENT_TYPE.LABEL, data)

    @staticmethod
    def textRepSize(message):
        mod = False
        text = ''
        count = 0
        for ids in message.split('\"'):
            if count:
                text += '"'
            if mod:
                text += '%s' % (int(ids) * config.data['battleMessageSizeInPercent'] / 100)
                mod = False
            else:
                text += '%s' % ids
            if 'size=' in ids:
                mod = True
            count += 1
        return text

    def set_text(self, text):
        txt = '<font face="%s" color="#FFFFFF" vspace="-3" align="baseline" >%s</font>' % (config.data['font'], text)
        self.updateObject(COMPONENT_TYPE.LABEL, {'text': self.textRepSize(txt)})

    def setVisible(self, status):
        data = {'visible': status}
        self.updateObject(COMPONENT_TYPE.LABEL, data)
        if config.data['UI'] in (5, 6, 7, 8, 11):
            data = {'background': False}
        else:
            data = {'background': config.data['background']}
        self.updateObject(COMPONENT_TYPE.LABEL, data)

    @staticmethod
    def screenFix(screen, value, mod, align=1):
        if align == 1:
            if value + mod > screen:
                return float(max(0, screen - mod))
            if value < 0:
                return 0.0
        if align == -1:
            if value - mod < -screen:
                return min(0, -screen + mod)
            if value > 0:
                return 0.0
        if align == 0:
            scr = screen / 2.0
            if value < scr:
                return float(scr - mod)
            if value > -scr:
                return float(-scr)
        return value

    # noinspection PyTypeChecker
    # noinspection PyArgumentEqualDefault
    def screenResize(self):
        curScr = GUI.screenResolution()
        scale = float(self.settingsCore.interfaceScale.get())
        xMo, yMo = curScr[0] / scale, curScr[1] / scale
        x = config.data['panel'].get('x', None)
        if config.data['panel']['alignX'] == COMPONENT_ALIGN.LEFT:
            x = self.screenFix(xMo, config.data['panel']['x'], config.data['panel']['width'], 1)
        if config.data['panel']['alignX'] == COMPONENT_ALIGN.RIGHT:
            x = self.screenFix(xMo, config.data['panel']['x'], config.data['panel']['width'], -1)
        if config.data['panel']['alignX'] == COMPONENT_ALIGN.CENTER:
            x = self.screenFix(xMo, config.data['panel']['x'], config.data['panel']['width'], 0)
        if x is not None:
            if x != config.data['panel']['x']:
                config.data['panel']['x'] = x
                self.data[COMPONENT_TYPE.LABEL]['x'] = x
        y = config.data['panel'].get('y', None)
        if config.data['panel']['alignY'] == COMPONENT_ALIGN.TOP:
            y = self.screenFix(yMo, config.data['panel']['y'], config.data['panel']['height'], 1)
        if config.data['panel']['alignY'] == COMPONENT_ALIGN.BOTTOM:
            y = self.screenFix(yMo, config.data['panel']['y'], config.data['panel']['height'], -1)
        if config.data['panel']['alignY'] == COMPONENT_ALIGN.CENTER:
            y = self.screenFix(yMo, config.data['panel']['y'], config.data['panel']['height'], 0)
        if y is not None:
            if y != config.data['panel']['y']:
                config.data['panel']['y'] = y
                self.data[COMPONENT_TYPE.LABEL]['y'] = y
        self.updateObject(COMPONENT_TYPE.LABEL, {'x': x, 'y': y})

    def getData(self):
        return self.data

    def getNames(self):
        return self.name


g_flash = Flash()
config = ConfigInterface()
worker = Worker()
statistic_mod = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(CrewWidget, '_CrewWidget__updateWidgetModel')
def new_CrewWidget(func, *args):
    worker.getCurrentHangarData()
    return func(*args)


@override(PlayerAvatar, 'onBattleEvents')
def new_onBattleEvents(func, *args):
    func(*args)
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        worker.onBattleEvents(args[1])


@override(Vehicle, 'onHealthChanged')
def new_onHealthChanged(func, self, newHealth, oldHealth, attackerID, attackReasonID):
    worker.shots(self, newHealth, attackerID)
    func(self, newHealth, oldHealth, attackerID, attackReasonID)


@override(Vehicle, 'startVisual')
def new_vehicleStartVisual(func, *args):
    func(*args)
    worker.initVehicle(args[0])


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        g_flash.startBattle()
        worker.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    try:
        if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
            g_flash.stopBattle()
            worker.endBattle()
            worker.clearData()
    except StandardError:
        pass
    func(*args)


@override(MarkOnGunAchievement, 'getUserCondition')
def new_getUserCondition(func, *args):
    if config.data['enabled'] and config.data['showInStatistic']:
        if worker.dossier is not None:
            targetData = worker.dossier
            damage = ProfileUtils.getValueOrUnavailable(ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamage()))
            # noinspection PyProtectedMember
            track = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedTrack))
            # noinspection PyProtectedMember
            radio = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedRadio))
            stun = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamageAssistedStun())
            currentDamage = int(damage + max(track, radio, stun))
            damageRating = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
            movingAvgDamage = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
            if damageRating:
                pC, dC, p20, p40, p55, p65, p85, p95, p100 = worker.calcStatistics(damageRating, movingAvgDamage)
                color = ['#F8F400', '#F8F400', '#60FF00', '#02C9B3', '#D042F3', '#D042F3']
                levels = [p55, p65, p85, p95, p100, 10000000]
                data = {'nextPercent': '%.0f' % pC,
                        'needDamage': '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= int(dC), levels)[0])], int(dC)),
                        'currentMovingAvgDamage': '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= movingAvgDamage, levels)[0])], movingAvgDamage),
                        'currentDamage': '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= currentDamage, levels)[0])], currentDamage),
                        '_20': worker.getNormalizeDigits(p20),
                        '_40': worker.getNormalizeDigits(p40),
                        '_55': worker.getNormalizeDigits(p55),
                        '_65': worker.getNormalizeDigits(p65),
                        '_85': worker.getNormalizeDigits(p85),
                        '_95': worker.getNormalizeDigits(p95),
                        '_100': worker.getNormalizeDigits(p100)
                        }
                temp = config.i18n['UI_tooltips'].format(**data)
                return temp
    return func(*args)


@override(MarkOnGunAchievement, '__init__')
def new_init(func, *args):
    func(*args)
    worker.dossier = args[1]


BigWorld.MoESetupSize = g_flash.setupSize
BigWorld.MoEText = g_flash.set_text

BigWorld.MoEUpdateObject = g_flash.updateObject
BigWorld.MoEData = g_flash.getData
BigWorld.MoEName = g_flash.getNames
