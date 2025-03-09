# -*- coding: utf-8 -*-
# import BigWorld
import GUI
from Avatar import PlayerAvatar
from Event import Event
from Vehicle import Vehicle
from helpers.CallbackDelayer import CallbackDelayer
from constants import SHELL_TYPES
from gui import InputHandler, g_guiResetters
from helpers import dependency
from items import vehicles
from skeletons.account_helpers.settings_core import ISettingsCore
from vehicle_systems.CompoundAppearance import CompoundAppearance

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, logError, getPlayer, getEntity, replaceMacros


class Events(object):
    def __init__(self):
        self.onBattleLoaded = Event()
        self.onVehiclesChanged = Event()
        self.onCountChanged = Event()
        self.onChanceChanged = Event()
        self.onHealthChanged = Event()


events = Events()


class ConfigInterface(DriftkingsConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'by: StranikS_Scan, re-coded by: Driftkings'
        self.data = {
            'enabled': True,
            'format': '{header}: {allyChance} {compareSign} {enemyChance}',
            'background': True,
            'textPosition': {
                'alignX': 'right',
                'alignY': 'top',
                'x': -250,
                'y': 443,
                'drag': True,
                'border': False,
                'visible': True,
                'alpha': 1.0,
            },
            'textShadow': {'distance': 0, 'angle': 90, 'color': '#000000', 'alpha': 1, 'blurX': 2, 'blurY': 2, 'strength': 200, 'quality': 1},
            'textFormat': {
                'font': '$FieldFont',
                'size': 16,
                'bold': False,
                'italic': False,
                'color': '#DBD7D2',
            },
            'compareValuesColor': {
                'bestValue': '#90EE90',
                'worstValue': '#FFBCAD'
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_teamChances_text': 'Show team chances',
            'UI_setting_teamChances_tooltip': 'Displays win chance percentage for each team during battle',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [],
            'column2': []
        }


class Flash(object):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self):
        textFormat = config.data['textFormat']
        self.font = textFormat['font']
        self.size = textFormat['size']
        self.color = textFormat['color']
        self.bold = textFormat['bold']
        self.italic = textFormat['italic']
        self.begin = '<font face="%s" size="%d" color="%s">%s%s' % (self.font, self.size, self.color, '<b>' if self.bold else '', '<i>' if self.italic else '')
        self.end = '%s%s</font>' % ('</b>' if self.bold else '', '</i>' if self.italic else '')
        self.name = {}
        self.data = {}

    def startBattle(self):
        if not config.data['enabled']:
            return
        self.data = self.setup()
        COMPONENT_EVENT.UPDATED += self.__updatePosition
        self.createObject(COMPONENT_TYPE.LABEL, self.data[COMPONENT_TYPE.LABEL])
        self.updateObject(COMPONENT_TYPE.LABEL, {'background': config.data['background']})
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
        # Copy textPosition settings to component data
        for key, value in config.data['textPosition'].items():
            if key in self.data[COMPONENT_TYPE.LABEL]:
                self.data[COMPONENT_TYPE.LABEL][key] = value
        return self.data

    def getHtmlTextWithTags(self, text, font=None, size=None, color=None, bold=None, italic=None):
        if not text:
            return ''

        return '<font face=\'%s\' size=\'%d\' color=\'%s\'>%s%s%s%s%s</font>' % (font if font else self.font, size if size else self.size, color if color else self.color, '<b>' if bold or self.bold else '', '<i>' if italic or self.italic else '', text, '</b>' if bold or self.bold else '', '</i>' if italic or self.italic else '')

    def getSimpleTextWithTags(self, text):
        return self.begin + text + self.end if text else ''

    def HtmlText(self, text):
        formatText = str(text)
        self.updateObject(COMPONENT_TYPE.LABEL, {'text': formatText})

    def setVisible(self, status):
        data = {'visible': status}
        self.updateObject(COMPONENT_TYPE.LABEL, data)

    @staticmethod
    def screenFix(screen, value, align=1):
        if align == 1:
            if value > screen:
                return float(max(0, screen))
            if value < 0:
                return 0.0
        elif align == -1:
            if value < -screen:
                return min(0, -screen)
            if value > 0:
                return 0.0
        elif align == 0:
            scr = screen / 2.0
            if value < scr:
                return float(scr)
            if value > -scr:
                return float(-scr)
        return value

    def screenResize(self):
        try:
            curScr = GUI.screenResolution()
            scale = float(self.settingsCore.interfaceScale.get())
            xMo, yMo = curScr[0] / scale, curScr[1] / scale
            x = config.data['textPosition'].get('x', None)
            if config.data['textPosition']['alignX'] == COMPONENT_ALIGN.LEFT:
                x = self.screenFix(xMo, config.data['textPosition']['x'], 1)
            elif config.data['textPosition']['alignX'] == COMPONENT_ALIGN.RIGHT:
                x = self.screenFix(xMo, config.data['textPosition']['x'], -1)  # Fixed the missing comma
            elif config.data['textPosition']['alignX'] == COMPONENT_ALIGN.CENTER:
                x = self.screenFix(xMo, config.data['textPosition']['x'], 0)
            if x is not None and x != config.data['textPosition']['x']:
                config.data['textPosition']['x'] = x
                self.data[COMPONENT_TYPE.LABEL]['x'] = x
            y = config.data['textPosition'].get('y', None)
            if config.data['textPosition']['alignY'] == COMPONENT_ALIGN.TOP:
                y = self.screenFix(yMo, config.data['textPosition']['y'], 1)
            elif config.data['textPosition']['alignY'] == COMPONENT_ALIGN.BOTTOM:
                y = self.screenFix(yMo, config.data['textPosition']['y'], -1)
            elif config.data['textPosition']['alignY'] == COMPONENT_ALIGN.CENTER:
                y = self.screenFix(yMo, config.data['textPosition']['y'], 0)
            if y is not None and y != config.data['textPosition']['y']:
                config.data['textPosition']['y'] = y
                self.data[COMPONENT_TYPE.LABEL]['y'] = y
            self.updateObject(COMPONENT_TYPE.LABEL, {'x': x, 'y': y})
        except Exception as e:
            logError(config.ID, 'Error during screen resize: {}', e)

    def getData(self):
        return self.data

    def getNames(self):
        return self.name


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'G-B7Z425MJ3L')
g_flash = Flash()
try:
    from gambiter import g_guiFlash
    from gambiter.flash import COMPONENT_TYPE, COMPONENT_EVENT, COMPONENT_ALIGN
