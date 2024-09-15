# -*- coding: utf-8 -*-
import math
from collections import defaultdict
from functools import partial
from random import choice

import BigWorld
import Math
import ResMgr
import SoundGroups
from PlayerEvents import g_playerEvents
from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.battle.shared.indicators import SixthSenseIndicator
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
from gui.shared.personality import ServicesLocator

from DriftkingsCore import SimpleConfigInterface, Analytics, override, callback, getPlayer, sendChatMessage, checkNamesList, calculate_version
from DriftkingsInject import DriftkingsInjector, SixthSenseMeta, SixthSenseTimer, g_events

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
    'Run: <font color=\'#daff8f\'>{}</font> sec.'
)


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.version = '1.3.5 (%(file_compile_date)s)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'defaultIcon': True,
            'lampShowTime': 1,
            'playTickSound': False,
            'userSound': True,
            'spottedMessage': True,
            'helpMessage': False,
            'defaultIconName': checkNamesList('gui/maps/icons/SixthSense/'),
            'userIcon': 'mods/configs/Driftkings/' + self.ID + '/SixthSenseIcon.png',
            'spottedText': 'I\'m Spotted at %(pos)s!',
            'delay': 4,
            'sixthSenseSound': 'SixthSense_06',
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_defaultIcon_text': 'Default Icon',
            'UI_setting_defaultIcon_tooltip': 'Use embedded image.',
            'UI_setting_lampShowTime_text': 'Lamp Show Time',
            'UI_setting_lampShowTime_tooltip': 'Choose value to hide icon (default 2 sec.)',
            'UI_setting_playTickSound_text': 'Play Tick Sound',
            'UI_setting_playTickSound_tooltip': 'Play tick sound.',
            'UI_setting_defaultIconName_text': 'Default Icon Name',
            'UI_setting_defaultIconName_tooltip': 'Select an embedded image.',
            'UI_setting_userSound_text': 'User Sound',
            'UI_setting_userSound_tooltip': 'Enable spotted text in battle.',
            'UI_setting_infoSpottedMessage_text': 'Spotted Messages:',
            'UI_setting_spottedMessage_text': 'Spotted',
            'UI_setting_spottedMessage_tooltip': 'Enable spotted text in battle.',
            'UI_setting_spottedText_text': 'Text Format',
            'UI_setting_spottedText_tooltip': 'Use macros to edit the message\n(macro:\'%(pos)s\').',
            'UI_setting_helpMessage_text': 'Help Message',
            'UI_setting_helpMessage_tooltip': 'Send for chat (Help me) message automatically.',
            'UI_setting_delay_text': 'Delay',
            'UI_setting_delay_tooltip': 'Text message remains on screen for this amount of seconds before fading out.',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        infoSLabel = self.tb.createLabel('infoSpottedMessage')
        infoSLabel['text'] += ''
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('defaultIcon'),
                self.tb.createImageOptions('defaultIconName', self.sixthSenseIconsNamesList()),
                self.tb.createControl('playTickSound'),
                self.tb.createSlider('lampShowTime', 2.0, 15.0, 1.0, '{{value}} ' + ' .sec'),

            ],
            'column2': [
                infoSLabel,
                self.tb.createControl('spottedMessage'),
                self.tb.createControl('helpMessage'),
                self.tb.createControl('spottedText', self.tb.types.TextInput, 300),
                self.tb.createSlider('delay', 1.0, 10.0, 1.0, '{{value}} ' + ' sec.')
            ]
        }

    @staticmethod
    def sixthSenseIconsNamesList():
        directory = 'gui/maps/icons/SixthSense/'
        folder = ResMgr.openSection(directory)
        return sorted(folder.keys())

    @staticmethod
    def onBattleLoaded():
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class Messages(object):
    def __init__(self):
        self.macro = defaultdict(lambda: 'macros not found')
        self.__time = 0.5

    @staticmethod
    def getSquarePosition():
        def clamp(val, vMax):
            vMin = 0.1
            return vMin if (val < vMin) else vMax if (val > vMax) else val

        def pos2name(pos):
            sqrsName = 'KJHGFEDCBA'
            linesName = '1234567890'
            return '{}{}'.format(sqrsName[int(pos[1]) - 1], linesName[int(pos[0]) - 1])

        player = getPlayer()
        boundingBox = player.arena.arenaType.boundingBox
        position = BigWorld.entities[player.playerVehicleID].position

        positionRect = Math.Vector2(position[0], position[2])
        bottomLeft, upperRight = boundingBox
        spaceSize = upperRight - bottomLeft
        relPos = positionRect - bottomLeft
        relPos[0] = clamp(relPos[0], spaceSize[0])
        relPos[1] = clamp(relPos[1], spaceSize[1])

        return pos2name((math.ceil(relPos[0] / spaceSize[0] * 10), math.ceil(relPos[1] / spaceSize[1] * 10)))

    def sendMessage(self):
        self.macro['pos'] = self.getSquarePosition()
        message = config.data['spottedText'] % self.macro
        if message:
            sendChatMessage(message, 1, config.data['delay'])

    def helpMessage(self):
        def message(avatar):
            avatar.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.SOS)

        if config.data['helpMessage']:
            callback(self.__time, partial(message, getPlayer()))


g_messages = Messages()


class SixthSense(SixthSenseMeta, SixthSenseTimer):

    def __init__(self):
        super(SixthSense, self).__init__(config.ID)
        self.radio_installed = False
        self.__visible = False
        self.__message = None

    def getSettings(self):
        return config.data

    def _populate(self):
        super(SixthSense, self)._populate()
        if config.data['playTickSound']:
            self.setSound(self._arenaVisitor.type.getCountdownTimerSound())
        g_playerEvents.onRoundFinished += self._onRoundFinished
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleStateUpdated += self._onVehicleStateUpdated
        optional_devices = self.sessionProvider.shared.optionalDevices
        if optional_devices is not None:
            optional_devices.onDescriptorDevicesChanged += self.onDevicesChanged

    def _dispose(self):
        self.destroyTimer()
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
        if state == VEHICLE_VIEW_STATE.OBSERVED_BY_ENEMY and value:
            time = config.data['lampShowTime']
            soundID = config.data['sixthSenseSound']
            if config.data['userSound'] and not config.data['playTickSound']:
                SoundGroups.g_instance.playSound2D(soundID)
            if self.radio_installed:
                time -= 2
            self.__message = self.getNewRandomMessage()
            self.show(time)
        elif state in _STATES_TO_HIDE:
            self.hide()

    def _onRoundFinished(self, *_):
        self.hide()

    def handleTimer(self, timeLeft):
        self.as_updateTimerS(self.__message.format(timeLeft))
        if timeLeft == 0:
            self.hide()

    def show(self, seconds):
        if not self.__visible:
            self.as_showS()
            self.__visible = True
        self.timeTicking(seconds)

    def hide(self):
        if self.__visible:
            self.cancelCallback()
            self.as_hideS()
            self.__visible = False


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, SixthSense, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))


@override(SixthSenseIndicator, '_SixthSenseIndicator__show')
def new__show(func, self):
    func(self)
    if getPlayer().isVehicleAlive:
        if config.data['enabled'] and config.data['spottedMessage']:
            g_messages.sendMessage()
        if config.data['enabled'] and config.data['helpMessage']:
            g_messages.helpMessage()


@override(SixthSenseIndicator, '_populate')
def new_populate(func, self):
    func(self)
    if config.data['enabled'] and config.data['userIcon'] or config.data['defaultIcon'] is not None:
        self.flashObject.visible = False
