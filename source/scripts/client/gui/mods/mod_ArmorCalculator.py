# -*- coding: utf-8 -*-
from collections import defaultdict, namedtuple

from AvatarInputHandler.gun_marker_ctrl import _CrosshairShotResults
from DestructibleEntity import DestructibleEntity
from Vehicle import Vehicle
from aih_constants import CTRL_MODE_NAME, SHOT_RESULT
from constants import ARENA_BONUS_TYPE, SHELL_MECHANICS_TYPE, SHELL_TYPES
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
from items.components import component_constants
from items.components.component_constants import DEFAULT_PIERCING_POWER_RANDOMIZATION
from items.components.component_constants import MODERN_HE_PIERCING_POWER_REDUCTION_FACTOR_FOR_SHIELDS
from items.tankmen import getSkillsConfig
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, logDebug, calculate_version
from DriftkingsInject import DriftkingsInjector, ArmorCalculatorMeta, g_events

AS_INJECTOR = 'ArmorCalculatorInjector'
AS_BATTLE = 'ArmorCalculatorView'
AS_SWF = 'ArmorCalculator.swf'

# Constants
MinMax = namedtuple("MinMax", ("min", "max"))
DEFAULT_RANDOMIZATION = MinMax(1.0 - DEFAULT_PIERCING_POWER_RANDOMIZATION, 1.0 + DEFAULT_PIERCING_POWER_RANDOMIZATION)
UNDEFINED_RESULT = (SHOT_RESULT.UNDEFINED, None, None, None, False, False)
FULL_PP_RANGE = (SHELL_TYPES.HIGH_EXPLOSIVE, SHELL_TYPES.HOLLOW_CHARGE)
GUNNER_ARMORER = 'gunner_armorer'
LOADER_AMMUNITION_IMPROVE = 'loader_ammunitionImprove'


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.2.0 (%(file_compile_date)s)'
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


def _updateRandomization(vehicle):
    randomization = component_constants.DEFAULT_PIERCING_POWER_RANDOMIZATION
    if config.data['enabled'] and vehicle is not None and vehicle.isCrewFull:
        for _, tman in vehicle.crew:
            if tman and GUNNER_ARMORER in tman.skillsMap and tman.canUseSkillsInCurrentVehicle:
                level = tman.skillsMap[GUNNER_ARMORER].level * tman.skillsEfficiency * (tman.nativeTankRealRoleLevel / 100.0)
                randomization += (0.2 - randomization) * (level - randomization) / 100
                logDebug(config.ID, True, 'PIERCING_POWER_RANDOMIZATION level: {}, randomization: {}', level, randomization)
                break
    _ShotResult.RANDOMIZATION = randomization


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
        prebattleCtrl = self.sessionProvider.dynamic.prebattleSetup
        if prebattleCtrl is not None:
            prebattleCtrl.onVehicleChanged += self.__updateCurrVehicleInfo
            prebattleCtrl.onBattleStarted += self.__updateCurrVehicleInfo

    def _dispose(self):
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged -= self.as_onCrosshairPositionChangedS
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, "onCameraChanged"):
            handler.onCameraChanged -= self.onCameraChanged
        g_events.onArmorChanged -= self.onArmorChanged
        g_events.onMarkerColorChanged -= self.onMarkerColorChanged
        prebattleCtrl = self.sessionProvider.dynamic.prebattleSetup
        if prebattleCtrl is not None:
            prebattleCtrl.onVehicleChanged -= self.__updateCurrVehicleInfo
            prebattleCtrl.onBattleStarted -= self.__updateCurrVehicleInfo
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
        if data[1] is None:
            return self.as_armorCalculatorS('')

        armor, piercingPower, caliber, ricochet, noDamage = data[1:]
        self.calcMacro['ricochet'] = config.i18n['UI_ricochet'] if ricochet else ''
        self.calcMacro['noDamage'] = config.i18n['UI_noDamage'] if noDamage else ''
        self.calcMacro['countedArmor'] = armor
        self.calcMacro['piercingPower'] = piercingPower
        self.calcMacro['piercingReserve'] = piercingPower - armor
        self.calcMacro['caliber'] = caliber
        self.as_armorCalculatorS(config.data['template'] % self.calcMacro)

    def __updateCurrVehicleInfo(self, vehicle=None):
        ctrl = self.sessionProvider.dynamic.prebattleSetup
        if ctrl is None:
            return
        if vehicle is None:
            vehicle = ctrl.getCurrentGUIVehicle()
        if vehicle is not None and not avatar_getter.isObserver():
            isComp7Battle = self.sessionProvider.arenaVisitor.getArenaBonusType() == ARENA_BONUS_TYPE.COMP7
            Randomizer._updateRandomization(vehicle, isComp7=isComp7Battle)