except ImportError as err:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    logError(config.ID, 'gambiter.GUIFlash not found. {}', err)


class TanksStatistic(object):
    allyChance = property(lambda self: self.__allyChance)
    enemyChance = property(lambda self: self.__enemyChance)
    allyTanksCount = property(lambda self: self.__allyTanksCount)
    enemyTanksCount = property(lambda self: self.__enemyTanksCount)
    allyTeamHP = property(lambda self: self.__allyTeamHP)
    enemyTeamHP = property(lambda self: self.__enemyTeamHP)
    allyTeamOneDamage = property(lambda self: self.__allyTeamOneDamage)
    enemyTeamOneDamage = property(lambda self: self.__enemyTeamOneDamage)
    allyTeamDPM = property(lambda self: self.__allyTeamDPM)
    enemyTeamDPM = property(lambda self: self.__enemyTeamDPM)
    allyTeamForces = property(lambda self: self.__allyTeamForces)
    enemyTeamForces = property(lambda self: self.__enemyTeamForces)

    def __init__(self):
        self.__getAllyTanksCount = lambda withDead=False: sum([1 for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTanksCount = lambda withDead=False: sum([1 for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getAllyTeamHP = lambda withDead=False: sum([value['hp'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTeamHP = lambda withDead=False: sum([value['hp'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getAllyTeamOneDamage = lambda withDead=False: sum([value['gun']['currentDamage'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTeamOneDamage = lambda withDead=False: sum([value['gun']['currentDamage'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getAllyTeamDPM = lambda withDead=False: sum([value['gun']['currentDpm'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTeamDPM = lambda withDead=False: sum([value['gun']['currentDpm'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getAllyTeamForces = lambda withDead=False: sum([value['force'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTeamForces = lambda withDead=False: sum([value['force'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.init()

    def init(self):
        self.base = {}
        self.__allyTanksCount = None
        self.__enemyTanksCount = None
        self.__allyTeamHP = None
        self.__enemyTeamHP = None
        self.__allyTeamOneDamage = None
        self.__enemyTeamOneDamage = None
        self.__allyTeamDPM = None
        self.__enemyTeamDPM = None
        self.__allyTeamForces = None
        self.__enemyTeamForces = None
        self.__enemyChance = None
        self.__allyChance = None

    def addVehicleInfo(self, vehicleID, vehicleInfo):
        if vehicleID not in self.base:
            vType = vehicleInfo['vehicleType']
            self.base[vehicleID] = tank = {}
            tank['accountDBID'] = vehicleInfo['accountDBID']
            tank['userName'] = vehicleInfo['name']
            tank['tank_id'] = vType.type.compactDescr
            tank['name'] = vType.type.shortUserString.replace(' ', '')
            tank['type'] = {}
            tank['type']['tag'] = set(vehicles.VEHICLE_CLASS_TAGS & vType.type.tags).pop()
            tank['isEnemy'] = vehicleInfo['team'] != getPlayer().team
            tank['isAlive'] = vehicleInfo['isAlive']
            tank['level'] = vType.level
            tank['hp'] = tank['hpMax'] = vType.maxHealth
            tank['gun'] = {}
            tank['gun']['reload'] = float(vType.gun.reloadTime)
            if vType.gun.clip[0] > 1:
                tank['gun']['ammer'] = {}
                tank['gun']['ammer']['reload'] = tank['gun']['reload']
                tank['gun']['ammer']['capacity'] = vType.gun.clip[0]
                tank['gun']['ammer']['shellReload'] = float(vType.gun.clip[1])
                tank['gun']['reload'] = tank['gun']['ammer']['shellReload'] + tank['gun']['ammer']['reload'] / tank['gun']['ammer']['capacity']
            tank['gun']['shell'] = {'AP': {'damage': 0, 'dpm': 0}, 'APRC': {'damage': 0, 'dpm': 0}, 'HC': {'damage': 0, 'dpm': 0}, 'HE': {'damage': 0, 'dpm': 0}}
            for shot in vType.gun.shots:
                tag = 'APRC' if shot.shell.kind == SHELL_TYPES.ARMOR_PIERCING_CR else ('HC' if shot.shell.kind == SHELL_TYPES.HOLLOW_CHARGE else ('HE' if shot.shell.kind == SHELL_TYPES.HIGH_EXPLOSIVE else 'AP'))
                damage = shot.shell.armorDamage[0] if hasattr(shot.shell, 'armorDamage') else shot.shell.damage[0]
                damage = float(damage)
                if damage > tank['gun']['shell'][tag]['damage']:
                    tank['gun']['shell'][tag]['damage'] = damage * (0.5 if tag == 'HE' else 1.0)
                    tank['gun']['shell'][tag]['dpm'] = damage * 60 / tank['gun']['reload']
            if 'SPG' == tank['type']['tag']:
                shell = 'HE'
            else:
                shell = 'AP' if tank['gun']['shell']['AP']['damage'] > 0 else ('APRC' if tank['gun']['shell']['APRC']['damage'] > 0 else ('HC' if tank['gun']['shell']['HC']['damage'] > 0 else 'HE'))
            tank['gun']['currentShell'] = shell
            tank['gun']['currentDamage'] = tank['gun']['shell'][shell]['damage']
            tank['gun']['currentDpm'] = tank['gun']['shell'][shell]['dpm']
            self.update(0, vehicleID)

    def update(self, reason, vehicleID):
        if self.base:
            if reason <= 2:
                self.__allyTeamHP = self.__getAllyTeamHP()
                self.__enemyTeamHP = self.__getEnemyTeamHP()
            if reason <= 1:
                self.__allyTanksCount = self.__getAllyTanksCount()
                self.__enemyTanksCount = self.__getEnemyTanksCount()
                self.__allyTeamOneDamage = self.__getAllyTeamOneDamage()
                self.__enemyTeamOneDamage = self.__getEnemyTeamOneDamage()
                self.__allyTeamDPM = self.__getAllyTeamDPM()
                self.__enemyTeamDPM = self.__getEnemyTeamDPM()
            for value in self.base.itervalues():
                if value['isAlive']:
                    if value['isEnemy']:
                        value['Th'] = value['hp'] / self.__allyTeamDPM if self.__allyTeamDPM > 0 else 999999.9
                        value['Te'] = self.__allyTeamHP / value['gun']['currentDpm']
                    else:
                        value['Th'] = value['hp'] / self.__enemyTeamDPM if self.__enemyTeamDPM > 0 else 999999.9
                        value['Te'] = self.__enemyTeamHP / value['gun']['currentDpm']
                    value['force'] = value['Th'] / value['Te'] if value['Te'] > 0 else 999999.9
                else:
                    value['Th'] = 0
                    value['Te'] = 999999.9
                    value['force'] = 0
            self.__allyTeamForces = self.__getAllyTeamForces()
            self.__enemyTeamForces = self.__getEnemyTeamForces()
            allForces = self.__allyTeamForces + self.__enemyTeamForces
            for value in self.base.itervalues():
                value['contribution'] = 100 * value['force'] / allForces if allForces != 0 and value['isAlive'] else 0
            self.__allyChance = 100 * self.__allyTeamForces / allForces if allForces != 0 else 0
            self.__enemyChance = 100 * self.__enemyTeamForces / allForces if allForces != 0 else 0
            # Events -----------------------------------------------------------
            events.onVehiclesChanged(self, reason, vehicleID)
            if reason <= 1:
                events.onCountChanged(self.__allyTanksCount, self.__enemyTanksCount)
            events.onHealthChanged(self.__allyTeamHP, self.__enemyTeamHP)
            events.onChanceChanged(self.__allyChance, self.__enemyChance, self.__allyTeamForces, self.__enemyTeamForces)


g_tanksStatistic  = TanksStatistic()


class Worked(CallbackDelayer):
    def __init__(self):
        CallbackDelayer.__init__(self)
        self.macro = {}
        self.compareValuesColor = (config.data['compareValuesColor']['bestValue'], config.data['compareValuesColor']['worstValue'], config.data['textFormat']['color'])

    @staticmethod
    def compare_sign(ally, enemy):
        if ally < enemy:
            return '&#x003C;'
        elif ally > enemy:
            return '&#x003E;'
        return '&#x007C;'

    def flash_text(self):
        if not config.data.get('enabled', False):
            return
        g_flash.setVisible(True)
        ally = g_tanksStatistic.allyChance
        enemy = g_tanksStatistic.enemyChance
        ally_text = self.formatChanceText(ally, enemy)
        enemy_text = self.formatChanceText(enemy, ally)
        text = self.formatText(ally_text, enemy_text, ally, enemy)
        data = g_flash.getSimpleTextWithTags(text)
        g_flash.HtmlText(data)
        self.delayCallback(0.3, self.flash_text)

    def formatChanceText(self, old, new):
        if old > new:
            color = self.compareValuesColor[0]
        elif old < new:
            color = self.compareValuesColor[1]
        else:
            color = self.compareValuesColor[2]
        return g_flash.getHtmlTextWithTags('%6.2f' % old, color=color)

    def updateMacros(self, data):
        for key, value in data.items():
            self.macro['{%s}' % key] = str(value)

    def formatText(self, allyText, enemyText, ally, enemy):
        data = {
            'header': 'Chances',
            'allyChance': allyText,
            'enemyChance': enemyText,
            'compareSign':  self.compare_sign(ally, enemy)
        }
        self.updateMacros(data)
        format_text = replaceMacros(config.data['format'], self.macro)
        return format_text


g_mod = Worked()


@override(Vehicle, 'onHealthChanged')
def new__onHealthChanged(func, self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
    func(self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs)
    if self.id in g_tanksStatistic.base:
        tank = g_tanksStatistic.base[self.id]
        if tank['hp'] != self.health:
            reason = 2
            tank['hp'] = self.health if self.health > 0 else 0
            if tank['hp'] == 0:
                tank['isAlive'] = False
                reason = 1
            g_tanksStatistic.update(reason, self.id)


@override(PlayerAvatar, 'vehicle_onAppearanceReady')
def new__onAppearanceReady(func, self, vehicle):
    func(self, vehicle)
    if vehicle.id in g_tanksStatistic.base:
        entity = getEntity(vehicle.id)
        if entity:
            tank = g_tanksStatistic.base[vehicle.id]
            if tank['hp'] != entity.health:
                reason = 2
                tank['hp'] = vehicle.health if vehicle.health > 0 else 0
                if tank['hp'] == 0:
                    tank['isAlive'] = False
                    reason = 1
                g_tanksStatistic.update(reason, vehicle.id)

@override(CompoundAppearance, 'prerequisites')
def new__prerequisites(func, self, typeDescriptor, vehicleID, *args, **kwargs):
    result = func(self, typeDescriptor, vehicleID, *args, **kwargs)
    try:
        g_tanksStatistic.addVehicleInfo(vehicleID, getPlayer().arena.vehicles.get(vehicleID))
    finally:
        return result


@override(PlayerAvatar, '_PlayerAvatar__onArenaVehicleKilled')
def new__onArenaVehicleKilled(func, self, targetID, *args, **kwargs):
    func(self, targetID, *args, **kwargs)
    if targetID in g_tanksStatistic.base:
        tank = g_tanksStatistic.base[targetID]
        if tank['isAlive']:
            tank['isAlive'] = False
            tank['hp'] = 0
            g_tanksStatistic.update(1, targetID)


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(func, self):
    func(self)
    g_tanksStatistic.init()
    for vehicleID in self.arena.vehicles:
        g_tanksStatistic.addVehicleInfo(vehicleID, self.arena.vehicles.get(vehicleID))
    g_flash.startBattle()
    g_mod.flash_text()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new__destroyGUI(func, self):
    func(self)
    g_flash.stopBattle()
