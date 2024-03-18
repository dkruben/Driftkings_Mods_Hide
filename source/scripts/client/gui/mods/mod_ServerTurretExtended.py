# -*- coding: utf-8 -*-
import math

import BigWorld
import CommandMapping
import Keys
import VehicleGunRotator
import gun_rotation_shared
from Avatar import PlayerAvatar, MOVEMENT_FLAGS
from AvatarInputHandler.siege_mode_player_notifications import SOUND_NOTIFICATIONS
from constants import VEHICLE_SETTING, VEHICLE_SIEGE_STATE
from gui import InputHandler
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE

from DriftkingsCore import SimpleConfigInterface, override, checkKeys, Analytics, callback, cancelCallback, getPlayer, sendPanelMessage


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.6.5 (%(file_compile_date)s)'
        self.author = ' (orig by spoter)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.defaultKeys = {
            'buttonAutoMode': [Keys.KEY_R, [Keys.KEY_LALT, Keys.KEY_RALT]],
            'buttonMaxMode': [Keys.KEY_R, [Keys.KEY_LCONTROL, Keys.KEY_RCONTROL]]
        }
        self.data = {
            'enabled': True,
            'activateMessage': False,
            'fixAccuracyInMove': True,
            'serverTurret': False,
            'fixWheelCruiseControl': True,
            'autoActivateWheelMode': True,
            'maxWheelMode': True,
            'buttonAutoMode': self.defaultKeys['buttonAutoMode'],
            'buttonMaxMode': self.defaultKeys['buttonMaxMode'],
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_activateMessage_text': 'Show Activation Message',
            'UI_setting_activateMessage_tooltip': 'Show Activation Message in battle',
            'UI_setting_fixAccuracyInMove_text': 'Fix Accuracy',
            'UI_setting_fixAccuracyInMove_tooltip': 'When you tank move and then stop, used fix accuracy to not lost aiming',
            'UI_setting_serverTurret_text': 'Server Turret',
            'UI_setting_serverTurret_tooltip': 'Move Turret to Server Aim coordinates (need enabled Server Sight in game settings)',
            'UI_battle_activateMessage': '\'Server Turret Extended\': Activated',
            'UI_setting_fixWheelCruiseControl_text': 'Fix Cruise Control on Wheels',
            'UI_setting_fixWheelCruiseControl_tooltip': 'When you activate Wheel mode with Cruise Control, vehicle stopped, this setting disable that',
            'UI_setting_maxWheelMode_text': 'Wheels: Keep maximum speed',
            'UI_setting_maxWheelMode_tooltip': 'When reaching maximum speed, does not disable speed mode when maneuvering',
            'UI_setting_buttonMaxMode_text': 'Button: Wheels keep maximum speed',
            'UI_setting_buttonMaxMode_tooltip': '',
            'UI_setting_autoActivateWheelMode_text': 'Wheels: Auto speed mode',
            'UI_setting_autoActivateWheelMode_tooltip': 'Automatically turns on speed or maneuvering mode',
            'UI_setting_buttonAutoMode_text': 'Button: Wheels auto speed mode',
            'UI_setting_buttonAutoMode_tooltip': '',
            'UI_battle_ON': 'ON',
            'UI_battle_OFF': 'OFF',
        }

        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('serverTurret'),
                self.tb.createControl('fixAccuracyInMove'),
                self.tb.createControl('fixWheelCruiseControl'),
                self.tb.createControl('activateMessage')
            ],
            'column2': [
                self.tb.createHotKey('buttonAutoMode'),
                self.tb.createHotKey('buttonMaxMode'),
                self.tb.createControl('maxWheelMode'),
                self.tb.createControl('fixWheelCruiseControl'),
                self.tb.createControl('autoActivateWheelMode')
            ]
        }