class ArmorCalculatorAllies(object):
    @staticmethod
    def isAlly(entity, player, onAlly):
        return False if onAlly else entity.publicInfo['team'] == player.team

    @classmethod
    def getShotResult(cls, hitPoint, collision, direction, piercingMultiplier, onAlly):
        if collision is None:
            return UNDEFINED_RESULT
        entity = collision.entity
        if not isinstance(entity, (Vehicle, DestructibleEntity)) or not entity.isAlive():
            return UNDEFINED_RESULT
        player = getPlayer()
        if player is None or cls.isAlly(entity, player, onAlly):
            return UNDEFINED_RESULT
        c_details = _CrosshairShotResults._getAllCollisionDetails(hitPoint, direction, entity)
        if c_details is None:
            return UNDEFINED_RESULT
        shot = player.getVehicleDescriptor().shot
        shell = shot.shell
        distance = player.position.flatDistTo(hitPoint)
        if shot.shell.kind in FULL_PP_RANGE:
            full_piercing_power = shot.piercingPower[0] * piercingMultiplier
        else:
            full_piercing_power = _CrosshairShotResults._computePiercingPowerAtDist(
                shot.piercingPower, distance, shot.maxDistance, piercingMultiplier)
        is_modern = cls.isModernMechanics(shell)
        armor, piercing_power, ricochet, no_damage = cls.computeArmor(c_details, shell, full_piercing_power, is_modern)
        if no_damage or ricochet:
            shot_result = SHOT_RESULT.NOT_PIERCED
        else:
            offset = piercing_power * shell.piercingPowerRandomization
            if armor < piercing_power - offset:
                shot_result = SHOT_RESULT.GREAT_PIERCED
            elif armor > piercing_power + offset:
                shot_result = SHOT_RESULT.NOT_PIERCED
            else:
                shot_result = SHOT_RESULT.LITTLE_PIERCED
        if is_modern:
            piercing_power = full_piercing_power
        return shot_result, armor, piercing_power, shell.caliber, ricochet, no_damage

    @staticmethod
    def isModernMechanics(shell):
        return (shell.kind == SHELL_TYPES.HIGH_EXPLOSIVE and shell.type.mechanics == SHELL_MECHANICS_TYPE.MODERN and shell.type.shieldPenetration)

    @staticmethod
    def computeArmor(c_details, shell, piercing_power, is_modern_he):
        computed_armor = 0
        ricochet = False
        no_damage = True
        is_jet = False
        jet_start_dist = 0
        jet_loss = _CrosshairShotResults._SHELL_EXTRA_DATA[shell.kind].jetLossPPByDist
        ignoredMaterials = set()
        for detail in c_details:
            mat_info = detail.matInfo
            if mat_info is None or (detail.compName, mat_info.kind) in ignoredMaterials:
                continue
            hitAngleCos = detail.hitAngleCos if mat_info.useHitAngle else 1.0
            computed_armor += _CrosshairShotResults._computePenetrationArmor(shell, hitAngleCos, mat_info)
            if is_jet:
                jetDist = detail.dist - jet_start_dist
                if jetDist > 0:
                    piercing_power *= 1.0 - jetDist * jet_loss
            else:
                ricochet = _CrosshairShotResults._shouldRicochet(shell, hitAngleCos, mat_info)
            if mat_info.vehicleDamageFactor:
                no_damage = False
                break
            elif is_modern_he:
                piercing_power -= computed_armor * MODERN_HE_PIERCING_POWER_REDUCTION_FACTOR_FOR_SHIELDS
            elif jet_loss > 0:
                is_jet = True
                jet_start_dist += detail.dist + mat_info.armor * 0.001
            if mat_info.collideOnceOnly:
                ignoredMaterials.add((detail.compName, mat_info.kind))
        return computed_armor, piercing_power, ricochet, no_damage


