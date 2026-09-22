# -*- coding: utf-8 -*-
from collections import defaultdict, namedtuple

from AvatarInputHandler.gun_marker_ctrl import _CrosshairShotResults, computePiercingPowerAtDist
from DestructibleEntity import DestructibleEntity
from Vehicle import Vehicle
from account_helpers.settings_core.settings_constants import GRAPHICS
from aih_constants import CTRL_MODE_NAME, SHOT_RESULT
from constants import SHELL_MECHANICS_TYPE, SHELL_TYPES
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.battle.shared.crosshair import plugins
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.CROSSHAIR_VIEW_ID import CROSSHAIR_VIEW_ID
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control import avatar_getter
from gui.shared.gui_items import KPI
from gui.shared.personality import ServicesLocator
from helpers import dependency
from items.tankmen import getSkillsConfig
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, logDebug, calculate_version
from DriftkingsInject import DriftkingsInjector, ArmorCalculatorMeta, g_events

AS_INJECTOR = 'ArmorCalculatorInjector'
AS_BATTLE = 'ArmorCalculatorView'
AS_SWF = 'ArmorCalculator.swf'

# Constants
MinMax = namedtuple('MinMax', ('min', 'max'))
DEFAULT_RANDOMIZATION = MinMax(0.75, 1.25)
UNDEFINED_RESULT = (SHOT_RESULT.UNDEFINED, None, None, None, False, False)
FULL_PP_RANGE = (SHELL_TYPES.HIGH_EXPLOSIVE, SHELL_TYPES.HOLLOW_CHARGE)


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.3.2 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'displayOnAllies': False,
            'messages': {
                'green': '<font size=\'20\' color=\'#66FF33\'>Breaking through.</font>',
                'normal': 'Easy To Penetrate :)',
                'orange': '<font size=\'20\' color=\'#FF9900\'>Switch to Gold.</font>',
                'purple': '<font size=\'20\' color=\'#6F6CD3\'>Your time has come.</font>',
                'red': '<font size=\'20\' color=\'#FF0000\'>Try hard, your time has come.</font>',
                'yellow': '<font size=\'20\' color=\'#FAF829\'>Switch to Gold.</font>'
            },
            'position': {
                'x': 0,
                'y': 40
            },
            'template': '<p align=\'center\'>%(ricochet)s %(noDamage)s<br><font color=\'%(color)s\'>%(countedArmor)d | %(piercingPower)d</font></p>'
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_displayOnAllies_text': 'Display On Allies',
            'UI_setting_displayOnAllies_tooltip': '',
            'UI_noDamage': 'Critical Hit, No Damage.',
            'UI_ricochet': 'Ricochet',
            'UI_colors': {
                'green': '#60CB00',
                'orange': '#FF9900',
                'purple': '#6F6CD3',
                'red': '#ED070A',
                'yellow': '#FFC900'
            }
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('displayOnAllies'),
            ],
            'column2': []
        }

    def onBattleLoaded(self):
        if not self.data['enabled']:
            return
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)
_isInitialized = False


class ArmorCalculator(ArmorCalculatorMeta):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        super(ArmorCalculator, self).__init__(config.ID)
        self.calcMacro = defaultdict(lambda: 'macros not found')

    def getSettings(self):
        return config.data

    def _populate(self):
        super(ArmorCalculator, self)._populate()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged += self.as_onCrosshairPositionChangedS
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, "onCameraChanged"):
            handler.onCameraChanged += self.onCameraChanged
        g_events.onArmorChanged += self.onArmorChanged
        g_events.onMarkerColorChanged += self.onMarkerColorChanged

    def _dispose(self):
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged -= self.as_onCrosshairPositionChangedS
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, "onCameraChanged"):
            handler.onCameraChanged -= self.onCameraChanged
        g_events.onArmorChanged -= self.onArmorChanged
        g_events.onMarkerColorChanged -= self.onMarkerColorChanged
        super(ArmorCalculator, self)._dispose()

    def onMarkerColorChanged(self, color):
        self.calcMacro['color'] = config.i18n['UI_colors'].get(color, '#FFD700')
        self.calcMacro['message'] = config.data['messages'].get(color, '')

    def onCameraChanged(self, ctrlMode, *_, **__):
        _CTRL_MODE = {CTRL_MODE_NAME.KILL_CAM, CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM,
                      CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION, CTRL_MODE_NAME.LOOK_AT_KILLER}
        if ctrlMode in _CTRL_MODE:
            self.as_armorCalculatorS('')

    def onArmorChanged(self, data):
        if data is None:
            return self.as_armorCalculatorS('')
        armor, piercingPower, caliber, ricochet, noDamage = data
        self.calcMacro['ricochet'] = config.i18n['UI_ricochet'] if ricochet else ''
        self.calcMacro['noDamage'] = config.i18n['UI_noDamage'] if noDamage else ''
        self.calcMacro['countedArmor'] = armor
        self.calcMacro['piercingPower'] = piercingPower
        self.calcMacro['piercingReserve'] = piercingPower - armor
        self.calcMacro['caliber'] = caliber
        self.as_armorCalculatorS(config.data['template'] % self.calcMacro)


