# -*- coding: utf-8 -*-
from math import degrees

import Keys
from constants import ARENA_GUI_TYPE
from constants import VISIBILITY
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.battle.shared.minimap import plugins
from gui.Scaleform.daapi.view.battle.shared.minimap.component import MinimapComponent
from gui.Scaleform.daapi.view.battle.shared.minimap.settings import CIRCLE_TYPE, CIRCLE_STYLE, VIEW_RANGE_CIRCLES_AS3_DESCR
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.DisposableEntity import EntityState
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control import avatar_getter
from gui.shared.personality import ServicesLocator
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import SimpleConfigInterface, Analytics, override, getPlayer, checkKeys, hex_to_decimal, logError, g_events

AS_INJECTOR = 'MinimapCentredViewInjector'
AS_BATTLE = 'MinimapCentredView'
AS_SWF = 'MinimapCentred.swf'

BATTLES_RANGE = (
    ARENA_GUI_TYPE.COMP7,
    ARENA_GUI_TYPE.EPIC_BATTLE,
    ARENA_GUI_TYPE.EPIC_RANDOM,
    ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING,
    ARENA_GUI_TYPE.FORT_BATTLE_2,
    ARENA_GUI_TYPE.FUN_RANDOM,
    ARENA_GUI_TYPE.MAPBOX,
    ARENA_GUI_TYPE.RANDOM,
    ARENA_GUI_TYPE.RANKED,
    ARENA_GUI_TYPE.SORTIE_2,
    ARENA_GUI_TYPE.TRAINING,
    ARENA_GUI_TYPE.UNKNOWN,
)


