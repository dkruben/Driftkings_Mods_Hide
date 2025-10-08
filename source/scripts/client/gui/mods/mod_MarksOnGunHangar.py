# -*- coding: utf-8 -*-
import datetime
import math
from collections import OrderedDict

import BigWorld
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from CurrentVehicle import g_currentVehicle
from Vehicle import Vehicle
from constants import ARENA_BONUS_TYPE
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_ON_GUN_RECORD
from gui.Scaleform.daapi.view.lobby.hangar.ammunition_panel import AmmunitionPanel
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.battle_control.controllers import feedback_events
from gui.impl.lobby.crew.widget.crew_widget import CrewWidget
from gui.shared.formatters import text_styles
from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, logException, calculate_version

DAMAGE_EVENTS = frozenset(
    [BATTLE_EVENT_TYPE.RADIO_ASSIST, BATTLE_EVENT_TYPE.TRACK_ASSIST, BATTLE_EVENT_TYPE.STUN_ASSIST,
     BATTLE_EVENT_TYPE.DAMAGE, BATTLE_EVENT_TYPE.TANKING, BATTLE_EVENT_TYPE.RECEIVED_DAMAGE])


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.values = {}
        self.colors = OrderedDict([
            ('UI_color_red', '#FF0000'), ('UI_color_nice_red', '#FA8072'), ('UI_color_chocolate', '#D3691E'),
            ('UI_color_orange', '#FFA500'), ('UI_color_gold', '#FFD700'), ('UI_color_cream', '#FCF5C8'),
            ('UI_color_yellow', '#FFFF00'), ('UI_color_green_yellow', '#ADFF2E'), ('UI_color_lime', '#00FF00'),
            ('UI_color_green', '#008000'), ('UI_color_aquamarine', '#2AB157'), ('UI_color_emerald', '#28F09C'),
            ('UI_color_cyan', '#00FFFF'), ('UI_color_cornflower_blue', '#6595EE'), ('UI_color_blue', '#0000FF'),
            ('UI_color_purple', '#800080'), ('UI_color_hot_pink', '#FF69B5'), ('UI_color_pink', '#FFC0CB'),
            ('UI_color_brown', '#A52A2B'), ('UI_color_wg_colorBlind', '#8378FC'), ('UI_color_wg_enemy', '#DB0400'),
            ('UI_color_wg_ally', '#80D639'), ('UI_color_wg_squadMan', '#FFB964'), ('UI_color_wg_player', '#FFE041')
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
        self.battleDamageRating = [
            self.battleDamageRating0, self.battleDamageRating20, self.battleDamageRating40,
            self.battleDamageRating55, self.battleDamageRating65, self.battleDamageRating85,
            self.battleDamageRating95, self.battleDamageRating100
        ]
        self.assists = ['assistSpot', 'assistTrack', 'assistSpam']
        self.levels = [0.0, 20.0, 40.0, 55.0, 65.0, 85.0, 95.0, 100.0]
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (spoter mods)'
        self.data = {
            'enabled': True,
            'UI': 1,
            'battleMessage': '<font size="14">{c_battleMarkOfGun} ({currentMarkOfGun}) {assistCurrent}</font>',
            'battleMessageAlt': '<font size="14">{c_damageCurrent} ({c_damageNextPercent})</font>',
            'battleMessage{assistSpam}': '<img src="img://gui/maps/icons/library/efficiency/48x48/stun.png" width="16" height="16" vspace="-5"/>',
            'battleMessage{assistSpot}': '<img src="img://gui/maps/icons/library/efficiency/48x48/detection.png" width="16" height="16" vspace="-5"/>',
            'battleMessage{assistTrack}': '<img src="img://gui/maps/icons/library/efficiency/48x48/immobilized.png" width="16" height="16" vspace="-5"/>',
            'battleMessage{battleMarkOfGun}': '%.2f%%',
            'battleMessage{c_battleMarkOfGun}': '%s',
            'battleMessage{c_currentMarkOfGun}': '%s',
            'battleMessage{c_damageCurrentPercent}': '%s',
            'battleMessage{c_damageCurrent}': '%s',
            'battleMessage{c_damageNextPercent}': '%s',
            'battleMessage{c_damageToMark100}': '%s',
            'battleMessage{c_damageToMark65}': '%s',
            'battleMessage{c_damageToMark85}': '%s',
            'battleMessage{c_damageToMark95}': '%s',
            'battleMessage{c_damageToMarkInfoLevel}': '%s',
            'battleMessage{c_damageToMarkInfo}': '%s',
            'battleMessage{c_nextMarkOfGun}': '%s',
            'battleMessage{c_status}Down': 'V',
            'battleMessage{c_status}Unknown': '~',
            'battleMessage{c_status}Up': '?',
            'battleMessage{currentMarkOfGun}': '%.2f%%',
            'battleMessage{damageCurrentPercent}': '[<b>%.0f</b>]',
            'battleMessage{damageCurrent}': '[<b>%.0f</b>]',
            'battleMessage{damageNextPercent}': '[<b>%.0f</b>]',
            'battleMessage{damageToMark100}': '<b>100%%:%.0f</b>',
            'battleMessage{damageToMark65}': '<b>65%%:%.0f</b>, ',
            'battleMessage{damageToMark85}': '<b>85%%:%.0f</b>',
            'battleMessage{damageToMark95}': '<b>95%%:%.0f</b>, ',
            'battleMessage{damageToMarkInfoLevel}': '%s%%',
            'battleMessage{damageToMarkInfo}': '%s',
            'battleMessage{nextMarkOfGun}': '%.1f%%',
            'battleMessage{status}Down': '<img src="img://gui/maps/icons/messenger/status/24x24/chat_icon_user_is_busy.png "vspace="-5"/>',
            'battleMessage{status}Unknown': '<img src="img://gui/maps/icons/messenger/status/24x24/chat_icon_user_is_busy_violet.png" vspace="-5"/>',
            'battleMessage{status}Up': '<img src="img://gui/maps/icons/messenger/status/24x24/chat_icon_user_is_online.png" vspace="-5"/>',
            'downColor': 21,
            'showInBattle': True,
            'showInBattleHalfPercents': False,
            'showInReplay': True,
            'showInStatistic': True,
            'unknownColor': 16,
            'upColor': 18,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_showInBattle_text': 'Battle: Hello message',
            'UI_setting_showInBattle_tooltip': '',
            'UI_setting_showInBattleHalfPercents_text': 'Battle: show damage to +0.5%',
            'UI_setting_showInBattleHalfPercents_tooltip': '',
            'UI_setting_showInReplay_text': 'Replay[test]: enabled',
            'UI_setting_showInReplay_tooltip': 'Show in replay not good, but useful for tests.',
            'UI_setting_showInStatistic_text': 'Statistic: enabled',
            'UI_setting_showInStatistic_tooltip': '',
            'UI_setting_upColor_text': 'Battle: color when % mark up',
            'UI_setting_upColor_tooltip': '',
            'UI_setting_downColor_text': 'Battle: color when % mark down',
            'UI_setting_downColor_tooltip': '',
            'UI_setting_unknownColor_text': 'Battle: color when % mark unknown',
            'UI_setting_unknownColor_tooltip': '',
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
            'UI_setting_UI_text': 'UI in battle',
            'UI_setting_UI_tooltip': 'UI in battle Extended:\n<img src="img://objects/ui_extended.png"></img>\nSimple:\n<img src="img://objects/ui_simple.png"></img>\nConfig:\n/mods/configs/Driftkings/MarksOnGunExtended/MarksOnGunExtended.json\n',
            'UI_menu_UIskill4ltu': '<font color="#60FF00">@skill</font> choice [<font color="#60FF00">twitch.tv/skill4ltu</font>]',
            'UI_menu_UIMyp': '<font color="#D042F3">@Myp</font> choice[<font color="#D042F3">twitch.tv/myp_</font>]',
            'UI_menu_UIspoter': '<font color="#6595EE">@spoter</font> choice [<font color="#6595EE">github.com/spoter</font>]',
            'UI_menu_UIspoterNew': 'new <font color="#6595EE">@spoter</font> choice [<font color="#6595EE">github.com/spoter</font>]',
            'UI_menu_UIcircon': '<font color="#02C9B3">@Circon</font> choice [<font color="#02C9B3">twitch.tv/circon</font>]',
            'UI_menu_UIoldskool': '<font color="#FFD700">@Oldskool</font> choice [<font color="#FFD700">twitch.tv/oldskool</font>]',
            'UI_menu_UIkorbenDallasNoMercy': '<font color="#e3256b">@KorbenDallasNoMercy</font> choice [<font color="#e3256b">youtube.com/c/KorbenDallasNoMercy</font>]',
            'UI_menu_UIReplayColor': 'Colored for Replays',
            'UI_menu_UIReplayColorDamage': 'Colored for Replays with damage',
            'UI_menu_UIReplay': 'for Replays',
            'UI_menu_UIReplayDamage': 'for Replays with damage',
            'UI_menu_UIConfig': 'Config',
            'UI_tooltips': (
                '<font color="#FFFFFF" size="12">{currentMovingAvgDamage} current moving average damage</font>\n'
                '<font color="#FFFFFF" size="12">{currentDamage} current summary damage</font>\n'
                'To <font color="#FFFFFF" size="12">{nextPercent}% </font>   need '
                '<font color="#FFFFFF" size="12">{needDamage}</font> moving average damage\n'
                'This statistic available to last battle on this vehicle\n'
                'To <font color="#FFFFFF" size="12">20% </font>   need '
                '<font color="#F8F400" size="12">~{_20}</font> moving average damage\n'
                'To <font color="#FFFFFF" size="12">40% </font>   need '
                '<font color="#F8F400" size="12">~{_40}</font> moving average damage\n'
                'To <font color="#FFFFFF" size="12">55% </font>   need '
                '<font color="#F8F400" size="12">~{_55}</font> moving average damage\n'
                'To <font color="#FFFFFF" size="12">65% </font>   need '
                '<font color="#60FF00" size="12">~{_65}</font> moving average damage\n'
                'To <font color="#FFFFFF" size="12">85% </font>   need '
                '<font color="#02C9B3" size="12">~{_85}</font> moving average damage\n'
                'To <font color="#FFFFFF" size="12">95% </font>   need '
                '<font color="#D042F3" size="12">~{_95}</font> moving average damage\n'
                'To <font color="#FFFFFF" size="12">100% </font>  need '
                '<font color="#D042F3" size="12">~{_100}</font> moving average damage'
            ),
            'NaN': '[<b>NaN</b>]',
            'UI_HangarStatsStart': '<b>{currentPercent}<font size="14">[{currentDamage}]</font> </b>',
            'UI_HangarStatsEnd': '{c_damageToMark65}, {c_damageToMark85}\n{c_damageToMark95}, {c_damageToMark100}'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        textExamples = []
        UIKey = 'UI_menu_'
        UIList = (
        'UIConfig', 'UIskill4ltu', 'UIMyp', 'UIspoter', 'UIcircon', 'UIReplay', 'UIReplayDamage', 'UIReplayColor',
        'UIReplayColorDamage', 'UIoldskool', 'UIspoterNew', 'UIkorbenDallasNoMercy')
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
                self.tb.createOptions('UI', [self.i18n[UIKey + x] for x in UIList]),
            ],
            'column2': [
                xColorUP,
                xColorDown,
                xColorUnknown
            ]
        }


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
        self.formatStrings = {
            'status': '',
            'battleMarkOfGun': '',
            'currentMarkOfGun': '',
            'nextMarkOfGun': '',
            'damageCurrent': '',
            'damageCurrentPercent': '',
            'damageNextPercent': '',
            'damageToMark65': '',
            'damageToMark85': '',
            'damageToMark95': '',
            'damageToMark100': '',
            'damageToMarkInfo': '',
            'damageToMarkInfoLevel': '',
            'c_status': '',
            'c_battleMarkOfGun': '',
            'c_currentMarkOfGun': '',
            'c__nextMarkOfGun': '',
            'c_damageCurrent': '',
            'c_damageCurrentPercent': '',
            'c_damageNextPercent': '',
            'c_damageToMark65': '',
            'c_damageToMark85': '',
            'c_damageToMark95': '',
            'c_damageToMark100': '',
            'c_damageToMarkInfo': '',
            'c_damageToMarkInfoLevel': '',
            'colorOpen': '<font color="{color}">',
            'colorClose': '</font>',
            'color': '',
            'assistSpot': config.data['battleMessage{assistSpot}'],
            'assistTrack': config.data['battleMessage{assistTrack}'],
            'assistSpam': config.data['battleMessage{assistSpam}']
        }
        self.messages = {
            'battleMessageskill4ltu': '<font size="20">{c_battleMarkOfGun} ({currentMarkOfGun}){status}</font>\n',
            'battleMessageskill4ltuAlt': '<font size="20">{c_battleMarkOfGun} ({currentMarkOfGun}){status}</font>\n<font size="12">{c_damageCurrent} ({damageCurrentPercent})</font>',
            'battleMessagesMyp': '<font size="20">{c_battleMarkOfGun}{c_damageCurrent}{status}</font>\n',
            'battleMessagesMypAlt': '<font size="20">{c_battleMarkOfGun}{c_damageCurrent}{status}</font>\n<font size="15">{currentMarkOfGun}{damageCurrentPercent}</font>',
            'battleMessagesspoter': '<font size="20">{c_battleMarkOfGun}:{c_damageCurrent}{assistCurrent}</font>\n<font size="15">{c_nextMarkOfGun}:{c_damageNextPercent}\n{currentMarkOfGun}:{damageCurrentPercent}</font>',
            'battleMessagesspoterAlt': '<font size="20">{c_battleMarkOfGun}:{c_damageCurrent}{assistCurrent}</font>\n<font size="15">{c_nextMarkOfGun}:{c_damageNextPercent}\n{currentMarkOfGun}:{damageCurrentPercent}</font>\n<font size="12">{c_damageToMark65}{c_damageToMark85}\n{c_damageToMark95}{c_damageToMark100}</font>',
            'battleMessagescircon': '<font size="14">{currentMarkOfGun}</font> <font size="10">{damageCurrentPercent}</font><font size="14"> ~ {c_nextMarkOfGun}</font> <font size="10">{c_damageNextPercent}</font>\n<font size="20">{c_battleMarkOfGun}{status}</font><font size="14">{c_damageCurrent}</font>',
            'battleMessagescirconAlt': '<font size="14">{currentMarkOfGun}</font> <font size="10">{damageCurrentPercent}</font><font size="14"> ~ {c_nextMarkOfGun}</font> <font size="10">{c_damageNextPercent}</font>\n<font size="20">{c_battleMarkOfGun}{status}</font><font size="14">{c_damageCurrent}</font>\n<font size="12">{c_damageToMark65}{c_damageToMark85}\n{c_damageToMark95}{c_damageToMark100}</font>',
            'battleMessageReplay': '<font size="72">{battleMarkOfGun}</font>',
            'battleMessageReplayAlt': '<font size="72">{battleMarkOfGun}</font><font size="32">{damageCurrent}</font>',
            'battleMessageReplayColor': '<font size="72">{c_battleMarkOfGun}</font>',
            'battleMessageReplayColorAlt': '<font size="72">{c_battleMarkOfGun}</font><font size="32">{c_damageCurrent}</font>',
            'battleMessageoldskool': '<font size="15">{c_battleMarkOfGun}\n{c_damageCurrent}{assistCurrent}</font>',
            'battleMessageoldskoolAlt': '<font size="15">{c_battleMarkOfGun}<tab>{c_nextMarkOfGun}\n{c_damageCurrent}{assistCurrent}<tab>{c_damageNextPercent}</font>'
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
        self.formatStrings = {
            'status': '',
            'battleMarkOfGun': '',
            'currentMarkOfGun': '',
            'nextMarkOfGun': '',
            'damageCurrent': '',
            'damageCurrentPercent': '',
            'damageNextPercent': '',
            'damageToMark65': '',
            'damageToMark85': '',
            'damageToMark95': '',
            'damageToMark100': '',
            'damageToMarkInfo': '',
            'damageToMarkInfoLevel': '',
            'c_status': '',
            'c_battleMarkOfGun': '',
            'c_currentMarkOfGun': '',
            'c__nextMarkOfGun': '',
            'c_damageCurrent': '',
            'c_damageCurrentPercent': '',
            'c_damageNextPercent': '',
            'c_damageToMark65': '',
            'c_damageToMark85': '',
            'c_damageToMark95': '',
            'c_damageToMark100': '',
            'c_damageToMarkInfo': '',
            'c_damageToMarkInfoLevel': '',
            'colorOpen': '<font color="{color}">',
            'colorClose': '</font>',
            'color': '',
            'assistSpot': config.data['battleMessage{assistSpot}'],
            'assistTrack': config.data['battleMessage{assistTrack}'],
            'assistSpam': config.data['battleMessage{assistSpam}']}
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
        player = BigWorld.player()
        guiSessionProvider = player.guiSessionProvider
        if guiSessionProvider.shared.vehicleState.getControllingVehicleID() == player.playerVehicleID:
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

    def shots(self, avatar, newHealth, _, attackerID):
        if not config.data['enabled']:
            return
        if not avatar.isStarted:
            return
        if newHealth > 0 >= avatar.health:
            return
        player = BigWorld.player()
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
        k = 0.019801980198019802
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
        colorNextPercent = config.battleDamageRating[config.levels.index(idx)] if idx else config.battleDamageRating[-1]
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
        k = 0.019801980198019802
        EMA = k * EDn + (1 - k) * d1
        start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(start)
        self.damages.append(EDn)
        while start <= curPercent < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
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
        k = 0.019801980198019802
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
                self.formatStrings['status'] = config.data['battleMessage{status}Up']
                self.formatStrings['c_status'] = '%s%s%s' % (self.formatStrings['colorOpen'], config.data['battleMessage{c_status}Up'],
                self.formatStrings['colorClose'])
            else:
                self.formatStrings['color'] = '%s' % config.colors.values()[config.data['downColor']]
                if self.checkMark(nextMark):
                    self.formatStrings['color'] = '#D042F3'
                self.formatStrings['status'] = config.data['battleMessage{status}Down']
                self.formatStrings['c_status'] = '%s%s%s' % (self.formatStrings['colorOpen'], config.data['battleMessage{c_status}Down'],
                self.formatStrings['colorClose'])
        else:
            self.formatStrings['color'] = '%s' % config.colors.values()[config.data['unknownColor']]
            self.formatStrings['status'] = config.data['battleMessage{status}Unknown']
            self.formatStrings['c_status'] = '%s%s%s' % (self.formatStrings['colorOpen'], config.data['battleMessage{c_status}Unknown'],
            self.formatStrings['colorClose'])
            unknown = True
        self.formatStrings['battleMarkOfGun'] = config.data['battleMessage{battleMarkOfGun}'] % nextMark
        self.formatStrings['c_battleMarkOfGun'] = '%s%s%s' % (self.formatStrings['colorOpen'], self.formatStrings['battleMarkOfGun'], self.formatStrings['colorClose'])
        nextMarkOfGun, damage, colorNowDamage, colorNextDamage, colorNextPercent = self.getColor(nextMark, EDn)
        self.formatStrings['nextMarkOfGun'] = config.data['battleMessage{nextMarkOfGun}'] % nextMarkOfGun
        self.formatStrings['c_nextMarkOfGun'] = '%s%s%s' % ('<font color="%s">' % colorNextPercent if not unknown else self.formatStrings['colorOpen'],
        self.formatStrings['nextMarkOfGun'], self.formatStrings['colorClose'])
        self.formatStrings['damageCurrent'] = config.data['battleMessage{damageCurrent}'] % EDn
        self.formatStrings['damageNextPercent'] = config.data['battleMessage{damageNextPercent}'] % damage if damage < 30000 or self.replay else config.i18n['NaN']
        self.formatStrings['c_damageCurrent'] = '%s%s%s' % ('<font color="%s">' % colorNowDamage if not unknown else self.formatStrings['colorOpen'],
        self.formatStrings['damageCurrent'], self.formatStrings['colorClose'])
        self.formatStrings['c_damageCurrentPercent'] = '%s%s%s' % (self.formatStrings['colorOpen'], self.formatStrings['damageCurrentPercent'], self.formatStrings['colorClose'])
        self.formatStrings['c_damageNextPercent'] = '%s%s%s' % ('<font color="%s">' % colorNextDamage if not unknown else self.formatStrings['colorOpen'],
        self.formatStrings['damageNextPercent'], self.formatStrings['colorClose'])
        self.formatStrings['assistCurrent'] = self.formatStrings[assistCurrent] if max(assists) else self.formatStrings['assistTrack']

    @staticmethod
    def isAvailable():
        vehicle = BigWorld.player().getVehicleAttached()
        return None if vehicle is None else vehicle.id == BigWorld.player().playerVehicleID

    def onVehicleKilled(self, target_id, *_, **__):
        if target_id == BigWorld.player().playerVehicleID:
            self.killed = True
            self.calc()

    def startBattle(self):
        if not config.data['enabled']:
            return
        self.startCount = 0
        BigWorld.callback(1.0, self.treadStartBattle)

    def treadStartBattle(self):
        vehicle = BigWorld.player().getVehicleAttached()
        if not vehicle:
            self.startCount += 1
            if self.startCount < 10:
                return BigWorld.callback(1.0, self.treadStartBattle)
            else:
                return
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
        if self.level and self.movingAvgDamage:
            BigWorld.player().arena.onVehicleKilled += self.onVehicleKilled
            self.formatStrings['currentMarkOfGun'] = config.data['battleMessage{currentMarkOfGun}'] % self.damageRating
            self.formatStrings['c_currentMarkOfGun'] = '%s%s%s' % (self.formatStrings['colorOpen'], self.formatStrings['currentMarkOfGun'], self.formatStrings['colorClose'])
            if self.name in config.values[dBid]:
                self.requestCurData(self.damageRating, self.movingAvgDamage)
            else:
                self.requestNewData(self.damageRating, self.movingAvgDamage)
            self.calcBattlePercents()
            self.calc()

    def endBattle(self):
        if not config.data['enabled']:
            return
        if self.level and self.movingAvgDamage:
            BigWorld.player().arena.onVehicleKilled -= self.onVehicleKilled

    @staticmethod
    def check_player_thread():
        player = BigWorld.player()
        return '%s' % player.databaseID if hasattr(player, 'databaseID') else '%s' % player.arena.vehicles[
            player.playerVehicleID]['accountDBID']

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


config = ConfigInterface()
worker = Worker()
analytics = Analytics(config.ID, config.version)


@override(CrewWidget, '_CrewWidget__updateWidgetModel')
@logException
def new__updateWidgetModel(func, *args):
    worker.getCurrentHangarData()
    return func(*args)


@override(PlayerAvatar, 'onBattleEvents')
@logException
def new__onBattleEvents(func, *args):
    func(*args)
    if BigWorld.player().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        worker.onBattleEvents(args[1])


@override(Vehicle, 'onHealthChanged')
@logException
def new__OnHealthChanged(func, self, newHealth, oldHealth, attackerID, *args, **kwargs):
    worker.shots(self, newHealth, oldHealth, attackerID)
    func(self, newHealth, oldHealth, attackerID, *args, **kwargs)


@override(Vehicle, 'startVisual')
@logException
def new__StartVisual(func, *args):
    func(*args)
    worker.initVehicle(args[0])


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
@logException
def new__startGUI(func, *args):
    func(*args)
    if BigWorld.player().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        worker.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
@logException
def new__destroyGUI(func, *args):
    try:
        if BigWorld.player().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
            worker.endBattle()
            worker.clearData()
    except StandardError:
        pass
    func(*args)


@override(MarkOnGunAchievement, 'getUserCondition')
@logException
def new__getUserCondition(func, *args):
    if config.data['enabled'] and config.data['showInStatistic']:
        if worker.dossier is not None:
            targetData = worker.dossier
            damage = ProfileUtils.getValueOrUnavailable(ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamage()))
            track = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedTrack))
            radio = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedRadio))
            stun = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamageAssistedStun())
            currentDamage = int(damage + max(track, radio, stun))
            damageRating = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
            movingAvgDamage = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
            if damageRating:
                pC, dC, p20, p40, p55, p65, p85, p95, p100 = worker.calcStatistics(damageRating, movingAvgDamage)
                color = ['#F8F400', '#F8F400', '#60FF00', '#02C9B3', '#D042F3', '#D042F3']
                levels = [p55, p65, p85, p95, p100, 10000000]
                data = {
                    'nextPercent': '%.0f' % pC,
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
@logException
def new__init(func, *args):
    func(*args)
    worker.dossier = args[1]


def htmlHangarBuilder():
    self = BigWorld.MoEHangarHTML
    if self.flashObject:
        self.flashObject.vehicleStatus.vehicleName.width = 250
        self.flashObject.vehicleStatus.vehicleName.htmlText = '<TEXTFORMAT INDENT="0" LEFTMARGIN="0" RIGHTMARGIN="0" LEADING="1"><P ALIGN="RIGHT"><FONT FACE="$FieldFont" SIZE="16" COLOR="#FEFEEC" KERNING="0">%s</FONT></P></TEXTFORMAT>' % self.moeStart


# @override(AmmunitionPanel, 'as_updateVehicleStatusS')
# def new__updateVehicleStatusS(func, self, data):
# Need Test
@override(AmmunitionPanel, 'update')
def __update(func, self, *args):
    # result = func(self, data)
    result = func(self, *args)
    vehicle = g_currentVehicle.item
    targetData = g_currentVehicle.getDossier()
    damageRating = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
    moeStart = ''
    moeEnd = ''
    if damageRating:
        damage = ProfileUtils.getValueOrUnavailable(ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamage()))
        track = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedTrack))
        radio = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedRadio))
        stun = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamageAssistedStun())
        currentDamage = int(damage + max(track, radio, stun))
        movingAvgDamage = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
        pC, dC, p20, p40, p55, p65, p85, p95, p100 = worker.calcStatistics(damageRating, movingAvgDamage)
        color = ['#F8F400', '#F8F400', '#60FF00', '#02C9B3', '#D042F3', '#D042F3']
        levels = [p55, p65, p85, p95, p100, 10000000]
        currentDamaged = '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= currentDamage, levels)[0])], currentDamage)
        currentMovingAvgDamage = '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= movingAvgDamage, levels)[0])], movingAvgDamage)
        data = {
            'currentPercent': '%s%%' % damageRating,
            'currentMovingAvgDamage': currentMovingAvgDamage,
            'currentDamage': currentDamaged if currentDamage > movingAvgDamage else currentMovingAvgDamage,
            'nextPercent': '<font color="%s">%s%%</font>' % (config.battleDamageRating[config.levels.index(filter(lambda x: x >= pC, config.levels)[0])], pC),
            'needDamage': '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= int(dC), levels)[0])], int(dC)),
            'c_damageToMark20': '<font color="%s"><b>20%%:%s</b></font>' % (config.ratings['very_bad'], worker.getNormalizeDigits(p20)),
            'c_damageToMark40': '<font color="%s"><b>40%%:%s</b></font>' % (config.ratings['bad'], worker.getNormalizeDigits(p40)),
            'c_damageToMark55': '<font color="%s"><b>55%%:%s</b></font>' % (config.ratings['normal'], worker.getNormalizeDigits(p55)),
            'c_damageToMark65': '<font color="%s"><b>65%%:%s</b></font>' % (config.ratings['good'], worker.getNormalizeDigits(p65)),
            'c_damageToMark85': '<font color="%s"><b>85%%:%s</b></font>' % (config.ratings['very_good'], worker.getNormalizeDigits(p85)),
            'c_damageToMark95': '<font color="%s"><b>95%%:%s</b></font>' % (config.ratings['unique'], worker.getNormalizeDigits(p95)),
            'c_damageToMark100': '<font color="%s"><b>100%%:%s</b></font>' % (config.ratings['unique'], worker.getNormalizeDigits(p100))
        }
        moeStart = text_styles.promoSubTitle(config.i18n['UI_HangarStatsStart'].format(**data))
        moeEnd = text_styles.stats(config.i18n['UI_HangarStatsEnd'].format(**data))
    oldData = '<b>%s     %s</b>' % (text_styles.promoSubTitle(vehicle.shortUserName), moeStart)
    self.as_updateVehicleStatusS(oldData)
    # self.moeStart = oldData
    self.moeEnd = moeEnd
    BigWorld.MoEHangarHTML = self
    BigWorld.callback(0.1, htmlHangarBuilder)
    return result
