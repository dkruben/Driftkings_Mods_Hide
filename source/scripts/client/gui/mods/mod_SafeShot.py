# -*- coding: utf-8 -*-
from collections import defaultdict

import Keys
from Avatar import PlayerAvatar
from BigWorld import serverTime
from gui import InputHandler
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, getTarget, checkKeys, sendChatMessage, sendPanelMessage, calculate_version


class ConfigInterface(DriftkingsConfigInterface):
    WASTE_SHOT_BLOCKED_MSG = 'Waste shot blocked!'
    TEAM_SHOT_BLOCKED_MSG = 'Team shot blocked!'
    DEAD_SHOT_BLOCKED_MSG = 'Dead shot blocked!'

    def __init__(self):
        self.macro = defaultdict(lambda: 'Macros not found!')
        self.deadDict = {}
        self.isEventBattle = False
        # self._isKeyPressed = False
        super(ConfigInterface, self).__init__()
        #
        override(FragsCollectableStats, 'addVehicleStatusUpdate', self.new__addVehicleStatusUpdate)
        override(PlayerAvatar, 'shoot', self.new__shoot)
        override(PlayerAvatar, 'onBecomePlayer', self.new__onBecomePlayer)
        override(PlayerAvatar, '_PlayerAvatar__startGUI', self.new__startGUI)
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.new__destroyGUI)

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.7.0 (%(file_compile_date)s)'
        self.defaultKeys = {'disableKey': [Keys.KEY_Q]}
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
            'format': '[%(name)s - %(vehicle)s], get out of the way!',
            'disableKey': self.defaultKeys['disableKey'],
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
        InputHandler.g_instance.onKeyDown += self.keyPressed

    def stopBattle(self):
        InputHandler.g_instance.onKeyUp -= self.keyPressed

    def keyPressed(self, event):
        if not config.data['enabled']:
            return
        # self._isKeyPressed = True
        if checkKeys(self.data['disableKey']) and event.isKeyDown():
            self.data['disableMessage'] = not self.data['disableMessage']
            sendPanelMessage('SafeShot: is Enabled' if self.data['disableMessage'] else 'SafeShot: is Disabled', 'Green' if self.data['disableMessage'] else 'Red')

    def new__addVehicleStatusUpdate(self, func, b_self, vInfoVO):
        func(b_self, vInfoVO)
        if not vInfoVO.isAlive() and self.data['enabled'] and self.data['deadShotBlock']:
            self.deadDict[vInfoVO.vehicleID] = serverTime()

    def new__shoot(self, func, b_self, isRepeat=False):
        if not self.data['enabled'] and not self.data['disableMessage'] and not self.isEventBattle:
            return func(b_self, isRepeat)
        target = getTarget()
        if target is None:
            if self.data['wasteShotBlock']:
                waste_message = self.data['clientMessages']['wasteShotBlockedMessage']
                sendPanelMessage(text=waste_message, colour='Yellow')
                return
        elif hasattr(target.publicInfo, 'team'):
            player = getPlayer()
            if self.data['teamShotBlock'] and player.team == target.publicInfo.team and target.isAlive():
                if not self.data['teamKillerShotUnblock'] and not player.guiSessionProvider.getArenaDP().isTeamKiller(target.id):
                    self.macro['name'] = target.publicInfo.name
                    self.macro['vehicle'] = target.typeDescriptor.type.shortUserString
                    text = self.data['format'] % self.macro
                    sendChatMessage(fullMsg=text, chanId=1, delay=2)
                    team_message = self.data['clientMessages']['teamShotBlockedMessage']
                    sendPanelMessage(text=team_message, colour='Yellow')
                    return
            elif self.data['deadShotBlock'] and not target.isAlive():
                if self.data['deadShotBlockTimeOut'] == 0 or serverTime() - self.deadDict.get(target.id, 0) < self.data['deadShotBlockTimeOut']:
                    dead_message = self.data['clientMessages']['deadShotBlockedMessage']
                    sendPanelMessage(text=dead_message, colour='Yellow')
                    return

        return func(b_self, isRepeat)

    def new__onBecomePlayer(self, func, b_self):
        func(b_self)
        self.isEventBattle = getPlayer().guiSessionProvider.arenaVisitor.gui.isEventBattle()

    def new__startGUI(self, func, *args):
        func(*args)
        self.startBattle()

    def new__destroyGUI(self, func, *args):
        func(*args)
        self.stopBattle()
        self.deadDict = {}


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')
