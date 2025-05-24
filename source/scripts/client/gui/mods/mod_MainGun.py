# -*- coding: utf-8 -*-
import os
import math

import BigWorld
import GUI
import ResMgr
from Vehicle import Vehicle
from Avatar import PlayerAvatar
from constants import ARENA_GUI_TYPE
from gui.Scaleform.daapi.view.battle.shared.ribbons_aggregator import RibbonsAggregator
from gui.battle_control.arena_info import vos_collections
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
from helpers.CallbackDelayer import CallbackDelayer

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, logError, calculate_version


class ConfigInterface(DriftkingsConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.1.5 (%(file_compile_date)s)'
        self.author = 'orig by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'backGroundEnabled': False,
            'textLock': False,
            'format': '<font size="16" face="$FieldFont"><b>{mainGun}</b></font>',
            'background': {
                'width': 200,
                'height': 50,
                'alpha': 80,
                'image': 'gui/maps/bg.png',
            },
            'mainGun': {
                'enabled': True,
                'dynamic': True,
                'format': "{mainGunIcon}{mainGunDoneIcon}{mainGunFailureIcon}  <font color='#E0E06D'>{mainGun}</font>",
                'mainGunDoneIcon': "<img src='img://gui/maps/icons/library/done.png' width='32' height='32' vspace='-8'>",
                'mainGunFailureIcon': "<img src='img://gui/maps/icons/library/icon_alert_32x32.png' width='32' height='32' vspace='-8'>",
                'mainGunIcon': "<img src='img://gui/maps/icons/achievement/32x32/mainGun.png' width='32' height='32' vspace='-8'>"
            },
            'shadow': {'enabled': True, 'distance': 0, 'angle': 90, 'color': '#000000', 'alpha': 0.8, 'blurX': 2, 'blurY': 2, 'strength': 2, 'quality': 4},
            'textPosition': {
                'alignX': 'left',
                'alignY': 'top',
                'x': 200,
                'y': 200
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_backGroundEnabled_text': 'BackGround',
            'UI_setting_backGroundEnabled_tooltip': '',
            'UI_setting_textLock_text': 'TextLock',
            'UI_setting_textLock_tooltip': '',

        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('backGroundEnabled'),
                self.tb.createControl('textLock')
            ],
            'column2': []
        }


class FlashController(object):
    def __init__(self, ID):
        self.ID = ID
        self.setup()
        COMPONENT_EVENT.UPDATED += self.__updatePosition

    def __updatePosition(self, alias, data):
        if alias != self.ID:
            return
        config.onApplySettings({'textPosition': data})

    def onApplySettings(self):
        g_guiFlash.updateComponent(self.ID, dict( config.data['textPosition'], drag=not config.data['textLock'], border=not config.data['textLock']))

    def setup(self):
        bgPath = config.data['background']['image']
        bgNormPath = os.path.normpath('gui/flash/' + bgPath).replace(os.sep, '/')
        bgSect = ResMgr.openSection(bgNormPath)
        if bgSect is None:
            logError(config.ID, 'Battle text background file not found: ' + bgNormPath)
        g_guiFlash.createComponent(self.ID, COMPONENT_TYPE.PANEL, dict(config.data['textPosition'], drag=not config.data['textLock'], border=not config.data['textLock'], limit=True))
        self.createBox()

    def createBox(self):
        bgConf = config.data['background']
        bgAltPath = '../maps/bg.png'
        bgPath = bgConf['image']
        width, height = bgConf['width'], bgConf['height']
        y = height
        g_guiFlash.createComponent(self.ID + '.text', COMPONENT_TYPE.LABEL, {'text': '', 'width': width, 'height': height, 'alpha': 0.0, 'x': 0, 'y': y, 'alignX': COMPONENT_ALIGN.CENTER, 'alignY': COMPONENT_ALIGN.TOP})
        shadow = config.data['shadow']
        if shadow['enabled']:
            g_guiFlash.updateComponent(self.ID + '.text', {'shadow': shadow})
        g_guiFlash.createComponent(self.ID + '.image', COMPONENT_TYPE.IMAGE, {'image': bgPath, 'imageAlt': bgAltPath, 'width': width, 'height': height, 'alpha': 0.0, 'x': 0, 'y': y + 2, 'alignX': COMPONENT_ALIGN.CENTER, 'alignY': COMPONENT_ALIGN.TOP})

    def destroy(self):
        COMPONENT_EVENT.UPDATED -= self.__updatePosition
        g_guiFlash.deleteComponent(self.ID + '.text')
        g_guiFlash.deleteComponent(self.ID + '.image')

    def addText(self, text):
        if not config.data['enabled']:
            return
        format_text = str(text)
        g_guiFlash.updateComponent(self.ID + '.text', {'text': format_text})
        g_guiFlash.updateComponent(self.ID + '.text', {'alpha': 1.0})
        if config.data['backGroundEnabled']:
            g_guiFlash.updateComponent(self.ID + '.image', {'alpha': config.data['background']['alpha']})