class MovementControl(object):
    timer = None
    callback = None

    @staticmethod
    def move_pressed(avatar, is_down, key):
        if CommandMapping.g_instance.isFiredList((CommandMapping.CMD_MOVE_FORWARD, CommandMapping.CMD_MOVE_FORWARD_SPEC, CommandMapping.CMD_MOVE_BACKWARD, CommandMapping.CMD_ROTATE_LEFT, CommandMapping.CMD_ROTATE_RIGHT), key):
            avatar.moveVehicle(0, is_down)

    def startBattle(self):
        InputHandler.g_instance.onKeyDown += self.keyPressed
        InputHandler.g_instance.onKeyUp += self.keyPressed
        self.timer = BigWorld.time()
        if self.callback is None:
            self.callback = callback(0.1, self.onCallback)
        return

    def endBattle(self):
        if self.callback is not None:
            cancelCallback(self.callback)
            self.callback = None
        InputHandler.g_instance.onKeyDown -= self.keyPressed
        InputHandler.g_instance.onKeyUp -= self.keyPressed
        return

    def onCallback(self):
        if config.data['enabled'] and config.data['autoActivateWheelMode']:
            self.changeMovement()
        self.callback = callback(0.1, self.onCallback)

    @staticmethod
    def keyPressed(event):
        if not config.data['enabled']:
            return
        if checkKeys(config.data['buttonAutoMode']) and event.isKeyDown():
            vehicle = getPlayer().getVehicleAttached()
            if vehicle and vehicle.isAlive() and vehicle.isWheeledTech and vehicle.typeDescriptor.hasSiegeMode:
                config.data['maxWheelMode'] = not config.data['maxWheelMode']
                message = '%s: %s' % (config.i18n['UI_setting_maxWheelMode_text'], config.i18n['UI_AutoMode_on'] if config.data['maxWheelMode'] else config.i18n['UI_AutoMode_off'])
                sendPanelMessage(message, 'Red')
        if checkKeys(config.data['buttonAutoMode']) and event.isKeyDown():
            vehicle = BigWorld.player().getVehicleAttached()
            if vehicle and vehicle.isAlive() and vehicle.isWheeledTech and vehicle.typeDescriptor.hasSiegeMode:
                config.data['autoActivateWheelMode'] = not config.data['autoActivateWheelMode']
                message = '%s: %s' % (config.i18n['UI_setting_autoActivateWheelMode_text'], config.i18n['UI_AutoMode_on'] if config.data['autoActivateWheelMode'] else config.i18n['UI_AutoMode_off'])
                sendPanelMessage(message, 'Red')

    # noinspection PyProtectedMember
    def changeMovement(self):
        player = BigWorld.player()
        vehicle = player.getVehicleAttached()
        if vehicle and vehicle.isAlive() and vehicle.isWheeledTech and vehicle.typeDescriptor.hasSiegeMode:
            flags = player.makeVehicleMovementCommandByKeys()
            if vehicle.siegeState == VEHICLE_SIEGE_STATE.DISABLED:
                if player._PlayerAvatar__cruiseControlMode:
                    return self.changeSiege(True)
                if flags & MOVEMENT_FLAGS.ROTATE_RIGHT or flags & MOVEMENT_FLAGS.ROTATE_LEFT or flags & MOVEMENT_FLAGS.BLOCK_TRACKS:
                    return
                if flags & MOVEMENT_FLAGS.FORWARD:
                    return self.changeSiege(True)
                if flags & MOVEMENT_FLAGS.BACKWARD:
                    return self.changeSiege(True)
            if vehicle.siegeState == VEHICLE_SIEGE_STATE.ENABLED:
                if not player._PlayerAvatar__cruiseControlMode:
                    realSpeed = int(vehicle.speedInfo.value[0] * 3.6)
                    checkSpeedLimits = self.checkSpeedLimits(vehicle, realSpeed)
                    if flags & MOVEMENT_FLAGS.ROTATE_RIGHT and checkSpeedLimits:
                        return self.changeSiege(False)
                    if flags & MOVEMENT_FLAGS.ROTATE_LEFT and checkSpeedLimits:
                        return self.changeSiege(False)
                    if flags & MOVEMENT_FLAGS.BLOCK_TRACKS:
                        return self.changeSiege(False)
                    if 20 > realSpeed > -20:
                        if not CommandMapping.g_instance.isActiveList((CommandMapping.CMD_MOVE_FORWARD, CommandMapping.CMD_MOVE_FORWARD_SPEC, CommandMapping.CMD_MOVE_BACKWARD)):
                            return self.changeSiege(False)
                        if realSpeed < 0 and flags & MOVEMENT_FLAGS.FORWARD:
                            return self.changeSiege(False)
                        if realSpeed > 0 and flags & MOVEMENT_FLAGS.BACKWARD:
                            return self.changeSiege(False)

    def changeSiege(self, status):
        SOUND_NOTIFICATIONS.TRANSITION_TIMER = ''
        getPlayer().cell.vehicle_changeSetting(VEHICLE_SETTING.SIEGE_MODE_ENABLED, status)
        self.timer = BigWorld.time()

    @staticmethod
    def checkSpeedLimits(vehicle, speed):
        if not config.data['maxWheelMode']:
            return True
        speedLimits = vehicle.typeDescriptor.defaultVehicleDescr.physics['speedLimits']
        return int(speedLimits[0] * 3.6) > speed > -int(speedLimits[1] * 3.6)

    @staticmethod
    def fixSiegeModeCruiseControl():
        vehicle = getPlayer().getVehicleAttached()
        result = vehicle and vehicle.isAlive() and vehicle.isWheeledTech and vehicle.typeDescriptor.hasSiegeMode
        if result:
            soundStateChange = vehicle.typeDescriptor.type.siegeModeParams['soundStateChange']
            vehicle.appearance.engineAudition.setSiegeSoundEvents(soundStateChange.isEngine, soundStateChange.npcOn, soundStateChange.npcOff)
        return result


