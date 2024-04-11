# -*- coding: utf-8 -*-
import math

import BigWorld
import CommandMapping
import Math
from Avatar import PlayerAvatar
from AvatarInputHandler import cameras, control_modes
from gui.shared.personality import ServicesLocator

from DriftkingsCore import SimpleConfigInterface, Analytics, override, getPlayer, getTarget, getEntity


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        self.player = None
        self.angle = None
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.7.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (spoter mods)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'angle': 1.3,
            'catchHiddenTarget': True,
            'disableArtyMode': True
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_angle_text': 'Set angle to catch target',
            'UI_setting_angle_value': 'x',
            'UI_setting_catchHiddenTarget_text': 'Catch target hidden behind an obstacle',
            'UI_setting_catchHiddenTarget_tooltip': '',
            'UI_setting_disableArtyMode_text': 'Disable in Arty mode',
            'UI_setting_disableArtyMode_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createSlider('angle', 0, 90.0, 0.1, '{{value}}%s' % self.i18n['UI_setting_angle_value'])
            ],
            'column2': [
                self.tb.createControl('catchHiddenTarget'),
                self.tb.createControl('disableArtyMode')
            ]
        }

    def startBattle(self):
        self.player = getPlayer()
        self.angle = math.radians(self.data['angle'])

    def catch(self):
        # noinspection PyProtectedMember
        if self.player._PlayerAvatar__autoAimVehID:
            return
        if getTarget() is not None:
            return
        if self.player.isObserver():
            return
        playerPosition = self.player.getOwnVehiclePosition()
        minRadian = 100000.0
        result = None
        result_len = None
        for vId, vData in self.player.arena.vehicles.iteritems():
            if vData['team'] != self.player.team and vData['isAlive']:
                vehicle = getEntity(vId)
                if vehicle is not None and vehicle.isStarted and vehicle.isAlive():
                    radian = self.calc_radian(vehicle.position, self.angle)
                    if radian:
                        length = Math.Vector3(vehicle.position - playerPosition).length
                        if result_len is None:
                            result_len = length
                            result = vehicle
                        if radian < minRadian and result_len >= length:
                            minRadian = radian
                            result = vehicle
        if self.data['catchHiddenTarget']:
            self.player.autoAim(result)
            return result if result is not None else None
        if result is not None and BigWorld.wg_collideSegment(self.player.spaceID, result.position, cameras.getWorldRayAndPoint(0, 0)[1], 128) is None:
            self.player.autoAim(result)
            return result if result is not None else None
        return

    @staticmethod
    def calc_radian(target_position, angle):
        cameraDir, cameraPos = cameras.getWorldRayAndPoint(0, 0)
        cameraDir.normalise()
        cameraToTarget = target_position - cameraPos
        dot = cameraToTarget.dot(cameraDir)
        if dot < 0:
            return
        targetRadian = cameraToTarget.lengthSquared
        radian = 1.0 - dot * dot / targetRadian
        if radian > angle:
            return
        return radian

    def injectButton(self, isDown, key):
        if self.data['enabled'] and self.player is not None:
            battle = ServicesLocator.appLoader.getDefBattleApp()
            if battle:
                if CommandMapping.g_instance.isFired(CommandMapping.CMD_CM_LOCK_TARGET, key) and isDown:
                    return self.catch()
        return


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    config.startBattle()


@override(control_modes.SniperControlMode, 'handleKeyEvent')
def new_keyEventSniper(func, *args):
    if config.injectButton(args[1], args[2]):
        return True
    func(*args)


@override(control_modes.StrategicControlMode, 'handleKeyEvent')
def new_keyEventStrategic(func, *args):
    if not config.data['disableArtyMode'] and config.injectButton(args[1], args[2]):
        return True
    func(*args)


@override(control_modes.ArtyControlMode, 'handleKeyEvent')
def new_keyEventArty(func, *args):
    if not config.data['disableArtyMode'] and config.injectButton(args[1], args[2]):
        return True
    func(*args)


@override(control_modes.ArcadeControlMode, 'handleKeyEvent')
def new_keyEventArcade(func, *args):
    if config.injectButton(args[1], args[2]):
        return True
    func(*args)
