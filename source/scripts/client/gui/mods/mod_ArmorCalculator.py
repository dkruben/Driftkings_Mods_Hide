# -*- coding: utf-8 -*-
from collections import defaultdict

from AvatarInputHandler.gun_marker_ctrl import _CrosshairShotResults
from DestructibleEntity import DestructibleEntity
from Vehicle import Vehicle
from aih_constants import CTRL_MODE_NAME, SHOT_RESULT
from constants import SHELL_MECHANICS_TYPE, SHELL_TYPES as SHELLS, SHELL_TYPES
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.battle.shared.crosshair import plugins
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.DisposableEntity import EntityState
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.CROSSHAIR_VIEW_ID import CROSSHAIR_VIEW_ID
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control import avatar_getter
from gui.shared.personality import ServicesLocator
from helpers import dependency
from items.components.component_constants import MODERN_HE_PIERCING_POWER_REDUCTION_FACTOR_FOR_SHIELDS
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import SimpleConfigInterface, Analytics, override, getPlayer, logDebug, logException, g_events

AS_INJECTOR = 'ArmorCalculatorInjector'
AS_BATTLE = 'ArmorCalculatorView'
AS_SWF = 'ArmorCalculator.swf'

UNDEFINED_RESULT = (SHOT_RESULT.UNDEFINED, None, None, None, False, False)
FULL_PP_RANGE = (SHELLS.HIGH_EXPLOSIVE, SHELLS.HOLLOW_CHARGE)


class ConfigInterface(SimpleConfigInterface):

    def __init__(self):
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'displayOnAllies': False,
            'messages': {
                'green': '<font size=\'20\' color=\'#66FF33\'>Breaking through.</font>',
                'normal': 'Easy To Penetrate :P',
                'orange': '<font size=\'20\' color=\'#FF9900\'>Switch to Gold.</font>',
                'purple': '<font size=\'20\' color=\'#6F6CD3\'>Your time has come.</font>',
                'red': '<font size=\'20\' color=\'#FF0000\'>Try hard, your time has come.</font>',
                'yellow': '<font size=\'20\' color=\'#FAF829\'>Switch to Gold.</font>'
            },
            'position': {
                'x': 0,
                'y': 40
            },
            'template': '<p align=\'center\'>%(ricochet)s%(noDamage)s<br><font color=\'%(color)s\'>%(countedArmor)d | %(piercingPower)d</font></p>'
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_displayOnAllies_text': 'Display On Allies',
            'UI_setting_displayOnAllies_tooltip': '',
            'UI_noDamage': 'Critical hit, no damage.',
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


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class ArmorCalculatorInjector(View):

    def _populate(self):
        # noinspection PyProtectedMember
        super(ArmorCalculatorInjector, self)._populate()
        g_events.onBattleClosed += self.destroy

    def _dispose(self):
        g_events.onBattleClosed -= self.destroy
        # noinspection PyProtectedMember
        super(ArmorCalculatorInjector, self)._dispose()

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            return
        super(ArmorCalculatorInjector, self).destroy()


class ArmorCalculatorMeta(BaseDAAPIComponent):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        super(ArmorCalculatorMeta, self).__init__()

    def _populate(self):
        # noinspection PyProtectedMember
        super(ArmorCalculatorMeta, self)._populate()
        g_events.onBattleClosed += self.destroy
        logDebug(True, '\'%s\' is loaded' % config.ID)

    def _dispose(self):
        g_events.onBattleClosed -= self.destroy
        # noinspection PyProtectedMember
        super(ArmorCalculatorMeta, self)._dispose()
        logDebug(True, '\'%s\' is closed' % config.ID)

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            return
        super(ArmorCalculatorMeta, self).destroy()

    def as_startUpdateS(self, linkage):
        return self.flashObject.as_startUpdate(linkage) if self._isDAAPIInited() else None

    def as_onCrosshairPositionChangedS(self, x, y):
        return self.flashObject.as_onCrosshairPositionChanged(x, y) if self._isDAAPIInited() else None

    def as_armorCalculatorS(self, text):
        return self.flashObject.as_armorCalculator(text) if self._isDAAPIInited() else None