class ConfigInterface(SimpleConfigInterface):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        self.minimapZoom = False
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.1.0 (%(file_compile_date)s)'
        self.author = '_DKRuben__EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.defaultKeys = {'button': [Keys.KEY_LCONTROL]}
        self.data = {
            'enabled': True,
            'permanentMinimapDeath': False,
            'yaw': True,
            'showNames': True,
            'viewRadius': True,
            'zoomFactor': 1.1,
            'button': self.defaultKeys['button'],
            'changeColorCircles': True,
            'colorDrawCircle': '2B28D1',
            'colorMaxViewCircle': 'E02810',
            'colorMinSpottingCircle': '35DE46',
            'colorViewCircle': 'FF7FFF',
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_permanentMinimapDeath_text': 'Permanent Minimap Death',
            'UI_setting_permanentMinimapDeath_tooltip': 'Always show the destroyed on the map',
            'UI_setting_showNames_text': 'Show Names',
            'UI_setting_showNames_tooltip': 'Display the names of destroyed tanks',
            'UI_setting_yaw_text': 'Show Hover Angles',
            'UI_setting_yaw_tooltip': 'Show Hover Angles on all vehicles where they are',
            'UI_setting_viewRadius_text': 'Real View',
            'UI_setting_viewRadius_tooltip': 'Remove the limitation of the circle of vision 445m',
            'UI_setting_button_text': 'Zoom Button',
            'UI_setting_button_tooltip': 'Hot key for zoom.',
            'UI_setting_changeColorCircles_text': 'Change Color Circles',
            'UI_setting_changeColorCircles_tooltip': 'When enabled, you can change the color of the circles on the minimap.',
            'UI_setting_colorDrawCircleCheck_text': 'Draw Range Circle',
            'UI_setting_colorDrawCircle_text': 'Default: <font color=\'#%(colorDrawCircle)s\'></font>',
            'UI_setting_colorDrawCircle_tooltip': '',
            'UI_setting_colorMaxViewCircleCheck_text': 'Max. View Range Circle',
            'UI_setting_colorMaxViewCircle_text': 'Default: <font color=\'#%(colorMaxViewCircle)s\'></font>',
            'UI_setting_colorMaxViewCircle_tooltip': '',
            'UI_setting_colorMinSpottingCircleCheck_text': 'Min. Spotting Range Circle',
            'UI_setting_colorMinSpottingCircle_text': 'Default: <font color=\'#%(colorMinSpottingCircle)s\'></font>',
            'UI_setting_colorMinSpottingCircle_tooltip': '',
            'UI_setting_colorViewCircleCheck_text': 'View Range Circle',
            'UI_setting_colorViewCircle_text': 'Default: <font color=\'#%(colorViewCircle)s\'></font>',
            'UI_setting_colorViewCircle_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        xColorDrawRange = self.tb.createControl('colorDrawCircle', self.tb.types.ColorChoice)
        xColorDrawRange['text'] = self.tb.getLabel('colorDrawCircleCheck')
        xColorDrawRange['tooltip'] %= {'colorDrawCircle': self.data['colorDrawCircle']}
        xColorMaxRange = self.tb.createControl('colorMaxViewCircle', self.tb.types.ColorChoice)
        xColorMaxRange['text'] = self.tb.getLabel('colorMaxViewCircleCheck')
        xColorMaxRange['tooltip'] %= {'colorMaxViewCircle': self.data['colorMaxViewCircle']}
        xColorMinSpottingRange = self.tb.createControl('colorMinSpottingCircle', self.tb.types.ColorChoice)
        xColorMinSpottingRange['text'] = self.tb.getLabel('colorMinSpottingCircleCheck')
        xColorMinSpottingRange['tooltip'] %= {'colorMinSpottingCircle': self.data['colorMinSpottingCircle']}
        xColorViewRange = self.tb.createControl('colorViewCircle', self.tb.types.ColorChoice)
        xColorViewRange['text'] = self.tb.getLabel('colorViewCircleCheck')
        xColorViewRange['tooltip'] %= {'colorViewCircle': self.data['colorViewCircle']}

        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('permanentMinimapDeath'),
                self.tb.createControl('showNames'),
                self.tb.createHotKey('button'),
                self.tb.createControl('viewRadius'),
                self.tb.createControl('yaw')
            ],
            'column2': [
                self.tb.createControl('changeColorCircles'),
                xColorDrawRange,
                xColorMaxRange,
                xColorMinSpottingRange,
                xColorViewRange
            ]
        }

    @property
    def notEpicBattle(self):
        return not self.sessionProvider.arenaVisitor.gui.isInEpicRange()

    @property
    def xvmInstalled(self):
        try:
            import xvm_main
            return True
        except ImportError:
            return False

    def onHotkeyPressed(self, event):
        if not hasattr(getPlayer(), 'arena') or not self.data['enabled']:
            return
        isDown = checkKeys(self.data['button'])
        if isDown != self.minimapZoom:
            self.minimapZoom = isDown
            g_events.onAltKey(isDown)
            avatar_getter.setForcedGuiControlMode(event.isKeyDown(), enableAiming=not event.isKeyDown(), cursorVisible=event.isKeyDown())
        if not event.isKeyDown():
            return

    @staticmethod
    def onBattleLoaded():
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class MinimapCentredInjector(View):

    def _populate(self):
        # noinspection PyProtectedMember
        super(MinimapCentredInjector, self)._populate()
        g_events.onBattleClosed += self.destroy

    def _dispose(self):
        g_events.onBattleClosed -= self.destroy
        # noinspection PyProtectedMember
        super(MinimapCentredInjector, self)._dispose()

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            return
        super(MinimapCentredInjector, self).destroy()


class MinimapCentredView(BaseDAAPIComponent):
    def _populate(self):
        # noinspection PyProtectedMember
        super(MinimapCentredView, self)._populate()
        g_events.onBattleClosed += self.destroy
        g_events.onAltKey += self.onAltKey

    def _dispose(self):
        g_events.onBattleClosed -= self.destroy
        g_events.onAltKey -= self.onAltKey
        # noinspection PyProtectedMember
        super(MinimapCentredView, self)._dispose()

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            return
        super(MinimapCentredView, self).destroy()

    def onAltKey(self, pressed):
        if config.notEpicBattle and not config.xvmInstalled:
            self.flashObject.as_minimapCentered(pressed, config.data['zoomFactor'])