class _ShotResult(_CrosshairShotResults):
    RANDOMIZATION = DEFAULT_RANDOMIZATION
    UNDEFINED_RESULT = (SHOT_RESULT.UNDEFINED, None)
    ENTITY_TYPES = (Vehicle, DestructibleEntity)
    JET_FACTOR = 0.001
    PP_REDUCTION_FACTOR = 3.0

    @classmethod
    def _isDestructibleComponent(cls, entity, componentID):
        return entity.isDestructibleComponent(componentID) if isinstance(entity, DestructibleEntity) else True

    @classmethod
    def _getShotResult(cls, gunMarker, multiplier, player):
        if player is None or gunMarker.collData is None:
            return cls.UNDEFINED_RESULT
        entity = gunMarker.collData.entity
        if not isinstance(entity, cls.ENTITY_TYPES) or not entity.isAlive() or entity.publicInfo['team'] == player.team:
            return cls.UNDEFINED_RESULT
        return cls._result(gunMarker, multiplier, player)

    @classmethod
    def _result(cls, gunMarker, multiplier, player):
        collision_details = cls._getAllCollisionDetails(gunMarker.position, gunMarker.direction, gunMarker.collData.entity)
        if collision_details is None:
            return cls.UNDEFINED_RESULT
        vDesc = player.getVehicleDescriptor()
        gunInstallationSlot = vDesc.gunInstallations[gunMarker.gunInstallationIndex]
        shot = vDesc.shot if gunInstallationSlot.isMainInstallation() else gunInstallationSlot.gun.shots[0]
        shell = shot.shell
        distance = player.position.flatDistTo(gunMarker.position)
        piercing_power = computePiercingPowerAtDist(shot.piercingPower, distance, shot.maxDistance, multiplier)
        if cls._isModernMechanics(shell):
            return cls._computeArmorModernHE(collision_details, shell, piercing_power, gunMarker.collData.entity)
        else:
            return cls._computeArmorDefault(collision_details, shell, piercing_power, gunMarker.collData.entity)

    @classmethod
    def _checkShotResult(cls, data):
        armor, piercing_power, _, ricochet, no_damage = data
        if no_damage or ricochet:
            return SHOT_RESULT.UNDEFINED
        elif armor < piercing_power * cls.RANDOMIZATION.min:
            return SHOT_RESULT.GREAT_PIERCED
        elif armor > piercing_power * cls.RANDOMIZATION.max:
            return SHOT_RESULT.NOT_PIERCED
        else:
            return SHOT_RESULT.LITTLE_PIERCED

    @staticmethod
    def _isModernMechanics(shell):
        return shell.kind == SHELL_TYPES.HIGH_EXPLOSIVE and shell.type.mechanics == SHELL_MECHANICS_TYPE.MODERN

    @classmethod
    def _computeArmorDefault(cls, collision_details, shell, full_piercing_power, entity):
        armor = 0
        piercing_power = full_piercing_power
        ignored_materials = set()
        isJet = False
        jet_loss = shell.type.piercingPowerLossFactorByDistance if cls._SHELL_EXTRA_DATA[shell.kind].hasPenetrationLoss else 0.0
        jet_start_dist = 0.0
        no_damage = True
        ricochet = False

        for detail in collision_details:
            if not cls._isDestructibleComponent(entity, detail.compName):
                continue
            mat_info = detail.matInfo
            if not mat_info or (detail.compName, mat_info.kind) in ignored_materials:
                continue
            hitAngleCos = detail.hitAngleCos if mat_info.useHitAngle else 1.0
            if isJet:
                jetDist = detail.dist - jet_start_dist
                if jetDist > 0.0:
                    piercing_power *= 1.0 - jetDist * jet_loss
            else:
                ricochet = cls._shouldRicochet(shell, hitAngleCos, mat_info)
                if ricochet:
                    break
            armor += cls._computePenetrationArmor(shell, hitAngleCos, mat_info)
            if mat_info.vehicleDamageFactor:
                no_damage = False
                break
            if jet_loss > 0.0:
                isJet = True
                jet_start_dist = detail.dist + mat_info.armor * cls.JET_FACTOR
            if mat_info.collideOnceOnly:
                ignored_materials.add((detail.compName, mat_info.kind))
        data = (int(armor), int(piercing_power), int(shell.caliber), ricochet, no_damage)
        return cls._checkShotResult(data), data

    @classmethod
    def _computeArmorModernHE(cls, collision_details, shell, piercing_power, entity):
        armor = 0
        ignored_materials = set()
        no_damage = True

        for detail in collision_details:
            if not cls._isDestructibleComponent(entity, detail.compName):
                continue
            mat_info = detail.matInfo
            if not mat_info or (detail.compName, mat_info.kind) in ignored_materials:
                continue
            hitAngleCos = detail.hitAngleCos if mat_info.useHitAngle else 1.0
            armor += cls._computePenetrationArmor(shell, hitAngleCos, mat_info)
            if mat_info.vehicleDamageFactor:
                no_damage = False
                break
            if shell.type.shieldPenetration:
                piercing_power = max(0, piercing_power - armor * cls.PP_REDUCTION_FACTOR)
            if mat_info.collideOnceOnly:
                ignored_materials.add((detail.compName, mat_info.kind))
        data = (int(armor), int(piercing_power), int(shell.caliber), False, no_damage)
        return cls._checkShotResult(data), data