g_flash = None
config = ConfigInterface()
statistic_mod = Analytics(config.ID, config.version)
try:
    from gambiter import g_guiFlash
    from gambiter.flash import COMPONENT_TYPE, COMPONENT_ALIGN, COMPONENT_EVENT
    g_flash = FlashController(config.ID)
except ImportError:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    logError(config.ID, 'gambiter.GUIFlash not found. Text viewing disabled.')
except StandardError:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None


class Optimization(CallbackDelayer):
    def __init__(self):
        CallbackDelayer.__init__(self)

    def destroy(self):
        CallbackDelayer.destroy(self)


class MainGun(object):
    def __init__(self):
        self.players_damage = dict()
        self.mainGunText = ''
        self.totals = [0, 0, True, 0, 0]

    @property
    def showMainGun(self):
        return '{mainGun}' in config.data['format'] and (True if scl.guiType in [ARENA_GUI_TYPE.RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM] else False)

    def battleLoading(self):
        if self.showMainGun and scl.health[scl.enemyTeam][1]:
            self.totals[0] = max(1000, int(math.ceil(scl.health[scl.enemyTeam][1] * 0.2)))
        self.updateMainGun()

    def playersDamage(self, attackerID, damage, targetTeam, attakerTeam):
        p_damage = self.players_damage.setdefault(attackerID, [0, False])
        if targetTeam == attakerTeam:
            p_damage[1] = True
        else:
            p_damage[0] += damage
            if self.showMainGun and config.data['mainGun']['dynamic']:
                player_damage = self.players_damage.setdefault(scl.playerID, [0, False])
                if attackerID != scl.playerID and p_damage[0] > self.totals[3] and not p_damage[1]:
                    if p_damage[0] > self.totals[0] and p_damage[0] > player_damage[0]:
                        self.totals[3] = p_damage[0]
                        self.totals[2] = False
                        self.updateMainGun()
                if player_damage[1]:
                    self.totals[2] = False
                    self.updateMainGun()

    def onPlayerFeedbackReceived(self, events):
        for event in events:
            eventType = event.getType()
            extra = event.getExtra()
            if eventType == FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY:
                damage = extra.getDamage()
                self.totals[4] += damage
                if config.data['mainGun']['dynamic']:
                    self.updateMainGun()

    @staticmethod
    def recipes(value):
        return '{:,}'.format(int(value)).replace(',', ' ')

    def updateMainGun(self):
        macros = {
            'mainGun': 0,
            'mainGunIcon': config.data['mainGun']['mainGunIcon'],
            'mainGunDoneIcon': '',
            'mainGunFailureIcon': config.data['mainGun']['mainGunFailureIcon']
        }
        if self.showMainGun:
            dynamic = config.data['mainGun']['dynamic']
            if dynamic:
                if self.totals[3] and self.totals[4] > self.totals[3]:
                    self.totals[3] = self.totals[4]
                    self.totals[2] = True
                self.totals[1] = max(max(self.totals[0], self.totals[3]) - self.totals[4], 0)
            mainGunAchived = dynamic and not self.totals[1] and self.totals[2]
            if mainGunAchived:
                macros['mainGun'] = ''
            elif not self.totals[2] and dynamic:
                macros['mainGun'] = ''
            else:
                macros['mainGun'] = self.recipes('%d' % self.totals[int(dynamic)])
            macros['mainGunDoneIcon'] = config.data['mainGun']['mainGunDoneIcon'] if mainGunAchived else ''
            macros['mainGunFailureIcon'] = config.data['mainGun']['mainGunFailureIcon'] if not self.totals[2] and dynamic else ''
        self.mainGunText = config.data['mainGun']['format'].format(**macros)
        if g_flash is not None:
            g_flash.addText(config.data['format'].format(mainGun=mainGuns.mainGunText))
            optimization.stopCallback(self.updateMainGun)
        else:
            optimization.delayCallback(0.2, self.updateMainGun)


