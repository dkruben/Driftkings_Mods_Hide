# -*- coding: utf-8 -*-
from collections import defaultdict

import Keys
from Avatar import PlayerAvatar
from BigWorld import serverTime
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, getTarget, checkKeys, sendChatMessage, sendPanelMessage, calculate_version


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.macro = defaultdict(lambda: 'Macros not found!')
        self.deadDict = {}
        self.isEventBattle = False
        self._is_key_pressed = True
        self.target = getTarget()
        super(ConfigInterface, self).__init__()
        #
        override(FragsCollectableStats, 'addVehicleStatusUpdate', self.new__addVehicleStatusUpdate)
        override(PlayerAvatar, 'shoot', self.new__shoot)
        override(PlayerAvatar, 'onBecomePlayer', self.new__onBecomePlayer)
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.new__destroyGUI)

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.7.5 (%(file_compile_date)s)'
        self.defaultKeys = {'disableKey': [Keys.KEY_Q]}
        self.data = {
            'enabled': True,
            'wasteShotBlock': False,
            'teamShotBlock': True,
            'teamKillerShotUnblock': True,
            'deadShotBlock': True,
            'deadShotBlockTimeOut': 3,
            'clientMessages': {
                'wasteShotBlockedMessage':'Waste shot blocked!',
                'teamShotBlockedMessage': 'Team shot blocked!',
                'deadShotBlockedMessage': 'Dead shot blocked!'
            },
            'format': '[%(name)s - %(vehicle)s], get out of the way!',
            'disableKey': self.defaultKeys['disableKey'],
            'disableMessage': True
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_wasteShotBlock_text': 'Waste Shot Block',
            'UI_setting_wasteShotBlock_tooltip': 'Prevents shooting when no target is selected',
            'UI_setting_teamShotBlock_text': 'Team Shot Block',
            'UI_setting_teamShotBlock_tooltip': 'Prevents shooting at teammates',
            'UI_setting_teamKillerShotUnblock_text': 'Team Killer Shot Unblock',
            'UI_setting_teamKillerShotUnblock_tooltip': 'Allows shooting at team killers',
            'UI_setting_deadShotBlock_text': 'Dead Shot Block',
            'UI_setting_deadShotBlock_tooltip': 'Prevents shooting at already destroyed vehicles',
            'UI_setting_deadShotBlockTimeOut_text': 'Dead Shot Block TimeOut',
            'UI_setting_deadShotBlockTimeOut_tooltip': 'Time in seconds to block shots after vehicle destruction',
            'UI_setting_format_text': 'Format Message',
            'UI_setting_format_tooltip': 'Custom message format when blocking team shots. Use %(name)s and %(vehicle)s as placeholders',
            'UI_setting_disableKey_text': 'Disable Key',
            'UI_setting_disableKey_tooltip': 'Hotkey to temporarily enable/disable the mod',
            'UI_setting_disableMessage_text': 'Disable Message',
            'UI_setting_disableMessage_tooltip': 'Show/hide notification messages when shots are blocked'
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
                self.tb.createSlider('deadShotBlockTimeOut', 2, 10, 1, '{{value}}%s' % '.sec')
            ]
        }

    def onHotkeyPressed(self, event):
        if not hasattr(getPlayer(), 'arena') or not self.data['enabled'] or not checkKeys(self.data['disableKey'], event.key) or not event.isKeyDown():
            return
        self._is_key_pressed = not self._is_key_pressed
        if self._is_key_pressed:
            sendPanelMessage('SafeShot: is Enabled')
            self.data['disableMessage'] = True
        else:
            sendPanelMessage('SafeShot: is Disabled', 'Red')
            self.data['disableMessage'] = False

    def new__addVehicleStatusUpdate(self, func, orig, vInfoVO):
        func(orig, vInfoVO)
        if not vInfoVO.isAlive() and self.data['enabled'] and self.data['deadShotBlock']:
            self.deadDict[vInfoVO.vehicleID] = serverTime()

    def new__shoot(self, func, orig, isRepeat=False):
        if not self.data['enabled'] and not self.data['disableMessage'] and not self.isEventBattle:
            return func(orig, isRepeat)
        if self.target is None:
            if self.data['wasteShotBlock']:
                sendPanelMessage(self.data['clientMessages']['wasteShotBlockedMessage'], 'Yellow')
                return
        elif hasattr(self.target.publicInfo, 'team'):
            player = getPlayer()
            if self.data['teamShotBlock'] and player.team == self.target.publicInfo.team and self.target.isAlive():
                if not self.data['teamKillerShotUnblock'] and not player.guiSessionProvider.getArenaDP().isTeamKiller(self.target.id):
                    self.macro.update({
                        'name': self.target.publicInfo.name if self.target else '',
                        'vehicle': self.target.typeDescriptor.type.shortUserString if self.target else ''
                    })
                    sendChatMessage((self.data['format'] % self.macro), 1, 3)
                    sendPanelMessage(self.data['clientMessages']['teamShotBlockedMessage'], 'Yellow')
                    return
            elif self.data['deadShotBlock'] and not self.target.isAlive():
                if self.data['deadShotBlockTimeOut'] == 0 or serverTime() - self.deadDict.get(self.target.id, 0) < self.data['deadShotBlockTimeOut']:
                    sendPanelMessage(self.data['clientMessages']['deadShotBlockedMessage'], 'Yellow')
                    return
        return func(orig, isRepeat)

    def new__onBecomePlayer(self, func, orig):
        func(orig)
        self.isEventBattle = getPlayer().guiSessionProvider.arenaVisitor.gui.isEventBattle()

    def new__destroyGUI(self, func, *args):
        func(*args)
        self.deadDict = {}


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')
