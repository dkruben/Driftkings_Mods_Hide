# -*- coding: utf-8 -*-
import math

import BigWorld
import GUI
from Avatar import PlayerAvatar
from AvatarInputHandler import AvatarInputHandler
from VehicleGunRotator import VehicleGunRotator
from aih_constants import CTRL_MODE_NAME
from gui import g_guiResetters
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore

from DriftkingsCore import DriftkingsConfigInterface, override, Analytics, calculate_version, logError, replaceMacros

whitelisted_modes = (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.SNIPER, CTRL_MODE_NAME.DUAL_GUN)


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'orig: Archie-osu, refactor: Driftkings'
        self.data = {
            'enabled': True,
            'format': "<font size='16' color='{color}' face='$TitleFont'>{realDispersion:.1f} {percent}% - ({aimingTime:.1f}s)</font>",
            'gunRotationFix': True,
            'reticleScaling': True,
            'scalingType': 0,
            'textPosition': {
                'alignX': 'center',
                'alignY': 'center',
                'x': 0,
                'y': 200,
                'drag': True,
                'border': False,
                'visible': True,
                'alpha': 1.0,
            },
            'textShadow': {'distance': 0, 'angle': 90, 'color': '#000000', 'alpha': 1, 'blurX': 2, 'blurY': 2, 'strength': 200, 'quality': 1},
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_gunRotationFix_text': 'Enable gun rotation fix',
            'UI_setting_gunRotationFix_tooltip': 'Fixes gun rotation being desynced from the server even if using server reticle.\nThis may cause animations to become jerky or stuttery.\nDoesn\'t work if the "Enable Server Reticle" setting is off!',
            'UI_setting_reticleScaling_text': 'Enable reticle scaling',
            'UI_setting_reticleScaling_tooltip': 'Scales the reticle down to its true size according to shot distribution.\nThis leads to the reticle being smaller, but shots may now hit its very edge.',
            'UI_setting_format_text': 'Format',
            'UI_setting_template_tooltip': "Macros: '{color}' '{aimingTime:1f}', '{percent}', '{realDispersion:.1f}'",
            'UI_setting_scalingType_text': 'Reticle scaling type',
            'UI_setting_scalingType_tooltip': 'Controls how the reticle is scaled.\nLinear scaling is best suited for low-latency stable internet connections.\nInterpolated scaling prevents shots going outside of the reticle on unstable internet,\n while giving an impression of faster aiming time.'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('gunRotationFix'),
                self.tb.createControl('reticleScaling'),
            ],
            'column2': [
                self.tb.createControl('format', self.tb.types.TextInput, 400),
                self.tb.createOptions('scalingType', ['Linear', 'Interpolated']),
            ]
        }


