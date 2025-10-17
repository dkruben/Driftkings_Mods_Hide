# -*- coding: utf-8 -*-
from collections import defaultdict
from functools import partial
from random import choice

import ResMgr
from PlayerEvents import g_playerEvents
from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.battle.shared.indicators import SixthSenseIndicator
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
from gui.shared.personality import ServicesLocator
from SoundGroups import g_instance

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, callback, getPlayer, square_position, sendChatMessage, calculate_version
from DriftkingsInject import DriftkingsInjector, SixthSenseMeta, g_events

AS_INJECTOR = 'SixthSenseInjector'
AS_BATTLE = 'SixthSenseView'
AS_SWF = 'SixthSenseIcon.swf'

_STATES_TO_HIDE = {
    VEHICLE_VIEW_STATE.SWITCHING, VEHICLE_VIEW_STATE.RESPAWNING,
    VEHICLE_VIEW_STATE.DESTROYED, VEHICLE_VIEW_STATE.CREW_DEACTIVATED
}

MESSAGES = (
    'Detected: <font color=\'#daff8f\'>{}</font> sec.',
    'Hide: <font color=\'#daff8f\'>{}</font> sec.',
    'Run: <font color=\'#daff8f\'>{}</font> sec.',
    'Alert: <font color=\'#ff7f7f\'>{}</font> sec.',
    'Danger: <font color=\'#ff5555\'>{}</font> sec.'
)


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.version = '1.6.5 (%(file_compile_date)s)'
        self.data = {
            'enabled': True,
            'defaultIcon': True,
            'userIcon': 'mods/configs/Driftkings/' + self.ID + '/SixthSenseIcon.png',
            'lampShowTime': 10,
            'playTickSound': False,
            'userSound': True,
            'defaultIconName': 0,
            'sixthSenseSound': 'SixthSense_06',
            'showTimer': True,
            'showTimerGraphics': True,
            'showTimerGraphicsColor': 'FFFFFF',
            'showTimerGraphicsRadius': 45,
            'iconSize': 90,
            'spottedMessage': True,
            'helpMessage': False,
            'spottedText': 'I\'m Spotted at %(pos)s!',
            'delay': 4,
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_defaultIcon_text': 'Default Icon',
            'UI_setting_defaultIcon_tooltip': 'Use embedded image.',
            'UI_setting_lampShowTime_text': 'Lamp Show Time',
            'UI_setting_lampShowTime_tooltip': '<b>How long does the target remain visible?</b><br>After being spotted, the tank remains visible even " "without direct line of sight. Standard — ~10 seconds, may vary from 7 to 13 depending on crew, " "equipment, and directives.',
            'UI_setting_playTickSound_text': 'Play Tick Sound',
            'UI_setting_playTickSound_tooltip': 'Play tick sound.',
            'UI_setting_defaultIconName_text': 'Default Icon Name',
            'UI_setting_defaultIconName_tooltip': 'Select an embedded image.',
            'UI_setting_userSound_text': 'User Sound',
            'UI_setting_userSound_tooltip': 'Enable custom sound when spotted.',
            'UI_setting_infoSpottedMessage_text': 'Spotted Messages:',
            'UI_setting_timerSettings_text': 'Timer Settings:',
            'UI_setting_spottedMessage_text': 'Spotted',
            'UI_setting_spottedMessage_tooltip': 'Enable spotted text in battle.',
            'UI_setting_spottedText_text': 'Text Format',
            'UI_setting_spottedText_tooltip': 'Use macros to edit the message\n(macro:\'%(pos)s\').',
            'UI_setting_helpMessage_text': 'Help Message',
            'UI_setting_helpMessage_tooltip': 'Send for chat (Help me) message automatically.',
            'UI_setting_delay_text': 'Delay',
            'UI_setting_delay_tooltip': 'Text message remains on screen for this amount of seconds before fading out.',
            'UI_setting_showTimer_text': 'Show Timer',
            'UI_setting_showTimer_tooltip': 'Show countdown timer when spotted.',
            'UI_setting_showTimerGraphics_text': 'Show Timer Graphics.',
            'UI_setting_showTimerGraphics_tooltip': 'Show graphical timer circle.',
            'UI_setting_showTimerGraphicsColor_text': 'Graphics color.',
            'UI_setting_showTimerGraphicsColor_tooltip': 'Color of the graphic circle.',
            'UI_setting_showTimerGraphicsRadius_text': 'Radius of the graphic circle.',
            'UI_setting_showTimerGraphicsRadius_tooltip': 'Size of the timer circle in pixels.',
            'UI_setting_iconSize_text': 'Image size',
            'UI_setting_iconSize_tooltip': 'In pixels (max 180)',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        infoSLabel = self.tb.createLabel('infoSpottedMessage')
        infoTimerLabel = self.tb.createLabel('timerSettings')

        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('defaultIcon'),
                self.tb.createImageOptions('defaultIconName', self.sixthSenseIconsNamesList()),
                self.tb.createControl('playTickSound'),
                self.tb.createSlider('lampShowTime', 2.0, 15.0, 1.0, '{{value}} sec'),
                self.tb.createSlider('iconSize', 50, 180, 10, '{{value}} px'),
                infoTimerLabel,
                self.tb.createControl('showTimer'),
                self.tb.createControl('showTimerGraphics'),
                self.tb.createControl('showTimerGraphicsColor', self.tb.types.ColorChoice),
                self.tb.createSlider('showTimerGraphicsRadius', 20, 100, 5, '{{value}} px'),
            ],
            'column2': [
                infoSLabel,
                self.tb.createControl('spottedMessage'),
                self.tb.createControl('helpMessage'),
                self.tb.createControl('spottedText', self.tb.types.TextInput, 300),
                self.tb.createSlider('delay', 1.0, 10.0, 1.0, '{{value}} sec'),
                self.tb.createControl('userSound')
            ]
        }

    @staticmethod
    def sixthSenseIconsNamesList():
        directory = 'gui/maps/icons/SixthSense/'
        folder = ResMgr.openSection(directory)
        if folder is not None:
            return sorted(folder.keys())
        return []

    def onBattleLoaded(self):
        if not self.data['enabled']:
            return
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


