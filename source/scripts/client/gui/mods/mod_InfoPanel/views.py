# -*- coding: utf-8 -*-
import Event
from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ComponentSettings, ScopeTemplates
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
from gui.shared.personality import ServicesLocator
from skeletons.gui.app_loader import GuiGlobalSpaceID

from ._constants import AS_BATTLE, AS_INJECTOR, AS_SWF


class Events(object):
    def __init__(self):
        self.hide = Event.Event()
        self.isDrag = Event.Event()
        self.onUpdatePosition = Event.Event()
        self.onUpdateUI = Event.Event()
        self.onAppResolution = Event.Event()
        self.setDefaultPosition = Event.Event()

        ServicesLocator.appLoader.onGUISpaceEntered += self.__onGUISpaceEntered

    def _onAppResolution(self, *args, **kwargs):
        self.onAppResolution(*args, **kwargs)

    @staticmethod
    def __onGUISpaceEntered(spaceID):
        if spaceID == GuiGlobalSpaceID.BATTLE:
            ServicesLocator.appLoader.getDefBattleApp().loadView(SFViewLoadParams(AS_INJECTOR))


g_events = Events()


class InfoPanelUI(View):
    def _populate(self):
        # noinspection PyProtectedMember
        super(InfoPanelUI, self)._populate()
        g_events.hide += self.as_hideS
        #
        g_events.onUpdateUI += self.onUpdateUI
        g_events.setDefaultPosition += self.as_setDefaultPositionS

        g_eventBus.addListener(events.GameEvent.FULL_STATS, self.handleToggleFullStats, scope=EVENT_BUS_SCOPE.BATTLE)
        g_eventBus.addListener(events.GameEvent.SHOW_CURSOR, self.handleShowCursor, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.addListener(events.GameEvent.HIDE_CURSOR, self.handleHideCursor, scope=EVENT_BUS_SCOPE.GLOBAL)

    def _dispose(self):
        g_events.onUpdateUI -= self.onUpdateUI
        g_events.hide -= self.as_hideS
        #
        g_eventBus.removeListener(events.GameEvent.FULL_STATS, self.handleToggleFullStats, scope=EVENT_BUS_SCOPE.BATTLE)
        g_eventBus.removeListener(events.GameEvent.SHOW_CURSOR, self.handleShowCursor, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.removeListener(events.GameEvent.HIDE_CURSOR, self.handleHideCursor, scope=EVENT_BUS_SCOPE.GLOBAL)
        # noinspection PyProtectedMember
        super(InfoPanelUI, self)._dispose()

    @staticmethod
    def onUpdatePosition(x, y):
        g_events.onUpdatePosition([x, y])

    def onUpdateUI(self, config, text):
        position = config.get('textPosition')
        if position is None:
            self.as_setDefaultPositionS()
        else:
            self.as_setPositionS(*position)
        self.as_setTextS(text)
        self.as_setShadowS(dict(config['textShadow']))
        self.as_isDraggableS(isDrag=not config['textLock'])

    def handleToggleFullStats(self, event):
        self.as_setVisibleS(not event.ctx['isDown'])

    def handleShowCursor(self, _):
        self.as_setVisibleBBS(True)

    def handleHideCursor(self, _):
        self.as_setVisibleBBS(False)

    def as_setScaleS(self, width, height):
        if self._isDAAPIInited():
            self.flashObject.as_setScale(width, height)

    def as_setTextS(self, text):
        if self._isDAAPIInited():
            self.flashObject.as_setText(text)

    def as_hideS(self, delay):
        if self._isDAAPIInited():
            self.flashObject.as_hide(delay)

    def as_setVisibleS(self, value):
        if self._isDAAPIInited():
            self.flashObject.as_setVisible(value)

    def as_setVisibleBBS(self, value):
        if self._isDAAPIInited():
            self.flashObject.as_setVisibleBB(value)

    def as_setPositionS(self, x, y):
        if self._isDAAPIInited():
            self.flashObject.as_setPosition(x, y)

    def as_setShadowS(self, linkage):
        if self._isDAAPIInited():
            self.flashObject.as_setShadow(linkage)

    def as_setDefaultPositionS(self):
        if self._isDAAPIInited():
            self.flashObject.as_setDefaultPosition()

    def as_isDraggableS(self, isDrag):
        if self._isDAAPIInited():
            self.flashObject.as_isDraggable(isDrag)


g_entitiesFactories.addSettings(ViewSettings(alias=AS_INJECTOR, clazz=View, url=AS_SWF, layer=WindowLayer.WINDOW, scope=ScopeTemplates.DEFAULT_SCOPE))
g_entitiesFactories.addSettings(ComponentSettings(AS_BATTLE, InfoPanelUI, ScopeTemplates.DEFAULT_SCOPE))