g_mod = ArmorCalculatorAllies()


class _ShotResult(object):
    RANDOMIZATION = component_constants.DEFAULT_PIERCING_POWER_RANDOMIZATION
    UNDEFINED_RESULT = (SHOT_RESULT.UNDEFINED, None, None, None, False, False)
    _JET_FACTOR = 0.001
    FULL_PP_RANGE = (SHELL_TYPES.HIGH_EXPLOSIVE, SHELL_TYPES.HOLLOW_CHARGE)

    @staticmethod
    def isAlly(entity, player, onAlly):
        return False if onAlly else entity.publicInfo['team'] == player.team

    @classmethod
    def getShotResult(cls, hitPoint, collision, direction, piercingMultiplier, onAlly, player):
        if player is None or collision is None:
            return cls.UNDEFINED_RESULT
        entity = collision.entity
        if not isinstance(entity, (Vehicle, DestructibleEntity)) or not entity.isAlive() or cls.isAlly(entity, player, onAlly):
            return cls.UNDEFINED_RESULT
        c_details = _CrosshairShotResults._getAllCollisionDetails(hitPoint, direction, entity)
        if c_details is None:
            return cls.UNDEFINED_RESULT
        shot = player.getVehicleDescriptor().shot
        shell = shot.shell
        distance = player.position.flatDistTo(hitPoint)
        is_modern = cls.isModernMechanics(shell)
        if is_modern or shot.shell.kind in cls.FULL_PP_RANGE:
            piercing_power = shot.piercingPower[0] * piercingMultiplier
        else:
            piercing_power = _CrosshairShotResults._computePiercingPowerAtDist(shot.piercingPower, distance, shot.maxDistance, piercingMultiplier)
        return cls.computeArmorHE(c_details, shell, piercing_power) if is_modern else cls.computeArmor(c_details, shell, piercing_power)

    @classmethod
    def _checkShotResult(cls, armor, piercing_power, ricochet, no_damage):
        if no_damage or ricochet:
            return SHOT_RESULT.NOT_PIERCED
        if isinstance(cls.RANDOMIZATION, MinMax):
            min_pp = piercing_power * cls.RANDOMIZATION.min
            max_pp = piercing_power * cls.RANDOMIZATION.max
            if armor < min_pp:
                return SHOT_RESULT.GREAT_PIERCED
            elif armor > max_pp:
                return SHOT_RESULT.NOT_PIERCED
            else:
                return SHOT_RESULT.LITTLE_PIERCED
        else:
            offset = piercing_power * cls.RANDOMIZATION
            if armor < piercing_power - offset:
                return SHOT_RESULT.GREAT_PIERCED
            elif armor > piercing_power + offset:
                return SHOT_RESULT.NOT_PIERCED
            else:
                return SHOT_RESULT.LITTLE_PIERCED

    @staticmethod
    def isModernMechanics(shell):
        return (shell.kind == SHELL_TYPES.HIGH_EXPLOSIVE and shell.type.mechanics == SHELL_MECHANICS_TYPE.MODERN)

    @classmethod
    def computeArmor(cls, c_details, shell, piercing_power):
        computed_armor = 0
        ricochet = False
        no_damage = True
        is_jet = False
        jet_start_dist = 0
        jet_loss = _CrosshairShotResults._SHELL_EXTRA_DATA[shell.kind].jetLossPPByDist
        ignoredMaterials = set()
        for detail in c_details:
            mat_info = detail.matInfo
            if mat_info is None or (detail.compName, mat_info.kind) in ignoredMaterials:
                continue
            hitAngleCos = detail.hitAngleCos if mat_info.useHitAngle else 1.0
            computed_armor += _CrosshairShotResults._computePenetrationArmor(shell, hitAngleCos, mat_info)
            if is_jet:
                jetDist = detail.dist - jet_start_dist
                if jetDist > 0:
                    piercing_power *= 1.0 - jetDist * jet_loss
            else:
                ricochet = _CrosshairShotResults._shouldRicochet(shell, hitAngleCos, mat_info)
            if mat_info.vehicleDamageFactor:
                no_damage = False
                break
            if jet_loss > 0:
                is_jet = True
                jet_start_dist += detail.dist + mat_info.armor * cls._JET_FACTOR
            if mat_info.collideOnceOnly:
                ignoredMaterials.add((detail.compName, mat_info.kind))
        shot_result = cls._checkShotResult(computed_armor, piercing_power, ricochet, no_damage)
        return shot_result, computed_armor, piercing_power, shell.caliber, ricochet, no_damage

    @classmethod
    def computeArmorHE(cls, c_details, shell, piercing_power):
        computed_armor = 0
        ignoredMaterials = set()
        no_damage = True
        for detail in c_details:
            mat_info = detail.matInfo
            if mat_info is None or (detail.compName, mat_info.kind) in ignoredMaterials:
                continue
            hitAngleCos = detail.hitAngleCos if mat_info.useHitAngle else 1.0
            armor = _CrosshairShotResults._computePenetrationArmor(shell, hitAngleCos, mat_info)
            computed_armor += armor
            if mat_info.vehicleDamageFactor:
                no_damage = False
                break
            if shell.type.shieldPenetration:
                piercing_power -= armor * MODERN_HE_PIERCING_POWER_REDUCTION_FACTOR_FOR_SHIELDS
            if mat_info.collideOnceOnly:
                ignoredMaterials.add((detail.compName, mat_info.kind))
        shot_result = cls._checkShotResult(computed_armor, max(piercing_power, 0), False, no_damage)
        return shot_result, computed_armor, max(piercing_power, 0), shell.caliber, False, no_damage