class Support(object):
    @staticmethod
    def message():
        sendPanelMessage(config.i18n['UI_battle_activateMessage'])

    def startBattle(self):
        if config.data['enabled'] and config.data['activateMessage']:
            callback(5.0, self.message)


config = ConfigInterface()
movement_control = MovementControl()
support = Support()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(PlayerAvatar, 'handleKey')
def new_playerAvatarHandleKey(func, *args):
    if config.data['enabled'] and config.data['fixAccuracyInMove']:
        self, is_down, key, mods = args
        movement_control.move_pressed(self, is_down, key)
    return func(*args)


@override(VehicleGunRotator.VehicleGunRotator, 'setShotPosition')
def new_vehicleGunRotatorSetShotPosition(func, self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh=False):
    if config.data['enabled']:
        if self._avatar.vehicle:
            self._VehicleGunRotator__turretYaw, self._VehicleGunRotator__gunPitch = self._avatar.vehicle.getServerGunAngles()
        forceValueRefresh = config.data['serverTurret']
    return func(self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh)


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    support.startBattle()
    movement_control.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    movement_control.endBattle()
    func(*args)


@override(PlayerAvatar, 'updateSiegeStateStatus')
def updateSiegeStateStatus(func, self, vehicleID, status, timeLeft):
    if not movement_control.fixSiegeModeCruiseControl():
        return func(self, vehicleID, status, timeLeft)
    typeDescr = self._PlayerAvatar__updateVehicleStatus(vehicleID)
    if not typeDescr or not self.vehicle or vehicleID != self.vehicle.id:
        return
    self.guiSessionProvider.invalidateVehicleState(VEHICLE_VIEW_STATE.SIEGE_MODE, (status, timeLeft))
    self._PlayerAvatar__onSiegeStateUpdated(vehicleID, status, timeLeft)


def decodeRestrictedValueFromUInt(code, bits, minBound, maxBound):
    code -= 0.5
    t = float(code) / ((1 << bits) - 1)
    return minBound + t * (maxBound - minBound)


def decodeAngleFromUInt(code, bits):
    code -= 0.5
    return math.pi * 2.0 * code / (1 << bits) - math.pi


gun_rotation_shared.decodeRestrictedValueFromUint = decodeRestrictedValueFromUInt
gun_rotation_shared.decodeAngleFromUint = decodeAngleFromUInt
