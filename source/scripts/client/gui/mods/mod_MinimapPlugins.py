# -*- coding: utf-8 -*-
from math import degrees

import Keys
from constants import VISIBILITY
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.battle.shared.minimap import plugins
from gui.Scaleform.daapi.view.battle.shared.minimap.component import MinimapComponent
from gui.Scaleform.daapi.view.battle.shared.minimap.settings import CIRCLE_TYPE, VIEW_RANGE_CIRCLES_AS3_DESCR
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control import avatar_getter
from gui.shared.personality import ServicesLocator
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, checkKeys, hexToDecimal, logError, calculate_version, xvmInstalled, battle_range
from DriftkingsInject import DriftkingsInjector, DriftkingsView, g_events

AS_INJECTOR = 'MinimapCentredViewInjector'
AS_BATTLE = 'MinimapCentredView'
AS_SWF = 'MinimapCentred.swf'


class ConfigInterface(DriftkingsConfigInterface):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        self.minimapZoom = False
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.3.0 (%(file_compile_date)s)'  # Updated version number
        self.author = '_DKRuben__EU'
        self.defaultKeys = {'button': [Keys.KEY_LCONTROL]}
        self.data = {
            'enabled': True,
            'permanentMinimapDeath': False,
            'yaw': True,
            'showNames': True,
            'viewRadius': True,
            'zoomFactor': 1.1,
            'zoomFactorMax': 2.0,  # New setting for maximum zoom level
            'button': self.defaultKeys['button'],
            'alpha': 90,
            'changeColorCircles': True,
            'colorDrawCircle': '2B28D1',
            'colorMaxViewCircle': 'E02810',
            'colorMinSpottingCircle': '35DE46',
            'colorViewCircle': 'FF7FFF',
            'showLastPositions': True,  # New setting for showing last known positions
            'lastPositionDuration': 30,  # New setting for how long to show last positions (seconds)
            'showVehicleTypes': True,  # New setting for showing vehicle types on minimap
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
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
            'UI_setting_zoomFactorMax_text': 'Maximum Zoom Factor',
            'UI_setting_zoomFactorMax_tooltip': 'Maximum zoom level for the minimap (1.0-3.0)',
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
            'UI_setting_showLastPositions_text': 'Show Last Known Positions',
            'UI_setting_showLastPositions_tooltip': 'Display the last known positions of enemy vehicles',
            'UI_setting_lastPositionDuration_text': 'Last Position Duration',
            'UI_setting_lastPositionDuration_tooltip': 'How long to show last known positions (in seconds)',
            'UI_setting_showVehicleTypes_text': 'Show Vehicle Types',
            'UI_setting_showVehicleTypes_tooltip': 'Display vehicle type icons on the minimap'
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
                self.tb.createControl('yaw'),
                self.tb.createControl('showLastPositions'),
                self.tb.createSlider('lastPositionDuration', 10, 60, 5, '{{value}}.s')
            ],
            'column2': [
                self.tb.createControl('changeColorCircles'),
                xColorDrawRange,
                xColorMaxRange,
                xColorMinSpottingRange,
                xColorViewRange,
                self.tb.createControl('showVehicleTypes'),
                self.tb.createSlider('zoomFactorMax', 1.0, 3.0, 0.1, '{{value}}.Px/Py')
            ]
        }

    @property
    def notEpicBattle(self):
        return not self.sessionProvider.arenaVisitor.gui.isInEpicRange()

    def onHotkeyPressed(self, event):
        if not self.data['enabled']:
            return
        # Handle regular zoom button
        isDown = checkKeys(self.data['button'])
        if isDown != self.minimapZoom:
            self.minimapZoom = isDown
            g_events.onAltKey(isDown)
            avatar_getter.setForcedGuiControlMode(event.isKeyDown(), enableAiming=not event.isKeyDown(), cursorVisible=event.isKeyDown())
        if not event.isKeyDown():
            return

    def onBattleLoaded(self):
        if not self.data['enabled']:
            return
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


