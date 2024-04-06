# -*- coding: utf-8 -*-
import math
import traceback
from functools import partial
from collections import defaultdict


import BigWorld
import CommandMapping
# import messenger.gui.Scaleform.view.battle.messenger_view as MESSEGER_VIEW
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
from gui.shared.gui_items.Vehicle import VEHICLE_CLASS_NAME
from items import vehicles

from DriftkingsCore import SimpleConfigInterface, Analytics, override, sendChatMessage, getPlayer, callback, getTarget


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.3.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'maxLinesCount': 8,
            'artyMessage': True,
            'artyTxt': '(%(player-tank)s, %(player-name)s) shoot me :(',
            'clipLoad': True,
            'loadTxt': 'Reloading at %(pos)s, for %(load)s seconds.',
            'attackCommandOnSight': False,
            'delaySight': 2.0,
            'debug': True,
            'timeout': 5.0
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_infoCountLine_text': 'Chat Lines Control:',
            'UI_setting_linesCount_text': 'Enable Lines Count',
            'UI_setting_linesCount_tooltip': 'Enable limit lines in game chat.',
            'UI_setting_maxLinesCount_text': 'Max. Lines Count',
            'UI_setting_maxLinesCount_tooltip': 'Maximum number of lines in chat (maximum value 6).',
            'UI_setting_infoArtyMessage_text': 'Arty Damage:',
            'UI_setting_artyMessage_text': 'Arty Damage Message',
            'UI_setting_artyMessage_tooltip': 'Arty Damage Massage',
            'UI_setting_artyTxt_text': 'Text Format',
            'UI_setting_artyTxt_tooltip': 'Use macros to edit the message.\n(macros: \'%(player-tank)s - %(player-name)s\')',
            'UI_setting_infoClipLoad_text': 'ReLoad Clip Time:',
            'UI_setting_clipLoad_text': 'ReLoad Status',
            'UI_setting_clipLoad_tooltip': 'Clip Load Time Massage',
            'UI_setting_loadTxt_text': 'Text Format',
            'UI_setting_loadTxt_tooltip': 'Use macros to edit the message\n (macros: \'%(load)s\' - \'%(pos)s\')',
            'UI_setting_infoAttackCommandOnSight_text': 'Attack Command On Sight:',
            'UI_setting_attackCommandOnSight_text': 'Attack Command On Sight Message',
            'UI_setting_attackCommandOnSight_tooltip': 'AutoFocus Message',
            'UI_setting_delaySight_text': 'Delay',
            'UI_setting_delaySight_tooltip': 'Text message remains on screen for this amount of seconds before fading out.',
            'UI_setting_timeout_text': 'Time before text message disappears',
            'UI_setting_timeout_tooltip': 'Text message remains on screen for this amount of seconds before fading out.'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        infoALabel = self.tb.createLabel('infoArtyMessage')
        infoALabel['text'] += ''
        infoClLabel = self.tb.createLabel('infoClipLoad')
        infoClLabel['text'] += ''
        infoCLabel = self.tb.createLabel('infoAttackCommandOnSight')
        infoCLabel['text'] += ''
        infoCountLine = self.tb.createLabel('infoCountLine')
        infoCountLine['text'] += ''
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createStepper('maxLinesCount', 2.0, 10.0, 1.0, True),
                infoALabel,
                self.tb.createControl('artyMessage'),
                self.tb.createControl('artyTxt', self.tb.types.TextInput, 300),
                infoClLabel,
                self.tb.createControl('clipLoad'),
                self.tb.createControl('loadTxt', self.tb.types.TextInput, 300),
            ],
            'column2': [
                infoCLabel,
                self.tb.createControl('attackCommandOnSight'),
                self.tb.createSlider('delaySight', 0.2, 0.8, 0.1, '{{value}} ' + ' M.sec'),
                self.tb.createSlider('timeout', 1.0, 10.0, 1.0, '{{value}} ' + ' sec'),
            ]
        }


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class Worker(object):

    def __init__(self):
        self.macro = defaultdict(lambda: 'Macros does not exist')
        self.__time = 0.5
        self.lastAttackCommandTime = 0

    @staticmethod
    def getSquarePosition():
        def clamp(val, vMax):
            vMin = 0.1
            return vMin if (val < vMin) else vMax if (val > vMax) else val

        def pos2name(pos):
            sqrsName = 'KJHGFEDCBA'
            linesName = '1234567890'
            return '%s%s' % (sqrsName[int(pos[1]) - 1], linesName[int(pos[0]) - 1])

        arena = getattr(getPlayer(), 'arena', None)
        boundingBox = arena.arenaType.boundingBox
        position = BigWorld.entities[getPlayer().playerVehicleID].position

        positionRect = (position[0], position[2])
        bottomLeft, upperRight = boundingBox
        spaceSize = upperRight - bottomLeft
        relPos = positionRect - bottomLeft
        relPos[0] = clamp(relPos[0], spaceSize[0])
        relPos[1] = clamp(relPos[1], spaceSize[1])

        return pos2name((math.ceil(relPos[0] / spaceSize[0] * 10), math.ceil(relPos[1] / spaceSize[1] * 10)))

    def artyCoolDownMessage(self, attackerID):
        player = getPlayer()
        attacker = player.arena.vehicles.get(attackerID)
        if attacker is None:
            return
        if attacker['vehicleType'] is None:
            return
        if vehicles.getVehicleClass(attacker['vehicleType'].type.compactDescr) == VEHICLE_CLASS_NAME.SPG:
            if player.team != attacker['team']:
                self.macro['player-tank'] = attacker['vehicleType'].type.shortUserString
                self.macro['player-name'] = attacker['name']
                self.macro['pos'] = self.getSquarePosition()
                message = config.data['artyTxt'] % self.macro
                if message:
                    sendChatMessage(message, 1, config.data['delay'])

    def onReload(self, avatar):
        self.macro['load'] = math.ceil(avatar.guiSessionProvider.shared.ammo.getGunReloadingState().getTimeLeft())
        self.macro['pos'] = self.getSquarePosition()
        message = config.data['loadTxt'] % self.macro
        if len(message) > 0:
            avatar.guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(message, 0)
        else:
            avatar.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.RELOADINGGUN)

    def onSight(self, avatar, target):
        if ((BigWorld.serverTime() - self.lastAttackCommandTime) > config.data['timeout']) and (getTarget() == target):
            avatar.guiSessionProvider.shared.chatCommands.sendTargetedCommand(BATTLE_CHAT_COMMAND_NAMES.ATTACK_ENEMY, target.id)
        self.lastAttackCommandTime = BigWorld.serverTime()


