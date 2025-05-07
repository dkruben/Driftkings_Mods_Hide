# -*- coding: utf-8 -*-
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from gui.battle_control.controllers import feedback_events
from gui.battle_control.controllers.personal_efficiency_ctrl import _AGGREGATED_DAMAGE_EFFICIENCY_TYPES, _createEfficiencyInfoFromFeedbackEvent

from DriftkingsCore import DriftkingsConfigInterface, override, Analytics, sendPanelMessage, getPlayer, calculate_version

SOUND_LIST = ['soundSpotted', 'soundAssist']
GENERATOR = {
    BATTLE_EVENT_TYPE.SPOTTED: ['UI_setting_Spotted_text', 'messageColorSpotted', 'Spotted'],
    BATTLE_EVENT_TYPE.RADIO_ASSIST: ['UI_setting_AssistRadio_text', 'messageColorAssistRadio', 'AssistRadio'],
    BATTLE_EVENT_TYPE.TRACK_ASSIST: ['UI_setting_AssistTrack_text', 'messageColorAssistTrack', 'AssistTrack'],
    BATTLE_EVENT_TYPE.STUN_ASSIST: ['UI_setting_AssistStun_text', 'messageColorAssistStun', 'AssistStun']
}


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.format_str = {}
        self.format_recreate()
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.8.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (spoter mods)'
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
            'UI_version': calculate_version(self.version),
            'UI_setting_sound_text': 'Enable battle sounds',
            'UI_setting_sound_tooltip': 'Toggle sound notifications for spotted enemies and assist damage',
            'UI_setting_sound_default': 'Default: %s' % ('Enabled' if self.data['sound'] else 'Disabled'),
            'UI_setting_soundSpotted_text': 'Spotted notification sound',
            'UI_setting_soundSpotted_tooltip': 'Sound played when you spot an enemy vehicle',
            'UI_setting_soundSpotted_default': 'Default: %s' % self.data['soundSpotted'],
            'UI_setting_soundAssist_text': 'Assist notification sound',
            'UI_setting_soundAssist_tooltip': 'Sound played when you get assist damage (radio, track or stun)',
            'UI_setting_soundAssist_default': 'Default: %s' % self.data['soundAssist'],
            'UI_setting_iconSizeX_text': 'Icon width',
            'UI_setting_iconSizeX_value': ' px',
            'UI_setting_iconSizeX_tooltip': 'Width of vehicle icons in notifications',
            'UI_setting_iconSizeX_default': 'Default: %s px' % self.data['iconSizeX'],
            'UI_setting_iconSizeY_text': 'Icon height',
            'UI_setting_iconSizeY_value': ' px',
            'UI_setting_iconSizeY_tooltip': 'Height of vehicle icons in notifications',
            'UI_setting_iconSizeY_default': 'Default: %s px' % self.data['iconSizeY'],
            'UI_setting_messageColorSpottedCheck_text': 'Spotted message color',
            'UI_setting_messageColorSpotted_text': 'Current: <font color=\'#%(messageColorSpotted)s\'>■■■■</font>',
            'UI_setting_messageColorSpotted_tooltip': 'Color used for the "Spotted" notification text',
            'UI_setting_messageColorAssistRadioCheck_text': 'Radio assist message color',
            'UI_setting_messageColorAssistRadio_text': 'Current: <font color=\'#%(messageColorAssistRadio)s\'>■■■■</font>',
            'UI_setting_messageColorAssistRadio_tooltip': 'Color used for the "Radio Hit Assist" notification text',
            'UI_setting_messageColorAssistTrackCheck_text': 'Track assist message color',
            'UI_setting_messageColorAssistTrack_text': 'Current: <font color=\'#%(messageColorAssistTrack)s\'>■■■■</font>',
            'UI_setting_messageColorAssistTrack_tooltip': 'Color used for the "Track Hit Assist" notification text',
            'UI_setting_messageColorAssistStunCheck_text': 'Stun assist message color',
            'UI_setting_messageColorAssistStun_text': 'Current: <font color=\'#%(messageColorAssistStun)s\'>■■■■</font>',
            'UI_setting_messageColorAssistStun_tooltip': 'Color used for the "Stun Hit Assist" notification text',
            'UI_setting_Spotted_text': 'Spotted:',
            'UI_setting_Spotted_default': 'Default: %s' % self.data['Spotted'],
            'UI_setting_Spotted_description': 'Format of the message shown when you spot an enemy',
            'UI_setting_Spotted_tooltip': 'Customize the message shown when you spot an enemy vehicle',
            'UI_setting_AssistRadio_text': 'Radio assist:',
            'UI_setting_AssistRadio_default': 'Default: %s' % self.data['AssistRadio'],
            'UI_setting_AssistRadio_description': 'Format of the message shown for radio assist damage',
            'UI_setting_AssistRadio_tooltip': 'Customize the message shown when you get radio assist damage',
            'UI_setting_AssistTrack_text': 'Track assist:',
            'UI_setting_AssistTrack_default': 'Default: %s' % self.data['AssistTrack'],
            'UI_setting_AssistTrack_description': 'Format of the message shown for track assist damage',
            'UI_setting_AssistTrack_tooltip': 'Customize the message shown when you get track assist damage',
            'UI_setting_AssistStun_text': 'Stun assist:',
            'UI_setting_AssistStun_default': 'Default: %s' % self.data['AssistStun'],
            'UI_setting_AssistStun_description': 'Format of the message shown for stun assist damage',
            'UI_setting_AssistStun_tooltip': 'Customize the message shown when you get stun assist damage',
            'UI_setting_macrosList': 'Available macros: {icons} - vehicle icons, {names} - player names, {vehicles} - vehicle names, {icons_names} - icons with names, {icons_vehicles} - icons with vehicle names, {full} - complete information, {damage} - damage amount',
            'UI_macros_help_title': 'Macro Usage Guide',
            'UI_macros_help': 'Use these macros in your message formats to customize notifications:\n• {icons} - Shows vehicle icons\n• {names} - Shows player names\n• {vehicles} - Shows vehicle names\n• {icons_names} - Shows icons with player names\n• {icons_vehicles} - Shows icons with vehicle names\n• {full} - Shows complete information\n• {damage} - Shows damage amount (for assist messages only)'
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
        return any(macros in self.data[text_type] for text_type in ['Spotted', 'AssistRadio', 'AssistTrack', 'AssistStun'])

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

    def sound(self, assist_type):
        soundID = self.data[SOUND_LIST[assist_type]]
        getPlayer().soundNotifications.play(soundID)

    def textGenerator(self, event):
        textKey, colorKey, macrosKey = GENERATOR[event]
        formatted_text = self.data[macrosKey].format(**self.format_str)
        message = (self.i18n[textKey], formatted_text)
        color = self.data[colorKey]
        return message, color

    def postMessage(self, events):
        if not self.data['enabled']:
            return
        g_sessionProvider = getPlayer().guiSessionProvider
        self.format_recreate()
        for data in events:
            feedbackEvent = feedback_events.PlayerFeedbackEvent.fromDict(data)
            eventID = feedbackEvent.getBattleEventType()
            if eventID not in [BATTLE_EVENT_TYPE.SPOTTED, BATTLE_EVENT_TYPE.RADIO_ASSIST, BATTLE_EVENT_TYPE.TRACK_ASSIST, BATTLE_EVENT_TYPE.STUN_ASSIST]:
                continue
            vehicleID = feedbackEvent.getTargetID()
            vehicleInfo = g_sessionProvider.getArenaDP().getVehicleInfo(vehicleID)
            if not vehicleInfo:
                continue
            icon = '<img src=\'img://%s\' width=\'%s\' height=\'%s\' />' % (vehicleInfo.vehicleType.iconPath.replace('..', 'gui'), self.data['iconSizeX'], self.data['iconSizeY'])
            targetInfo = g_sessionProvider.getCtx().getPlayerFullNameParts(vID=vehicleID)
            if self.check_macros('{icons}'):
                self.format_str['icons'] += icon
            if self.check_macros('{names}'):
                self.format_str['names'] += '[<b>%s</b>]' % targetInfo.playerName if targetInfo.playerName else icon
            if self.check_macros('{vehicles}'):
                self.format_str['vehicles'] += '[<b>%s</b>]' % targetInfo.vehicleName if targetInfo.vehicleName else icon
            if self.check_macros('{icons_names}'):
                self.format_str['icons_names'] += '%s[<b>%s</b>]' % (icon, targetInfo.playerName) if targetInfo.playerName else icon
            if self.check_macros('{icons_vehicles}'):
                self.format_str['icons_vehicles'] += '%s[<b>%s</b>]' % (icon, targetInfo.vehicleName) if targetInfo.vehicleName else icon
            if self.check_macros('{full}'):
                self.format_str['full'] += '%s[<b>%s</b>]' % (icon, targetInfo) if targetInfo else icon
            if self.check_macros('{damage}'):
                extra = _createEfficiencyInfoFromFeedbackEvent(feedbackEvent)
                if extra and extra.getType() in _AGGREGATED_DAMAGE_EFFICIENCY_TYPES:
                    damage = extra.getDamage()
                    if damage:
                        self.format_str['damage'] += '<b> +%s</b>' % damage
            if self.data['sound']:
                self.sound(0 if eventID == BATTLE_EVENT_TYPE.SPOTTED else 1)
            message, color = self.textGenerator(eventID)
            sendPanelMessage(text="<font color='#%s'>%s</font>" % (color, message))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


@override(PlayerAvatar, 'onBattleEvents')
def new__onBattleEvents(func, *args):
    func(*args)
    config.postMessage(args[1])