class ArmorCalculator(ArmorCalculatorMeta):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        super(ArmorCalculator, self).__init__()
        self.calcMacro = defaultdict(lambda: 'macros not found')

    def _populate(self):
        super(ArmorCalculator, self)._populate()
        self.as_startUpdateS(config.data)
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged += self.as_onCrosshairPositionChangedS
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
        g_events.onArmorChanged += self.onArmorChanged
        g_events.onMarkerColorChanged += self.onMarkerColorChanged

    def _dispose(self):
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged -= self.as_onCrosshairPositionChangedS
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        g_events.onArmorChanged -= self.onArmorChanged
        g_events.onMarkerColorChanged -= self.onMarkerColorChanged
        super(ArmorCalculator, self)._dispose()

    @logException
    def onMarkerColorChanged(self, color):
        self.calcMacro['color'] = config.i18n['UI_colors'].get(color, '#FFD700')
        self.calcMacro['message'] = config.data['messages'].get(color, '')

    @logException
    def onCameraChanged(self, ctrlMode, *_, **__):
        _CTRL_MODE = {CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM, CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION}
        if ctrlMode in _CTRL_MODE:
            self.as_armorCalculatorS('')

    @logException
    def onArmorChanged(self, armor, piercingPower, caliber, ricochet, noDamage):
        if armor is None:
            return self.as_armorCalculatorS('')
        self.calcMacro['ricochet'] = config.i18n['UI_ricochet'] if ricochet else ''
        self.calcMacro['noDamage'] = config.i18n['UI_noDamage'] if noDamage else ''
        self.calcMacro['countedArmor'] = armor
        self.calcMacro['piercingPower'] = piercingPower
        self.calcMacro['piercingReserve'] = piercingPower - armor
        self.calcMacro['caliber'] = caliber
        self.as_armorCalculatorS(config.data['template'] % self.calcMacro)
        print '=' * 25
        print 'as_'
        print self.as_armorCalculatorS(config.data['template'] % self.calcMacro)
        print '=' * 25
        print 'template'
        print (config.data['template'] % self.calcMacro)
        print '=' * 25


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
        # noinspection PyProtectedMember
        c_details = _CrosshairShotResults._getAllCollisionDetails(hitPoint, direction, entity)
        if c_details is None:
            return UNDEFINED_RESULT
        shot = player.getVehicleDescriptor().shot
        shell = shot.shell
        full_piercing_power = cls.getFullPiercingPower(hitPoint, piercingMultiplier, shot, player)
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
    def getFullPiercingPower(hitPoint, piercingMultiplier, shot, player):
        p100, p500 = (pp * piercingMultiplier for pp in shot.piercingPower)
        if shot.shell.kind in FULL_PP_RANGE:
            return p100
        else:
            distance = hitPoint.distTo(player.position)
            if distance <= 100.0:
                return p100
            elif distance < shot.maxDistance:
                return p100 - (p100 - p500) * (distance - 100.0) / 400.0
            return p500

    @staticmethod
    def isModernMechanics(shell):
        return shell.kind == SHELL_TYPES.HIGH_EXPLOSIVE and shell.type.mechanics == SHELL_MECHANICS_TYPE.MODERN and shell.type.shieldPenetration

    @staticmethod
    def computeArmor(c_details, shell, piercing_power, is_modern_he):
        computed_armor = 0
        ricochet = False
        no_damage = True
        is_jet = False
        jet_start_dist = 0
        # noinspection PyProtectedMember
        jet_loss = _CrosshairShotResults._SHELL_EXTRA_DATA[shell.kind].jetLossPPByDist
        for detail in c_details:
            mat_info = detail.matInfo
            if mat_info is None:
                continue
            # noinspection PyProtectedMember
            computed_armor += _CrosshairShotResults._computePenetrationArmor(shell, detail.hitAngleCos, mat_info)
            if is_jet:
                jetDist = detail.dist - jet_start_dist
                if jetDist > 0:
                    piercing_power *= 1.0 - jetDist * jet_loss
            else:
                # noinspection PyProtectedMember
                ricochet = _CrosshairShotResults._shouldRicochet(shell, detail.hitAngleCos, mat_info)
            if mat_info.vehicleDamageFactor:
                no_damage = False
                break
            elif is_modern_he:
                piercing_power -= computed_armor * MODERN_HE_PIERCING_POWER_REDUCTION_FACTOR_FOR_SHIELDS
            elif jet_loss > 0:
                is_jet = True
                jet_start_dist += detail.dist + mat_info.armor * 0.001
        return computed_armor, piercing_power, ricochet, no_damage


g_mod = ArmorCalculatorAllies()
g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, ArmorCalculatorInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, ArmorCalculator, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))


class ShotResultIndicatorPlugin(plugins.ShotResultIndicatorPlugin):

    def __init__(self, parentObj):
        super(ShotResultIndicatorPlugin, self).__init__(parentObj)
        self.__onAlly = bool(config.data['displayOnAllies'])

    def __updateColor(self, markerType, hitPoint, collision, direction):
        shot_result, armor, piercing_power, caliber, ricochet, no_damage = g_mod.getShotResult(hitPoint, collision, direction, self.__piercingMultiplier, self.__onAlly)
        if shot_result in self.__colors:
            color = self.__colors[shot_result]
            if self.__cache[markerType] != shot_result and self._parentObj.setGunMarkerColor(markerType, color):
                self.__cache[markerType] = shot_result
                g_events.onMarkerColorChanged(color)
            g_events.onArmorChanged(armor, piercing_power, caliber, ricochet, no_damage)

    def __setMapping(self, keys):
        super(ShotResultIndicatorPlugin, self).__setMapping(keys)
        self.__mapping[CROSSHAIR_VIEW_ID.STRATEGIC] = True


@override(plugins, 'createPlugins')
def createPlugins(base, *args):
    _plugins = base(*args)
    if config.data['enabled']:
        _plugins['shotResultIndicator'] = ShotResultIndicatorPlugin
    return _plugins


def onBattleLoaded():
    app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
    if app is None:
        return
    app.loadView(SFViewLoadParams(AS_INJECTOR))


g_events.onBattleLoaded += onBattleLoaded