class MinimapCentredView(DriftkingsView):
    def __init__(self):
        super(MinimapCentredView, self).__init__(config.ID)
        self._zoomToggled = False
        self._currentZoomLevel = 1.0

    def _populate(self):
        # noinspection PyProtectedMember
        super(MinimapCentredView, self)._populate()
        g_events.onAltKey += self.onAltKey

    def _dispose(self):
        g_events.onAltKey -= self.onAltKey
        # noinspection PyProtectedMember
        super(MinimapCentredView, self)._dispose()

    def onAltKey(self, pressed):
        if config.notEpicBattle and not xvmInstalled:
            zoomFactor = config.data['zoomFactor'] if pressed else 1.0
            self._currentZoomLevel = min(zoomFactor, config.data['zoomFactorMax'])
            self.flashObject.as_minimapCentered(pressed, self._currentZoomLevel)


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
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MAX_DRAW_CIRCLE,hexToDecimal(config.data['colorDrawCircle']), config.data['alpha'], 565.0)
            return super(PersonalEntriesPlugin, self).__addDrawRangeCircle()

    def __addMaxViewRangeCircle(self):
        if config.data['enabled'] and config.data['changeColorCircles']:
            if self.__circlesVisibilityState & CIRCLE_TYPE.MAX_VIEW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.MAX_VIEW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MAX_VIEW_CIRCLE,hexToDecimal(config.data['colorMaxViewCircle']), config.data['alpha'], VISIBILITY.MAX_RADIUS)
            return super(PersonalEntriesPlugin, self).__addMaxViewRangeCircle()

    def __addMinSpottingRangeCircle(self):
        if config.data['enabled'] and config.data['changeColorCircles']:
            if self.__circlesVisibilityState & CIRCLE_TYPE.MIN_SPOTTING_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.MIN_SPOTTING_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_MIN_SPOTTING_CIRCLE,hexToDecimal(config.data['colorMinSpottingCircle']), config.data['alpha'], VISIBILITY.MIN_RADIUS)
            return super(PersonalEntriesPlugin, self).__addMinSpottingRangeCircle()

    def __addViewRangeCircle(self):
        if config.data['enabled'] and config.data['changeColorCircles']:
            if self.__circlesVisibilityState & CIRCLE_TYPE.VIEW_RANGE:
                return
            self.__circlesVisibilityState |= CIRCLE_TYPE.VIEW_RANGE
            self._invoke(self.__circlesID, VIEW_RANGE_CIRCLES_AS3_DESCR.AS_ADD_DYN_CIRCLE,hexToDecimal(config.data['colorViewCircle']), config.data['alpha'], self._getViewRangeRadius())
            return super(PersonalEntriesPlugin, self).__addViewRangeCircle()


class ArenaVehiclesPlugin(plugins.ArenaVehiclesPlugin):
    def __init__(self, *args, **kwargs):
        super(ArenaVehiclesPlugin, self).__init__(*args, **kwargs)
        self.__showDestroyEntries = config.data['showNames']
        self.__isDestroyImmediately = config.data['permanentMinimapDeath']
        self.__showVehicleTypes = config.data['showVehicleTypes']
        self.__lastPositions = {}
        self.__lastPositionTimers = {}

    def start(self):
        super(ArenaVehiclesPlugin, self).start()
        if config.data['enabled'] and config.data['showLastPositions']:
            g_events.onMinimapClicked += self.onMinimapClicked

    def stop(self):
        if config.data['enabled'] and config.data['showLastPositions']:
            g_events.onMinimapClicked -= self.onMinimapClicked
        super(ArenaVehiclesPlugin, self).stop()

    def _showVehicle(self, vehicleID, location):
        entry = self._entries[vehicleID]
        if entry.isAlive():
            # Store last position for enemy vehicles
            if config.data['showLastPositions'] and entry.getTeam() != self._playerTeam:
                self.__lastPositions[vehicleID] = location
                self.__lastPositionTimers[vehicleID] = config.data['lastPositionDuration']
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

    def __switchToVehicle(self, prevCtrlID):
        if self.__isDestroyImmediately:
            return
        super(ArenaVehiclesPlugin, self).__switchToVehicle(prevCtrlID)

    def _getDisplayedName(self, vInfo):
        if not vInfo.isAlive() and not config.data['showNames']:
            return ''
        # noinspection PyProtectedMember
        return super(ArenaVehiclesPlugin, self)._getDisplayedName(vInfo)

    def updateLastPositions(self, deltaTime):
        if not config.data['showLastPositions']:
            return
        for vehicleID in list(self.__lastPositionTimers.keys()):
            self.__lastPositionTimers[vehicleID] -= deltaTime
            if self.__lastPositionTimers[vehicleID] <= 0:
                del self.__lastPositionTimers[vehicleID]
                del self.__lastPositions[vehicleID]
            else:
                opacity = min(100, int(self.__lastPositionTimers[vehicleID] / config.data['lastPositionDuration'] * 100))
                location = self.__lastPositions[vehicleID]
                self._invoke(vehicleID, 'setLastPosition', location[0], location[1], opacity)

    def onMinimapClicked(self, x, y):
        pass


# Add the new event handlers to the g_events object
def init_events():
    if not hasattr(g_events, 'onToggleZoom'):
        g_events.onToggleZoom = set()
    if not hasattr(g_events, 'onMinimapClicked'):
        g_events.onMinimapClicked = set()


init_events()


@override(MinimapComponent, '_setupPlugins')
def new_setupPlugins(func, self, arenaVisitor):
    args = func(self, arenaVisitor)
    try:
        allowedMode = arenaVisitor.gui.guiType in battle_range
        if not xvmInstalled and allowedMode and config.data['enabled']:
            if config.data['permanentMinimapDeath']:
                args['vehicles'] = ArenaVehiclesPlugin
            args['personal'] = PersonalEntriesPlugin
    except Exception as err:
        logError(config.ID, repr(err))
    finally:
        return args


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, MinimapCentredView, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