g_mod = Worker()


# hooks
@override(Vehicle, 'showDamageFromShot')
def new_showDamageFromShot(func, self, vehicle, attackerID, points, effectsIndex, damageFactor, *args, **kwargs):
    func(self, attackerID, self, vehicle, attackerID, points, effectsIndex, damageFactor, *args, **kwargs)
    if config.data['enabled'] and config.data['artyMessage']:
        if self.isPlayerVehicle and self.isAlive():
            g_mod.artyCoolDownMessage(attackerID)


@override(Vehicle, 'showDamageFromExplosion')
def new_showDamageFromExplosion(func, self, vehicle, attackerID, center, effectsIndex, damageFactor, *args, **kwargs):
    func(self, self, vehicle, attackerID, center, effectsIndex, damageFactor, *args, **kwargs)
    if config.data['enabled'] and config.data['artyMessage']:
        if self.isPlayerVehicle and self.isAlive():
            g_mod.artyCoolDownMessage(attackerID)


@override(PlayerAvatar, 'targetFocus')
def new_targetFocus(func, self, entity):
    func(self, entity)
    if config.data['attackCommandOnSight']:
        if self.isVehicleAlive and entity.isAlive() and hasattr(entity, 'publicInfo') and (self.team != entity.publicInfo['team']):
            callback(float(config.data['delaySight']), partial(g_mod.onSight, self, entity))


@override(PlayerAvatar, 'handleKey')
def handleKey(func, self, isDown, key, mods):
    if config.data['enabled'] and config.data['clipLoad']:
        try:
            cmdMap = CommandMapping.g_instance
            if cmdMap.isFired(CommandMapping.CMD_RELOAD_PARTIAL_CLIP, key) and isDown and self.isVehicleAlive:
                self.guiSessionProvider.shared.ammo.reloadPartialClip(self)
                callback(0.5, partial(g_mod.onReload, self))
                return True
        except StandardError:
            traceback.print_exc()

    func(self, isDown, key, mods)


# @override(MESSEGER_VIEW, '_makeSettingsVO')
# def new_makeSettingsVO(func, arenaVisitor):
#    result = func(arenaVisitor)
#    if config.data['enabled']:
#        result['maxLinesCount'] = config.data['maxLinesCount']
#        return result