class ShotResultIndicatorPlugin(plugins.ShotResultIndicatorPlugin):
    def __init__(self, parentObj):
        super(ShotResultIndicatorPlugin, self).__init__(parentObj)
        self.__onAlly = bool(config.data['displayOnAllies'])
        self.__player = getPlayer()

    def __updateColor(self, markerType, hitPoint, collision, direction):
        result = _ShotResult.getShotResult(hitPoint, collision, direction, self.__piercingMultiplier, self.__onAlly, self.__player)
        shot_result, data = result[0], result[1:]
        if shot_result in self.__colors:
            color = self.__colors[shot_result]
            if self.__cache[markerType] != shot_result and self._parentObj.setGunMarkerColor(markerType, color):
                self.__cache[markerType] = shot_result
                g_events.onMarkerColorChanged(color)
            g_events.onArmorChanged(result)

    def __setMapping(self, keys):
        super(ShotResultIndicatorPlugin, self).__setMapping(keys)
        self.__mapping[CROSSHAIR_VIEW_ID.STRATEGIC] = True

    def start(self):
        super(ShotResultIndicatorPlugin, self).start()
        prebattleCtrl = self.sessionProvider.dynamic.prebattleSetup
        if prebattleCtrl is not None:
            prebattleCtrl.onVehicleChanged += self.__updateCurrVehicleInfo

    def stop(self):
        super(ShotResultIndicatorPlugin, self).stop()
        prebattleCtrl = self.sessionProvider.dynamic.prebattleSetup
        if prebattleCtrl is not None:
            prebattleCtrl.onVehicleChanged -= self.__updateCurrVehicleInfo

    def __updateCurrVehicleInfo(self, vehicle):
        if avatar_getter.isObserver(self.__player) or vehicle is None:
            return
        isComp7Battle = self.sessionProvider.arenaVisitor.getArenaBonusType() == ARENA_BONUS_TYPE.COMP7
        Randomizer._updateRandomization(vehicle, isComp7=isComp7Battle)