class _ShotResultAll(_ShotResult):

    @classmethod
    def _getShotResult(cls, gunMarker, multiplier, player):
        collision = gunMarker.collData
        if player is None or collision is None or not isinstance(collision.entity, cls.ENTITY_TYPES) or not collision.entity.isAlive():
            return cls.UNDEFINED_RESULT
        return cls._result(gunMarker, multiplier, player)


class ShotResultIndicatorPlugin(plugins.ShotResultIndicatorPlugin):

    def __init__(self, parentObj):
        super(ShotResultIndicatorPlugin, self).__init__(parentObj)
        self.__player = getPlayer()
        self.__data = None
        self.__resolver = _ShotResultAll if config.data['displayOnAllies'] else _ShotResult

    def __onGunMarkerStateChanged(self, markerType, gunMarkerState, supportMarkersInfo):
        if not self.__isEnabled:
            return
        shot_result, data = self.__resolver._getShotResult(gunMarkerState, self.__piercingMultiplier, self.__player)
        if shot_result in self.__colors:
            color = self.__colors[shot_result]
            if self.__cache[markerType] != shot_result and self._parentObj.setGunMarkerColor(markerType, color):
                self.__cache[markerType] = shot_result
                g_events.onMarkerColorChanged(color)
            if self.__data != data:
                self.__data = data
                g_events.onArmorChanged(data)

    def __setMapping(self, keys):
        super(ShotResultIndicatorPlugin, self).__setMapping(keys)
        self.__mapping[CROSSHAIR_VIEW_ID.STRATEGIC] = True

    def start(self):
        super(ShotResultIndicatorPlugin, self).start()
        self.__player = getPlayer()
        prebattleCtrl = self.sessionProvider.dynamic.prebattleSetup
        if prebattleCtrl is not None:
            prebattleCtrl.onVehicleChanged += self.__updateCurrVehicleInfo

    def stop(self):
        super(ShotResultIndicatorPlugin, self).stop()
        prebattleCtrl = self.sessionProvider.dynamic.prebattleSetup
        if prebattleCtrl is not None:
            prebattleCtrl.onVehicleChanged -= self.__updateCurrVehicleInfo

    def __updateCurrVehicleInfo(self, vehicle):
        if not avatar_getter.isObserver(self.__player) and vehicle is not None:
            Randomizer._updateRandomization(vehicle)


