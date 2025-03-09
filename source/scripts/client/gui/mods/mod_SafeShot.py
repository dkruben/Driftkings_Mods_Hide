# -*- coding: utf-8 -*-
import Keys
from Avatar import PlayerAvatar
from gui import InputHandler
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from messenger import MessengerEntry

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, getTarget, callback, serverTime, checkKeys, calculate_version, sendPanelMessage, sendChatMessage


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.isEventBattle = False
        self.deadDict = {}
        self.is_key_pressed = True
        # overrides methods
        override(FragsCollectableStats, 'addVehicleStatusUpdate', self.new__addVehicleStatusUpdate)
        override(PlayerAvatar, 'shoot', self.new__shoot)
        override(PlayerAvatar, 'shootDualGun', self.new__shootDualGun)
        override(PlayerAvatar, 'onBecomePlayer', self.new__onBecomePlayer)
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.new__destroyGUI)
        override(PlayerAvatar, '_PlayerAvatar__startGUI', self.new__startGUI)
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.8.0 (%(file_compile_date)s)'
        self.defaultKeys = {'disableKey': [Keys.KEY_Q]}
        self.data = {
            'enabled': True,
            'wasteShotBlock': False,
            'teamShotBlock': True,
            'teamKillerShotUnblock': False,
            'deadShotBlock': True,
            'deadShotBlockTimeOut': 2,
            'disableKey': self.defaultKeys['disableKey'],
            'activateMessage': True,
            'triggerMessage': True,
            'clientMessages': {
                'wasteShotBlockedMessage': 'Waste shot blocked!',
                'teamShotBlockedMessage': 'Team shot blocked!',
                'deadShotBlockedMessage': 'Dead shot blocked!'
            },
            'chatMessages': '[{name} - {vehicle}], get out of the way!'
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
            'UI_setting_chatMessages_text': 'Format Message',
            'UI_setting_chatMessages_tooltip': 'Custom message format when blocking team shots. Use %(name)s and %(vehicle)s as placeholders',
            'UI_setting_disableKey_text': 'Disable Key',
            'UI_setting_disableKey_tooltip': 'Hotkey to temporarily enable/disable the mod',
            'UI_setting_triggerMessage_text': 'Disable Message',
            'UI_setting_triggerMessage_tooltip': 'Show/hide notification messages when shots are blocked',
            'UI_setting_activateMessage_text': 'Activate Message',
            'UI_setting_activateMessage_tooltip': 'Show notification message when entering battle',
            'UI_battle_activateMessage': 'Mod: SafeShot Activated!',
            'UI_triggerText_enabled': 'SafeShot: Enabled!',
            'UI_triggerText_disabled': 'SafeShot: Disabled!'
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
                self.tb.createControl('activateMessage')
            ],
            'column2': [
                self.tb.createControl('triggerMessage'),
                self.tb.createHotKey('disableKey'),
                self.tb.createControl('chatMessages', self.tb.types.TextInput, 350),
                self.tb.createSlider('deadShotBlockTimeOut', 2, 10, 1, '{{value}}%s' % '.sec')
            ]
        }

    def isShotAllowed(self):
        if not (self.data['enabled'] and not self.isEventBattle):
            return True
        if getTarget() is None:
            if self.data['wasteShotBlock']:
                sendPanelMessage(self.data['clientMessages']['wasteShotBlockedMessage'], 'Yellow')
                return False
        elif hasattr(getTarget().publicInfo, 'team'):
            if self.data['teamShotBlock'] and (getPlayer().team is getTarget().publicInfo.team) and getTarget().isAlive():
                if not (self.data['teamKillerShotUnblock'] and getPlayer().guiSessionProvider.getArenaDP().isTeamKiller(getTarget().id)):
                    sendChatMessage(self.data['chatMessages'].replace('{name}', getTarget().publicInfo.name).replace('{vehicle}', getTarget().typeDescriptor.type.shortUserString), 1, 2)
                    sendPanelMessage(self.data['clientMessages']['teamShotBlockedMessage'], 'Yellow')
                    return False
            elif self.data['deadShotBlock'] and (not getTarget().isAlive()) and ((self.data['deadShotBlockTimeOut'] == 0) or ((serverTime() - self.deadDict.get(getTarget().id, 0)) < self.data['deadShotBlockTimeOut'])):
                sendPanelMessage(self.data['clientMessages']['deadShotBlockedMessage'], 'Yellow')
                return False
        return True

    def start_battle(self):
        InputHandler.g_instance.onKeyDown += self.keyPressed

    def endBattle(self):
        InputHandler.g_instance.onKeyDown -= self.keyPressed

    def keyPressed(self, event):
        if not self.data['enabled']:
            return
        if checkKeys(self.data['disableKey']) and event.isKeyDown():
            if self.data['triggerMessage']:
                self.is_key_pressed = not self.is_key_pressed
                sendPanelMessage(self.i18n['UI_triggerText_enabled'] if self.is_key_pressed else self.i18n['UI_triggerText_disabled'], 'Green' if self.is_key_pressed else 'Red')

    def new__addVehicleStatusUpdate(self, func, orig, vInfoVO):
        func(orig, vInfoVO)
        if not vInfoVO.isAlive() and self.data['enabled'] and self.data['deadShotBlock']:
            self.deadDict.update({vInfoVO.vehicleID: serverTime()})

    def new__shoot(self, func, orig, isRepeat=False):
        if self.isShotAllowed():
            func(orig, isRepeat)

    def new__shootDualGun(self, func, orig, chargeActionType, isPrepared=False, isRepeat=False):
        if self.isShotAllowed():
            func(orig, chargeActionType, isPrepared, isRepeat)

    def new__onBecomePlayer(self, func, orig):
        func(orig)
        self.isEventBattle = getPlayer().guiSessionProvider.arenaVisitor.gui.isEventBattle()

    def new__startGUI(self, func, *args):
        func(*args)
        self.start_battle()
        support.start_battle()


    def new__destroyGUI(self, func, orig, *args):
        func(orig, *args)
        self.endBattle()
        self.isEventBattle = False
        self.is_key_pressed = False
        self.deadDict.clear()


class Support(object):
    @staticmethod
    def message():
        sendPanelMessage(config.i18n['UI_battle_activateMessage'])

    def start_battle(self):
        if config.data['enabled'] and config.data['activateMessage']:
            callback(5.0, self.message)


config = ConfigInterface()
support = Support()
analytics = Analytics(config.ID, config.version, 'G-B7Z425MJ3L')