class MessagesSpotted(object):
    def __init__(self):
        self.macro = defaultdict(lambda: 'macros not found')
        self.__time = 0.5
        self.last_position = None

    def sendMessage(self):
        self.macro['pos'] = square_position.getSquarePosition()
        if self.macro['pos'] != self.last_position:
            message = config.data['spottedText'] % self.macro
            if message:
                sendChatMessage(message, 1, config.data['delay'])
                self.last_position = self.macro['pos']

    def helpMessage(self):
        def message(avatar):
            avatar.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.SOS)
        if config.data['helpMessage']:
            callback(self.__time, partial(message, getPlayer()))


g_messages = MessagesSpotted()


class SixthSense(SixthSenseMeta):
    def __init__(self):
        super(SixthSense, self).__init__(config.ID)
        self.radio_installed = False
        self.__sounds = dict()
        self.__visible = False
        self.__message = None
        self.__radar = None
        self.__soundID = None
        try:
            from constants import DIRECT_DETECTION_TYPE
            self.__radar = DIRECT_DETECTION_TYPE.STEALTH_RADAR
        except:
            pass

    def getSettings(self):
        return config.data

    def callWWISE(self, wwiseEventName):
        if wwiseEventName in self.__sounds:
            sound = self.__sounds[wwiseEventName]
        else:
            sound = g_instance.getSound2D(wwiseEventName)
            self.__sounds[wwiseEventName] = sound
        if sound is not None:
            if sound.isPlaying:
                sound.stop()
            sound.play()

    def _populate(self):
        super(SixthSense, self)._populate()
        if config.data['playTickSound']:
            self.__soundID = self._arenaVisitor.type.getCountdownTimerSound()
        g_playerEvents.onRoundFinished += self._onRoundFinished
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleStateUpdated += self._onVehicleStateUpdated
        optional_devices = self.sessionProvider.shared.optionalDevices
        if optional_devices is not None:
            optional_devices.onDescriptorDevicesChanged += self.onDevicesChanged

    def _dispose(self):
        if self.sessionProvider.isReplayPlaying and self._getPyReloading():
            self.as_hideS()
        for sound in self.__sounds.values():
            sound.stop()
        self.__sounds.clear()
        self.__soundID = None
        g_playerEvents.onRoundFinished -= self._onRoundFinished
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleStateUpdated -= self._onVehicleStateUpdated
        optional_devices = self.sessionProvider.shared.optionalDevices
        if optional_devices is not None:
            optional_devices.onDescriptorDevicesChanged -= self.onDevicesChanged
        super(SixthSense, self)._dispose()

    def onDevicesChanged(self, devices):
        self.radio_installed = 'improvedRadioCommunication' in (device.groupName for device in devices if device is not None)

    def getNewRandomMessage(self):
        message = choice(MESSAGES)
        if message == self.__message:
            message = self.getNewRandomMessage()
        return message

    def _onVehicleStateUpdated(self, state, value):
        if state == VEHICLE_VIEW_STATE.OBSERVED_BY_ENEMY:
            if value.get('isObserved', False):
                detection_type = value.get("detectionType", 0)
                self.__last_detection_type = detection_type
                if hasattr(self, 'isComp7Battle') and self.isComp7Battle:
                    if detection_type == self.__radar:
                        time = 2
                    else:
                        time = 4
                        if config.data['userSound'] and not config.data['playTickSound']:
                            g_instance.playSound2D(config.data['sixthSenseSound'])
                else:
                    time = config.data['lampShowTime']
                    if config.data['userSound'] and not config.data['playTickSound']:
                        g_instance.playSound2D(config.data['sixthSenseSound'])
                    if self.radio_installed:
                        time -= 1.5
                self.__message = self.getNewRandomMessage()
                self.as_showS(time)
            else:
                self.as_hideS()
        elif state in _STATES_TO_HIDE:
            self.as_hideS()

    def _onRoundFinished(self, *_):
        self.as_hideS()

    def getTimerString(self, timeLeft):
        return self.__message.format(timeLeft)

    def playSound(self):
        if self.__soundID is not None:
            self.callWWISE(self.__soundID)


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, SixthSense, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))


@override(SixthSenseIndicator, '_show')
def new__show(func, self):
    func(self)
    player = getPlayer()
    if player and player.isVehicleAlive:
        if config.data['enabled']:
            if config.data['spottedMessage']:
                g_messages.sendMessage()
            if config.data['helpMessage']:
                g_messages.helpMessage()


@override(SixthSenseIndicator, '_populate')
def new_populate(func, self):
    func(self)
    if config.data['enabled'] and (config.data['userIcon'] or config.data['defaultIcon'] is not None):
        self.flashObject.visible = False
