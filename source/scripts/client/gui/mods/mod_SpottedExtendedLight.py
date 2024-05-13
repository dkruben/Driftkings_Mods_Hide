# -*- coding: utf-8 -*-
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from gui.battle_control.controllers import feedback_events
from gui.battle_control.controllers.personal_efficiency_ctrl import _AGGREGATED_DAMAGE_EFFICIENCY_TYPES, _createEfficiencyInfoFromFeedbackEvent

from DriftkingsCore import SimpleConfigInterface, override, Analytics, sendPanelMessage, getPlayer


SOUND_LIST = ['soundSpotted', 'soundAssist']
TEXT_LIST = ['Spotted', 'AssistRadio', 'AssistTrack', 'AssistStun']

GENERATOR = {
    BATTLE_EVENT_TYPE.SPOTTED: ['UI_setting_Spotted_text', 'messageColorSpotted', 'Spotted'],
    BATTLE_EVENT_TYPE.RADIO_ASSIST: ['UI_setting_AssistRadio_text', 'messageColorAssistRadio', 'AssistRadio'],
    BATTLE_EVENT_TYPE.TRACK_ASSIST: ['UI_setting_AssistTrack_text', 'messageColorAssistTrack', 'AssistTrack'],
    BATTLE_EVENT_TYPE.STUN_ASSIST: ['UI_setting_AssistStun_text', 'messageColorAssistStun', 'AssistStun']
}


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        self.format_str = {}
        self.format_recreate()
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.7.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (spoter mods)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'sound': True,
            'iconSizeX': 47,
            'iconSizeY': 16,
            'soundSpotted': 'enemy_sighted_for_team',
            'soundAssist': 'gun_intuition',
            'messageColorSpotted': 'FF69B5',
            'messageColorAssistRadio': '28F09C',
            'messageColorAssistTrack': '00FF00',
            'messageColorAssistStun': '00FFFF',
            'Spotted': '{icons}{vehicles}',
            'AssistRadio': '{icons}{vehicles}{damage}',
            'AssistTrack': '{icons}{vehicles}{damage}',
            'AssistStun': '{icons}{vehicles}{damage}',
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': sum(int(x) * (10 ** i) for i, x in enumerate(reversed(self.version.split(' ')[0].split('.')))),
            'UI_setting_sound_text': 'Use sound in battle',
            'UI_setting_sound_tooltip': '',
            'UI_setting_sound_default': 'Default: %s' % ('On' if self.data['sound'] else 'Off'),
            'UI_setting_soundSpotted_text': 'ID sound to Spotted',
            'UI_setting_soundSpotted_tooltip': '',
            'UI_setting_soundSpotted_default': 'Default: %s' % self.data['soundSpotted'],
            'UI_setting_soundAssist_text': 'ID sound to Assist',
            'UI_setting_soundAssist_tooltip': '',
            'UI_setting_soundAssist_default': 'Default: %s' % self.data['soundAssist'],
            'UI_setting_iconSizeX_text': 'Icon size X-coordinate',
            'UI_setting_iconSizeX_value': ' px.',
            'UI_setting_iconSizeX_tooltip': '',
            'UI_setting_iconSizeX_default': 'Default: %s' % self.data['iconSizeX'],
            'UI_setting_iconSizeY_text': 'Icon size Y-coordinate',
            'UI_setting_iconSizeY_value': ' px.',
            'UI_setting_iconSizeY_tooltip': '',
            'UI_setting_iconSizeY_default': 'Default: %s' % self.data['iconSizeY'],

            'UI_setting_messageColorSpottedCheck_text': 'Color to message "Spotted"',
            'UI_setting_messageColorSpotted_text': 'Default: <font color=\'#%(messageColorSpotted)s\'></font>',
            'UI_setting_messageColorSpotted_tooltip': '',

            'UI_setting_messageColorAssistRadioCheck_text': 'Color to message "Radio Hit Assist"',
            'UI_setting_messageColorAssistRadio_text': 'Default: <font color=\'#%(messageColorAssistRadio)s\'></font>',
            'UI_setting_messageColorAssistRadio_tooltip': '',

            'UI_setting_messageColorAssistTrackCheck_text': 'Color to message "Track Hit Assist"',
            'UI_setting_messageColorAssistTrack_text': 'Default: <font color=\'#%(messageColorAssistTrack)s\'></font>',
            'UI_setting_messageColorAssistTrack_tooltip': '',

            'UI_setting_messageColorAssistStunCheck_text': 'Color to message "Stun Hit Assist"',
            'UI_setting_messageColorAssistStun_text': 'Default: <font color=\'#%(messageColorAssistStun)s\'></font>',
            'UI_setting_messageColorAssistStun_tooltip': '',

            'UI_setting_Spotted_text': 'Spotted:',
            'UI_setting_Spotted_default': 'Default: %s' % self.data['Spotted'],
            'UI_setting_Spotted_description': 'Macros: Spotted',
            'UI_setting_AssistRadio_text': 'Assist Radio:',
            'UI_setting_AssistRadio_default': 'Default: %s' % self.data['AssistRadio'],
            'UI_setting_AssistRadio_description': 'Macros: Assist Radio',
            'UI_setting_AssistTrack_text': 'Assist Track:',
            'UI_setting_AssistTrack_default': 'Default: %s' % self.data['AssistTrack'],
            'UI_setting_AssistTrack_description': 'Macros: Assist Track',
            'UI_setting_AssistStun_text': 'Assist Stun:',
            'UI_setting_AssistStun_default': 'Default: %s' % self.data['AssistStun'],
            'UI_setting_AssistStun_description': 'Macros: Assist Stun',
            'UI_setting_macrosList': 'Available macros in messages {icons}, {names}, {vehicles}, {icons_names}, {icons_vehicles}, {full}, {damage}'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        xColorSpotted = self.tb.createControl('messageColorSpotted', self.tb.types.ColorChoice)
        xColorSpotted['text'] = self.tb.getLabel('messageColorSpottedCheck')
        xColorSpotted['tooltip'] %= {'messageColorSpotted': self.data['messageColorSpotted']}

        xColorAssistRadio = self.tb.createControl('messageColorAssistRadio', self.tb.types.ColorChoice)
        xColorAssistRadio['text'] = self.tb.getLabel('messageColorAssistRadioCheck')
        xColorAssistRadio['tooltip'] %= {'messageColorAssistRadio': self.data['messageColorAssistRadio']}

        xColorAssistTrack = self.tb.createControl('messageColorAssistTrack', self.tb.types.ColorChoice)
        xColorAssistTrack['text'] = self.tb.getLabel('messageColorAssistTrackCheck')
        xColorAssistTrack['tooltip'] %= {'messageColorAssistTrack': self.data['messageColorAssistTrack']}

        xColorAssistStun = self.tb.createControl('messageColorAssistStun', self.tb.types.ColorChoice)
        xColorAssistStun['text'] = self.tb.getLabel('messageColorAssistStunCheck')
        xColorAssistStun['tooltip'] %= {'messageColorAssistStun': self.data['messageColorAssistStun']}
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('sound'),
                self.tb.createSlider('iconSizeX', 5.0, 150.0, 1.0, '{{value}}%s' % self.i18n['UI_setting_iconSizeX_value']),
                self.tb.createSlider('iconSizeY', 5.0, 150.0, 1.0, '{{value}}%s' % self.i18n['UI_setting_iconSizeY_value'])
            ],
            'column2': [
                xColorSpotted,
                self.tb.createControl('Spotted', self.tb.types.TextInput, 300),
                xColorAssistRadio,
                self.tb.createControl('AssistRadio', self.tb.types.TextInput, 300),
                xColorAssistTrack,
                self.tb.createControl('AssistTrack', self.tb.types.TextInput, 300),
                xColorAssistStun,
                self.tb.createControl('AssistStun', self.tb.types.TextInput, 300)
            ]}

    def check_macros(self, macros):
        for i in TEXT_LIST:
            if macros in self.data[i]:
                return True

    def format_recreate(self):
        self.format_str = {
            'icons': '',
            'names': '',
            'vehicles': '',
            'icons_names': '',
            'icons_vehicles': '',
            'full': '',
            'damage': ''
        }

    @staticmethod
    def sound(assist_type):
        getPlayer().soundNotifications.play(config.data[SOUND_LIST[assist_type]])

    def textGenerator(self, event):
        text, color, macros = GENERATOR[event]
        return (config.i18n[text], config.data[macros].format(**self.format_str)), config.data[color]

    def postMessage(self, events):
        if not config.data['enabled']:
            return
        g_sessionProvider = getPlayer().guiSessionProvider
        self.format_recreate()
        for data in events:
            feedbackEvent = feedback_events.PlayerFeedbackEvent.fromDict(data)
            eventID = feedbackEvent.getBattleEventType()
            if eventID in [BATTLE_EVENT_TYPE.SPOTTED, BATTLE_EVENT_TYPE.RADIO_ASSIST, BATTLE_EVENT_TYPE.TRACK_ASSIST, BATTLE_EVENT_TYPE.STUN_ASSIST]:
                vehicleID = feedbackEvent.getTargetID()
                icon = '<img src=\'img://%s\' width=\'%s\' height=\'%s\' />' % (g_sessionProvider.getArenaDP().getVehicleInfo(vehicleID).vehicleType.iconPath.replace('..', 'gui'), config.data['iconSizeX'], config.data['iconSizeY'])
                target_info = g_sessionProvider.getCtx().getPlayerFullNameParts(vID=vehicleID)
                if self.check_macros('{icons}'):
                    self.format_str['icons'] += icon
                if self.check_macros('{names}'):
                    self.format_str['names'] += '[<b>%s</b>]' % target_info.playerName if target_info.playerName else icon
                if self.check_macros('{vehicles}'):
                    self.format_str['vehicles'] += '[<b>%s</b>]' % target_info.vehicleName if target_info.vehicleName else icon
                if self.check_macros('{icons_names}'):
                    self.format_str['icons_names'] += '%s[<b>%s</b>]' % (icon, target_info.playerName) if target_info.playerName else icon
                if self.check_macros('{icons_vehicles}'):
                    self.format_str['icons_vehicles'] += '%s[<b>%s</b>]' % (icon, target_info.vehicleName) if target_info.vehicleName else icon
                if self.check_macros('{damage}'):
                    extra = _createEfficiencyInfoFromFeedbackEvent(feedbackEvent)
                    if extra and extra.getType() in _AGGREGATED_DAMAGE_EFFICIENCY_TYPES:
                        self.format_str['damage'] += '<b> +%s</b>' % extra.getDamage()
                if self.check_macros('{full}'):
                    self.format_str['full'] += '%s[<b>%s</b>]' % (icon, target_info) if target_info else icon
                if eventID == BATTLE_EVENT_TYPE.SPOTTED:
                    if config.data['sound']:
                        self.sound(0)
                else:
                    if config.data['sound']:
                        self.sound(1)
                text, color = self.textGenerator(eventID)
                sendPanelMessage(text='<font color=\'#{}\'>{}</font>'.format(color, text))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(PlayerAvatar, 'onBattleEvents')
def new_onBattleEvents(func, *args):
    func(*args)
    config.postMessage(args[1])
