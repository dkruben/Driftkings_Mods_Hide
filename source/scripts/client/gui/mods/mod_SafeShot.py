# -*- coding: utf-8 -*-
import Keys
from Avatar import PlayerAvatar
from BigWorld import serverTime
from gui import InputHandler
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from DriftkingsCore import SimpleConfigInterface, Analytics, override, getPlayer, getTarget, checkKeys, sendChatMessage, sendPanelMessage, logException, calculate_version, replaceMacros


class ConfigInterface(SimpleConfigInterface):
    # Mensagens padrão
    WASTE_SHOT_BLOCKED_MSG = 'Waste shot blocked!'
    TEAM_SHOT_BLOCKED_MSG = 'Team shot blocked!'
    DEAD_SHOT_BLOCKED_MSG = 'Dead shot blocked!'

    def __init__(self):
        self._disable_key = False
        self.is_hot_key_event = False
        self.deadDict = {}
        self.isEventBattle = False
        super(ConfigInterface, self).__init__()

        # Sobrescrevendo métodos
        override(FragsCollectableStats, 'addVehicleStatusUpdate', self.__addVehicleStatusUpdate)
        override(PlayerAvatar, 'shoot', self.__shoot)
        override(PlayerAvatar, 'onBecomePlayer', self.__onBecomePlayer)
        override(PlayerAvatar, '_PlayerAvatar__startGUI', self.__startGUI)
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.__destroyGUI)

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.6.5 (%(file_compile_date)s)'
        self.defaultKeys = {'disableKey': [Keys.KEY_Q]}
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'

        self.data = {
            'enabled': True,
            'wasteShotBlock': False,
            'teamShotBlock': True,
            'teamKillerShotUnblock': True,
            'deadShotBlock': True,
            'deadShotBlockTimeOut': 3,
            'clientMessages': {
                'wasteShotBlockedMessage': self.WASTE_SHOT_BLOCKED_MSG,
                'teamShotBlockedMessage': self.TEAM_SHOT_BLOCKED_MSG,
                'deadShotBlockedMessage': self.DEAD_SHOT_BLOCKED_MSG
            },
            'format': '[{name} - {vehicle}], get out of the way!',
            'disableKey': self.defaultKeys['disableKey'],
            'onHold': True,
            'disableMessage': True
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_wasteShotBlock_text': 'Waste Shot Block',
            'UI_setting_wasteShotBlock_tooltip': '',
            'UI_setting_teamShotBlock_text': 'Team Shot Block',
            'UI_setting_teamShotBlock_tooltip': '',
            'UI_setting_teamKillerShotUnblock_text': 'Team Killer Shot Unblock',
            'UI_setting_teamKillerShotUnblock_tooltip': '',
            'UI_setting_deadShotBlock_text': 'Dead Shot Block',
            'UI_setting_deadShotBlock_tooltip': '',
            'UI_setting_deadShotBlockTimeOut_text': 'Dead Shot Block TimeOut',
            'UI_setting_deadShotBlockTimeOut_tooltip': '',
            'UI_setting_format_text': 'Format Message',
            'UI_setting_format_tooltip': '',
            'UI_setting_disableKey_text': 'Disable Key',
            'UI_setting_disableKey_tooltip': '',
            'UI_setting_disableMessage_text': 'Disable Message',
            'UI_setting_disableMessage_tooltip': '',
        }

        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('wasteShotBlock'),
                self.tb.createControl('teamShotBlock'),
                self.tb.createControl('teamKillerShotUnblock'),
                self.tb.createControl('deadShotBlock'),
            ],
            'column2': [
                self.tb.createControl('disableMessage'),
                self.tb.createHotKey('disableKey'),
                self.tb.createControl('format', self.tb.types.TextInput, 350),
                self.tb.createSlider('deadShotBlockTimeOut', 2, 10, 1, '{{value}}%s' % ' .sec')
            ]
        }

    def startBattle(self):
        InputHandler.g_instance.onKeyDown += self.injectButton
        self.is_hot_key_event = self.data['onHold']

    def stopBattle(self):
        InputHandler.g_instance.onKeyUp -= self.injectButton
        self.is_hot_key_event = False

    @logException
    def injectButton(self, event):
        if not self.data['disableMessage']:
            return

        if checkKeys(self.data['disableKey']) and event.isKeyDown():
            self._disable_key = True
            self.is_hot_key_event = not self.is_hot_key_event
            status_message = 'SafeShot: is Disabled' if self.is_hot_key_event else 'SafeShot: is Enabled'
            color = 'Red' if self.is_hot_key_event else 'Green'
            sendPanelMessage(status_message, color)

    def __addVehicleStatusUpdate(self, func, b_self, vInfoVO):
        func(b_self, vInfoVO)
        if not vInfoVO.isAlive() and self.data['enabled'] and self.data['deadShotBlock']:
            self.deadDict[vInfoVO.vehicleID] = serverTime()

    def __shoot(self, func, b_self, isRepeat=False):
        if not (self.data['enabled'] and not self.is_hot_key_event and not self.isEventBattle):
            return func(b_self, isRepeat)

        target = getTarget()
        if target is None:
            if self.data['wasteShotBlock']:
                sendPanelMessage(text=self.data['clientMessages']['wasteShotBlockedMessage'], colour='Yellow')
                return
        elif hasattr(target.publicInfo, 'team'):
            player = getPlayer()
            if self.data['teamShotBlock'] and player.team == target.publicInfo.team and target.isAlive():
                if not (self.data['teamKillerShotUnblock'] and player.guiSessionProvider.getArenaDP().isTeamKiller(target.id)):
                    macros = {}
                    macros_data = {'{name}': target.publicInfo.name, '{vehicle}': target.typeDescriptor.type.shortUserString}
                    for key, value in macros_data.iteritems():
                        macros['{%s}' % key] = str(value)
                    text = replaceMacros(self.data['format'], macros)
                    sendChatMessage(fullMsg=text, chanId=1, delay=2)
                    sendPanelMessage(text=self.data['clientMessages']['teamShotBlockedMessage'], colour='Yellow')
                    return
            elif self.data['deadShotBlock'] and not target.isAlive():
                if self.data['deadShotBlockTimeOut'] == 0 or serverTime() - self.deadDict.get(target.id, 0) < self.data['deadShotBlockTimeOut']:
                    sendPanelMessage(text=self.data['clientMessages']['deadShotBlockedMessage'], colour='Yellow')
                    return

        return func(b_self, isRepeat)

    def __onBecomePlayer(self, func, b_self):
        func(b_self)
        self.isEventBattle = getPlayer().guiSessionProvider.arenaVisitor.gui.isEventBattle()

    def __startGUI(self, func, *args):
        func(*args)
        self.startBattle()

    def __destroyGUI(self, func, *args):
        func(*args)
        self.stopBattle()
        self.deadDict = {}


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')