class Flash(object):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self):
        self.name = {}
        self.data = {}

    def startBattle(self):
        if not config.data['enabled']:
            return
        self.data = self.setup()
        COMPONENT_EVENT.UPDATED += self.__updatePosition
        self.createObject(COMPONENT_TYPE.LABEL, self.data[COMPONENT_TYPE.LABEL])
        g_guiResetters.add(self.screenResize)

    def stopBattle(self):
        if not config.data['enabled']:
            return
        g_guiResetters.remove(self.screenResize)
        COMPONENT_EVENT.UPDATED -= self.__updatePosition
        self.deleteObject(COMPONENT_TYPE.LABEL)

    def deleteObject(self, name):
        g_guiFlash.deleteComponent(self.name[name])

    def createObject(self, name, data):
        g_guiFlash.createComponent(self.name[name], name, data)

    def updateObject(self, name, data):
        g_guiFlash.updateComponent(self.name[name], data)

    def __updatePosition(self, alias, props):
        if str(alias) == str(config.ID):
            x = props.get('x', config.data['textPosition']['x'])
            if x and x != config.data['textPosition']['x']:
                config.data['textPosition']['x'] = x
                self.data[COMPONENT_TYPE.LABEL]['x'] = x
            y = props.get('y', config.data['textPosition']['y'])
            if y and y != config.data['textPosition']['y']:
                config.data['textPosition']['y'] = y
                self.data[COMPONENT_TYPE.LABEL]['y'] = y
            config.onApplySettings({'textPosition': {'x': x, 'y': y}})

    def setup(self):
        self.name = {COMPONENT_TYPE.LABEL: str(config.ID)}
        self.data = {
            COMPONENT_TYPE.LABEL: {
                'x': 0,
                'y': 0,
                'drag': True,
                'border': True,
                'alignX': 'center',
                'alignY': 'center',
                'visible': True,
                'text': '',
                'shadow': {
                    'distance': config.data['textShadow']['distance'],
                    'angle': config.data['textShadow']['angle'],
                    'color': config.data['textShadow']['color'],
                    'alpha': config.data['textShadow']['alpha'],
                    'blurX': config.data['textShadow']['blurX'],
                    'blurY': config.data['textShadow']['blurY'],
                    'strength': config.data['textShadow']['strength'],
                    'quality': config.data['textShadow']['quality']
                }
            }
        }
        for key, value in config.data['textPosition'].items():
            if key in self.data[COMPONENT_TYPE.LABEL]:
                self.data[COMPONENT_TYPE.LABEL][key] = value
        return self.data

    def simpleText(self, text):
        self.updateObject(COMPONENT_TYPE.LABEL, {'text': str(text)})

    def setVisible(self, status):
        self.updateObject(COMPONENT_TYPE.LABEL, {'visible': status})

    @staticmethod
    def screenFix(screen, value, align=1):
        if align == 1:
            return float(max(0, min(value, screen), 0))
        if align == -1:
            return float(min(0, max(value, -screen)))
        scr = screen / 2.0
        if align == 0:
            return float(max(scr, min(value, -scr)))
        return value

    def screenResize(self):
        curScr = GUI.screenResolution()
        scale = float(self.settingsCore.interfaceScale.get())
        xMo, yMo = curScr[0] / scale, curScr[1] / scale
        x = config.data['textPosition'].get('x')
        alignX = config.data['textPosition'].get('alignX')
        if alignX == COMPONENT_ALIGN.LEFT:
            x = self.screenFix(xMo, config.data['textPosition']['x'], 1)
        elif alignX == COMPONENT_ALIGN.RIGHT:
            x = self.screenFix(xMo, config.data['textPosition']['x'], -1)
        elif alignX == COMPONENT_ALIGN.CENTER:
            x = self.screenFix(xMo, config.data['textPosition']['x'], 0)
        if x is not None and x != config.data['textPosition']['x']:
            config.data['textPosition']['x'] = x
            self.data[COMPONENT_TYPE.LABEL]['x'] = x
        y = config.data['textPosition'].get('y')
        alignY = config.data['textPosition'].get('alignY')
        if alignY == COMPONENT_ALIGN.TOP:
            y = self.screenFix(yMo, config.data['textPosition']['y'], 1)
        elif alignY == COMPONENT_ALIGN.BOTTOM:
            y = self.screenFix(yMo, config.data['textPosition']['y'], -1)
        elif alignY == COMPONENT_ALIGN.CENTER:
            y = self.screenFix(yMo, config.data['textPosition']['y'], 0)
        if y is not None and y != config.data['textPosition']['y']:
            config.data['textPosition']['y'] = y
            self.data[COMPONENT_TYPE.LABEL]['y'] = y
        self.updateObject(COMPONENT_TYPE.LABEL, {'x': x, 'y': y})

    def getData(self):
        return self.data

    def getNames(self):
        return self.name


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)
g_flash = Flash()
try:
    from gambiter import g_guiFlash
    from gambiter.flash import COMPONENT_TYPE, COMPONENT_EVENT, COMPONENT_ALIGN
except ImportError as err:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    logError(config.ID, 'gambiter.GUIFlash not found. {}', err)


