# -*- coding: utf-8 -*-
import Keys
from Avatar import PlayerAvatar
from BigWorld import serverTime
from gui import InputHandler
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats

from DriftkingsCore import SimpleConfigInterface, Analytics, override, getPlayer, getTarget, checkKeys, sendChatMessage, sendPanelMessage, logException


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        self._disable_key = False
        self.is_hot_key_event = False
        self.deadDict = {}
        self.isEventBattle = False
        super(ConfigInterface, self).__init__()
        override(FragsCollectableStats, 'addVehicleStatusUpdate', self.__addVehicleStatusUpdate)
        override(PlayerAvatar, 'shoot', self.__shoot)
        override(PlayerAvatar, 'onBecomePlayer', self.__onBecomePlayer)

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.5.5 (%(file_compile_date)s)'
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
                'wasteShotBlockedMessage': 'Waste shot blocked!',
                'teamShotBlockedMessage': 'Team shot blocked!',
                'deadShotBlockedMessage': 'Dead shot blocked!'
            },
            'format': '[{name} - {vehicle}], get out of the way!',
            'disableKey': self.defaultKeys['disableKey'],
            'onHold': True,
            'disableMessage': False
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            #
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
            sendPanelMessage('SafeShot: is enabled' if self.is_hot_key_event else 'SafeShot: is disabled', 'Green' if self.is_hot_key_event else 'Red')

    def __addVehicleStatusUpdate(self, func, b_self, vInfoVO):
        func(b_self, vInfoVO)
        if not vInfoVO.isAlive() and self.data['enabled'] and self.data['deadShotBlock']:
            self.deadDict.update({vInfoVO.vehicleID: serverTime()})

    def __shoot(self, func, b_self, isRepeat=False):
        if not (self.data['enabled'] and not self.is_hot_key_event and not self.isEventBattle):
            return func(b_self, isRepeat)
        else:
            if getTarget() is None:
                if self.data['wasteShotBlock']:
                    sendPanelMessage(text=self.data['clientMessages']['wasteShotBlockedMessage'], colour='Yellow')
                    return
            elif hasattr(getTarget().publicInfo, 'team'):
                if self.data['teamShotBlock'] and getPlayer().team is getTarget().publicInfo.team and getTarget().isAlive():
                    if not (self.data['teamKillerShotUnblock'] and getPlayer().guiSessionProvider.getArenaDP().isTeamKiller(getTarget().id)):
                        text = self.data['format']
                        text = text.replace('{name}', getTarget().publicInfo.name)
                        text = text.replace('{vehicle}', getTarget().typeDescriptor.type.shortUserString)
                        sendChatMessage(fullMsg=text, chanId=1, delay=2)
                        sendPanelMessage(text=self.data['clientMessages']['teamShotBlockedMessage'], colour='Yellow')
                        return
                elif self.data['deadShotBlock'] and not getTarget().isAlive() and (self.data['deadShotBlockTimeOut'] == 0 or serverTime() - self.deadDict.get(getTarget().id, 0) < self.data['deadShotBlockTimeOut']):
                    sendPanelMessage(text=self.data['clientMessages']['deadShotBlockedMessage'], colour='Yellow')
                    return
            return func(b_self, isRepeat)

    def __onBecomePlayer(self, func, b_self):
        func(b_self)
        self.isEventBattle = getPlayer().guiSessionProvider.arenaVisitor.gui.isEventBattle()


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    config.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new__destroyGUI(func, *args):
    func(*args)
    config.startBattle()
    config.deadDict = {}