class SysClass(object):
    def __init__(self):
        self.health = dict()
        self.vehicles = dict()
        self.guiType = 0
        self.playerID = None
        self.enemyTeam = None
        self._health = [0, 0, 0, 0]

    def battleLoading(self):
        player = BigWorld.player()
        self.guiType = player.arena.guiType
        self.playerID = player.playerVehicleID
        self.enemyTeam = player.guiSessionProvider.getArenaDP().getEnemyTeams()[0]
        player.onVehicleEnterWorld += self._onEnterWorld
        player.arena.onVehicleKilled += self._onVehicleKilled
        player.arena.onVehicleAdded += self._onVehicleUpdate
        player.arena.onVehicleUpdated += self._onVehicleUpdate
        self.tanklistsCreate()
        mainGuns.battleLoading()

    def destroyBattle(self):
        self.__init__()
        mainGuns.__init__()
        optimization.destroy()
        player = BigWorld.player()
        player.onVehicleEnterWorld -= self._onEnterWorld
        player.arena.onVehicleKilled -= self._onVehicleKilled
        player.arena.onVehicleAdded -= self._onVehicleUpdate
        player.arena.onVehicleUpdated -= self._onVehicleUpdate

    def tanklistsCreate(self):
        collection = vos_collections.VehiclesInfoCollection().iterator(BigWorld.player().guiSessionProvider.getArenaDP())
        for vInfoVO in collection:
            maxHealth = vInfoVO.vehicleType.maxHealth
            if not vInfoVO or not maxHealth or not vInfoVO.vehicleType or not vInfoVO.vehicleType.classTag:
                continue
            if vInfoVO.vehicleID in self.vehicles:
                return None
            health = maxHealth if vInfoVO.isAlive() else 0
            self.vehicles.setdefault(vInfoVO.vehicleID, [health, maxHealth, vInfoVO.team, vInfoVO.vehicleType.classTag])
            if vInfoVO.team == BigWorld.player().team:
                self._health[1] += health
                self._health[3] += health
            else:
                self._health[0] += health
                self._health[2] += health

            hDic = self.health.setdefault(vInfoVO.team, [0, 0])
            hDic[0] += health
            hDic[1] += maxHealth

    def updateHealthPoints(self, damage, team):
        self.health[team][0] -= damage
        health = self.health[team][0]
        self._health[1 if team == BigWorld.player().team else 0] -= damage
        if self._health[1 if team == BigWorld.player().team else 0] <= 0:
            self._health[1 if team == BigWorld.player().team else 0] = 0
        if mainGuns.showMainGun and config.data['mainGun']['dynamic'] and team == self.enemyTeam:
            if health and mainGuns.totals[2] and mainGuns.totals[1] and health < mainGuns.totals[1]:
                mainGuns.totals[2] = False
                mainGuns.updateMainGun()

    def onHealthChanged(self, vehicle, newHealth, _, attackerID, __):
        if self.guiType in [ARENA_GUI_TYPE.RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM]:
            target = self.vehicles.get(vehicle.id)
            attacker = self.vehicles.get(attackerID)
            if target and target[0] > 0:
                damage = target[0] - newHealth
                target[0] = newHealth
                self.updateHealthPoints(damage, target[2])
                mainGuns.playersDamage(attackerID, damage, target[2], attacker[2])

    def _onVehicleKilled(self, targetID, *_, **__):
        target = self.vehicles.get(targetID)
        if target and target[0] > 0:
            self.updateHealthPoints(target[0], target[2])
            target[0] = 0
        if self.playerID == targetID and mainGuns.showMainGun and config.data['mainGun']['dynamic'] and mainGuns.totals[1]:
            mainGuns.totals[2] = False
            mainGuns.updateMainGun()

    def _onVehicleUpdate(self, tid):
        vInfoVO = BigWorld.player().guiSessionProvider.getArenaDP().getVehicleInfo(tid)
        maxHealth = vInfoVO.vehicleType.maxHealth
        if not vInfoVO or not maxHealth or not vInfoVO.vehicleType or not vInfoVO.vehicleType.classTag:
            return
        if tid in self.vehicles:
            return None
        health = maxHealth if vInfoVO.isAlive() else 0
        self.vehicles.setdefault(tid, [health, maxHealth, vInfoVO.team, vInfoVO.vehicleType.classTag])
        if vInfoVO.team == BigWorld.player().team:
            self._health[1] += health
        else:
            self._health[0] += health
        hDic = self.health.setdefault(vInfoVO.team, [0, 0])
        hDic[0] += health
        hDic[1] += maxHealth

    def _onEnterWorld(self, vehicle):
        target = self.vehicles.get(vehicle.id)
        newHealth = max(0, vehicle.health)
        if target and target[0] != newHealth and vehicle.isAlive():
            self.updateHealthPoints(target[0] - newHealth, target[2])
            target[0] = newHealth


@override(RibbonsAggregator, '_onPlayerFeedbackReceived')
def new__onPlayerFeedbackReceived(func, self, events):
    func(self, events)
    if not config.data['enabled']:
        return
    mainGuns.onPlayerFeedbackReceived(events)


@override(Vehicle, 'onHealthChanged')
def new__onHealthChanged(func, self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
    func(self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs)
    if not config.data['enabled']:
        return
    scl.onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID)


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(func, *args):
    func(*args)
    if not config.data['enabled']:
        return
    scl.battleLoading()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new__destroyGUI(func, *args):
    func(*args)
    if not config.data['enabled']:
        return
    scl.destroyBattle()


# Initialize the mod
optimization = Optimization()
mainGuns = MainGun()
scl = SysClass()