@override(plugins, 'createPlugins')
def createPlugins(func, *args):
    _plugins = func(*args)
    if config.data['enabled']:
        _plugins['shotResultIndicator'] = ShotResultIndicatorPlugin
    return _plugins


class Randomizer(object):
    GUNNER_ARMORER = 'gunner_armorer'
    LOADER_AMMUNITION_IMPROVE = 'loader_ammunitionImprove'
    RND_MIN_MAX_DEBUG = 'PIERCING_POWER_RANDOMIZATION: {}, vehicle: {}'
    RND_SKILL_DIFF_DEBUG = 'PIERCING_POWER_RANDOMIZATION: skill_name: {} skill_lvl: {} level_increase: {} percent: {}'
    RND_SET_PIERCING_DISTRIBUTION_BOUND_DEBUG = 'PIERCING_POWER_RANDOMIZATION: skill_name {}, percent {}'

    PIERCING_DISTRIBUTION_BOUND = {}

    @classmethod
    def getBaseSkillPercent(cls, skill_name):
        percent = cls.PIERCING_DISTRIBUTION_BOUND.get(skill_name, 0)
        if not percent:
            descrArgs = getSkillsConfig().getSkill(skill_name).uiSettings.descrArgs
            for name, descr in descrArgs:
                if name == KPI.Name.DAMAGE_AND_PIERCING_DISTRIBUTION_LOWER_BOUND:
                    percent = cls.PIERCING_DISTRIBUTION_BOUND[skill_name] = round(descr.value, 4)
                    logDebug(cls.RND_SET_PIERCING_DISTRIBUTION_BOUND_DEBUG, skill_name, percent)
                break
        return percent

    @classmethod
    def getCurrentSkillEfficiency(cls, tman, skill_name):
        skill = tman.skillsMap.get(skill_name)
        if skill is None:
            return 0
        level_increase, bonuses = tman.crewLevelIncrease
        result = (skill.level + level_increase) * tman.skillsEfficiency * cls.getBaseSkillPercent(skill_name)
        logDebug(cls.RND_SKILL_DIFF_DEBUG, skill_name, skill.level, level_increase, result)
        return result

    @classmethod
    def _updateRandomization(cls, vehicle):
        if vehicle is None or not config.data['enabled']:
            _ShotResult.RANDOMIZATION = DEFAULT_RANDOMIZATION
            return
        data = {cls.GUNNER_ARMORER: [], cls.LOADER_AMMUNITION_IMPROVE: []}
        for _, tman in vehicle.crew:
            if not tman or not tman.canUseSkillsInCurrentVehicle:
                continue
            for skill_name in tman.getPossibleSkills().intersection(data):
                data[skill_name].append(cls.getCurrentSkillEfficiency(tman, skill_name))
        randomization_min, randomization_max = DEFAULT_RANDOMIZATION
        for skill_name, value in data.items():
            if value:
                percent = sum(value) / len(value)
                randomization_min += percent
                if skill_name == cls.GUNNER_ARMORER:
                    randomization_max -= percent
        _ShotResult.RANDOMIZATION = MinMax(round(randomization_min, 4), round(randomization_max, 4))
        logDebug(config.ID, True, cls.RND_MIN_MAX_DEBUG, _ShotResult.RANDOMIZATION, vehicle.userName)


def init():
    global _isInitialized
    if _isInitialized:
        return
    g_events.onVehicleChangedDelayed += Randomizer._updateRandomization
    if g_entitiesFactories.getSettings(AS_INJECTOR) is None:
        g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
    if g_entitiesFactories.getSettings(AS_BATTLE) is None:
        g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, ArmorCalculator, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
    _isInitialized = True


def fini():
    global _isInitialized
    if not _isInitialized:
        return
    g_events.onVehicleChangedDelayed -= Randomizer._updateRandomization
    _isInitialized = False