class PersonalEntriesPlugin(plugins.PersonalEntriesPlugin):

    def start(self):
        super(PersonalEntriesPlugin, self).start()
        if config.data['enabled'] and config.data['yaw'] and self.__yawLimits is None:
            vInfo = self._arenaDP.getVehicleInfo()
            yawLimits = vInfo.vehicleType.turretYawLimits
            if yawLimits is not None:
                self.__yawLimits = (degrees(yawLimits[0]), degrees(yawLimits[1]))

    def _calcCircularVisionRadius(self):
        if config.data['enabled'] and config.data['viewRadius']:
            vehAttrs = self.sessionProvider.shared.feedback.getVehicleAttrs()
            return vehAttrs.get('circularVisionRadius', VISIBILITY.MIN_RADIUS)
        # noinspection PyProtectedMember
        return super(PersonalEntriesPlugin, self)._calcCircularVisionRadius()

    def __addDrawRangeCircle(self):
        if config.data['enabled'] and config.data['changeColorCircles']:
            if self.__circlesVisibilityState & CIRCLE_TYPE.DRAW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.DRAW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MAX_DRAW_CIRCLE,
                         hex_to_decimal(config.data['colorDrawCircle']), CIRCLE_STYLE.ALPHA, 565.0)
            return super(PersonalEntriesPlugin, self).__addDrawRangeCircle()

    def __addMaxViewRangeCircle(self):
        if config.data['enabled'] and config.data['changeColorCircles']:
            if self.__circlesVisibilityState & CIRCLE_TYPE.MAX_VIEW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.MAX_VIEW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MAX_VIEW_CIRCLE,
                         hex_to_decimal(config.data['colorMaxViewCircle']), CIRCLE_STYLE.ALPHA, VISIBILITY.MAX_RADIUS)
            return super(PersonalEntriesPlugin, self).__addMaxViewRangeCircle()

    def __addMinSpottingRangeCircle(self):
        if config.data['enabled'] and config.data['changeColorCircles']:
            if self.__circlesVisibilityState & CIRCLE_TYPE.MIN_SPOTTING_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.MIN_SPOTTING_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MIN_SPOTTING_CIRCLE,
                         hex_to_decimal(config.data['colorMinSpottingCircle']), CIRCLE_STYLE.ALPHA,
                         VISIBILITY.MIN_RADIUS)
            return super(PersonalEntriesPlugin, self).__addMinSpottingRangeCircle()

    def __addViewRangeCircle(self):
        if config.data['enabled'] and config.data['changeColorCircles']:
            if self.__circlesVisibilityState & CIRCLE_TYPE.VIEW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.VIEW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_DYN_CIRCLE,
                         hex_to_decimal(config.data['colorViewCircle']), CIRCLE_STYLE.ALPHA, self._getViewRangeRadius())
            return super(PersonalEntriesPlugin, self).__addViewRangeCircle()


class ArenaVehiclesPlugin(plugins.ArenaVehiclesPlugin):

    def __init__(self, *args, **kwargs):
        super(ArenaVehiclesPlugin, self).__init__(*args, **kwargs)
        self.__showDestroyEntries = config.data['showNames']
        self.__isDestroyImmediately = config.data['permanentMinimapDeath']

    def _showVehicle(self, vehicleID, location):
        entry = self._entries[vehicleID]
        if entry.isAlive():
            # noinspection PyProtectedMember
            super(ArenaVehiclesPlugin, self)._showVehicle(vehicleID, location)

    def _hideVehicle(self, entry):
        if entry.isAlive() and entry.isActive():
            # noinspection PyProtectedMember
            super(ArenaVehiclesPlugin, self)._hideVehicle(entry)

    def __setDestroyed(self, vehicleID, entry):
        if self.__isDestroyImmediately:
            self._setInAoI(entry, True)
        super(ArenaVehiclesPlugin, self).__setDestroyed(vehicleID, entry)
        self._invoke(entry.getID(), self._showNames)

    def __switchToVehicle(self, prevCtrlID):
        if self.__isDestroyImmediately:
            return
        super(ArenaVehiclesPlugin, self).__switchToVehicle(prevCtrlID)

    @property
    def _showNames(self):
        if self.__showDestroyEntries and config.data['showNames']:
            return 'showVehicleName'
        return 'hideVehicleName'


@override(MinimapComponent, '_setupPlugins')
def new_setupPlugins(base, plugin, arenaVisitor):
    res = base(plugin, arenaVisitor)
    try:
        allowedMode = arenaVisitor.gui.guiType in BATTLES_RANGE
        if not config.xvmInstalled and allowedMode and config.data['enabled']:
            if config.data['permanentMinimapDeath']:
                res['vehicles'] = ArenaVehiclesPlugin
            res['personal'] = PersonalEntriesPlugin
    except Exception as err:
        logError(repr(err))
    finally:
        return res


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, MinimapCentredInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, MinimapCentredView, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