class ReticleManager(object):
    def __init__(self):
        self.easingFactor = 1
        self.macro = {}

    @staticmethod
    def easeAiming(x):
        x = max(0.0, min(1.0, x))
        return 1.0 - math.cos((x * math.pi) / 2.0)

    @staticmethod
    def getColor(percent):
        if percent < 15:
            return '#FE0E00'
        elif percent < 35:
            return '#FE7903'
        elif percent < 50:
            return '#F8F400'
        elif percent < 75:
            return '#A6FFA6'
        elif percent < 90:
            return '#02C9B3'
        return '#D042F3'

    @staticmethod
    def calculateAimingData(avatar):
        aimingStartTime = avatar._PlayerAvatar__aimingInfo[0]
        aimingStartFactor = avatar._PlayerAvatar__aimingInfo[1]
        multFactor = avatar._PlayerAvatar__dispersionInfo[0]
        totalAimingTime = avatar._PlayerAvatar__dispersionInfo[4]
        currentTime = BigWorld.time()
        aimingTimeRemaining = max(aimingStartTime + (totalAimingTime * math.log(aimingStartFactor / multFactor)) - currentTime, 0)
        return aimingTimeRemaining, totalAimingTime

    def updateMacros(self, data):
        for key, value in data.items():
            if isinstance(value, float):
                self.macro['{%s:.1f}' % key] = str(round(value, 1))
            self.macro['{%s}' % key] = str(value)


g_work = ReticleManager()

@override(PlayerAvatar, 'getOwnVehicleShotDispersionAngle')
def new__getOwnVehicleShotDispersionAngle(func, self, turretRotationSpeed, withShot=0):
    result = func(self, turretRotationSpeed, withShot)
    if not config.data.get('enabled', False):
        return result
    currentDispersion = result[0] * 100
    reticleScaling = config.data.get('reticleScaling', False)
    if reticleScaling and config.data.get('scalingType', 0) == 0:
        realDispersion = currentDispersion / 1.71
    else:
        realDispersion = currentDispersion
    aimingTimeRemaining, totalAimingTime = g_work.calculateAimingData(self)
    if config.data.get('scalingType', 0) == 1 and reticleScaling:
        # fullyAimedDispersion = currentDispersion * math.exp(-aimingTimeRemaining / totalAimingTime)
        g_work.easingFactor = 1 - g_work.easeAiming(min(aimingTimeRemaining / 4.5, 1))
        realDispersion = currentDispersion / max((1.71 * g_work.easingFactor), 1)
    g_work.easingFactor = min(g_work.easingFactor, currentDispersion)
    dispersionPercent = int(math.ceil((g_work.easingFactor / currentDispersion) * 100))
    color = g_work.getColor(dispersionPercent)
    data = {
        'color': color,
        'realDispersion': realDispersion,
        'percent': str(dispersionPercent),
        'aimingTime': aimingTimeRemaining
    }
    g_work.updateMacros(data)
    format_text = replaceMacros(config.data['format'], g_work.macro)
    g_flash.setVisible(True)
    g_flash.simpleText(format_text)
    return result


@override(AvatarInputHandler, 'updateClientGunMarker')
def new__updateClientGunMarker(func, self, pos, direction, size, sizeOffset, relaxTime, collData):
    if (self._AvatarInputHandler__ctrlModeName in whitelisted_modes) and config.data['enabled'] and config.data['reticleScaling']:
        size = size / max((1.71 * g_work.easingFactor, 1))
    return func(self, pos, direction, size, sizeOffset, relaxTime, collData)


@override(AvatarInputHandler, 'updateServerGunMarker')
def new__updateServerGunMarker(func, self, pos, direction, size, sizeOffset, relaxTime, collData):
    if (self._AvatarInputHandler__ctrlModeName in whitelisted_modes) and config.data['enabled'] and config.data['reticleScaling']:
        size = size / max((1.71 * g_work.easingFactor, 1))
    return func(self, pos, direction, size, sizeOffset, relaxTime, collData)


@override(AvatarInputHandler, 'updateDualAccGunMarker')
def new__updateDualAccGunMarker(func, self, pos, direction, size, sizeOffset, relaxTime, collData):
    if (self._AvatarInputHandler__ctrlModeName in whitelisted_modes) and config.data['enabled'] and config.data['reticleScaling']:
        size = size / 1.71
    return func(self, pos, direction, size, sizeOffset, relaxTime, collData)


@override(VehicleGunRotator, 'setShotPosition')
def new__setShotPosition(func, self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh=False):
    if self._avatar.vehicle and config.data['gunRotationFix'] and config.data.get('enabled', True):
        self._VehicleGunRotator__turretYaw, self._VehicleGunRotator__gunPitch = self._avatar.vehicle.getServerGunAngles()
        forceValueRefresh = True
    return func(self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh)


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(func, self):
    func(self)
    g_flash.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new__destroyGUI(func, self):
    func(self)
    g_flash.stopBattle()