class Randomizer(object):
    GUNNER_ARMORER = 'gunner_armorer'
    LOADER_AMMUNITION_IMPROVE = 'loader_ammunitionImprove'
    RND_MIN_MAX_DEBUG = 'PIERCING_POWER_RANDOMIZATION: {}, vehicle: {}'
    RND_SKILL_DIFF_DEBUG = "PIERCING_POWER_RANDOMIZATION: skill_name: {} skill_lvl: {} level_increase: {} percent: {}"
    PIERCING_DISTRIBUTION_BOUND = {}

    @classmethod
    def getBaseSkillPercent(cls, skill_name):
        percent = cls.PIERCING_DISTRIBUTION_BOUND.get(skill_name, 0)
        if not percent:
            skill = getSkillsConfig().getSkill(skill_name)
            if skill and skill.uiSettings:
                for name, descr in skill.uiSettings.descrArgs:
                    if name == KPI.Name.DAMAGE_AND_PIERCING_DISTRIBUTION_LOWER_BOUND:
                        percent = cls.PIERCING_DISTRIBUTION_BOUND[skill_name] = round(descr.value, 4)
                        break
        return percent

    @classmethod
    def getCurrentSkillEfficiency(cls, tman, skill_name):
        skill = tman.skillsMap.get(skill_name)
        if skill is None:
            return 0
        level_increase, _ = tman.crewLevelIncrease
        result = (skill.level + level_increase) * tman.skillsEfficiency * cls.getBaseSkillPercent(skill_name)
        logDebug(cls.RND_SKILL_DIFF_DEBUG, skill_name, skill.level, level_increase, result)
        return result

    @classmethod
    def _updateRandomization(cls, vehicle, isComp7=False):
        randomization_min, randomization_max = (0.85, 1.15) if isComp7 else DEFAULT_RANDOMIZATION

        if config.data['enabled'] and vehicle is not None:
            data = {cls.GUNNER_ARMORER: [], cls.LOADER_AMMUNITION_IMPROVE: []}
            for _, tman in vehicle.crew:
                if not tman or not tman.canUseSkillsInCurrentVehicle:
                    continue
                possible_skills = tman.getPossibleSkills().intersection(data.keys())
                for skill_name in possible_skills:
                    data[skill_name].append(cls.getCurrentSkillEfficiency(tman, skill_name))
            for skill_name, values in data.iteritems():
                if values:
                    percent = sum(values) / len(values)
                    randomization_min += percent
                    if skill_name == cls.GUNNER_ARMORER:
                        randomization_max -= percent
        _ShotResult.RANDOMIZATION = MinMax(round(randomization_min, 4), round(randomization_max, 4))
        logDebug(cls.RND_MIN_MAX_DEBUG, _ShotResult.RANDOMIZATION, vehicle.userName)


@override(plugins, 'createPlugins')
def createPlugins(func, *args):
    _plugins = func(*args)
    if config.data['enabled']:
        _plugins['shotResultIndicator'] = ShotResultIndicatorPlugin
    return _plugins


def init():
    g_events.onVehicleChangedDelayed += Randomizer._updateRandomization
    g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
    g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, ArmorCalculator, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))


def fini():
    g_events.onVehicleChangedDelayed -= Randomizer._updateRandomization
