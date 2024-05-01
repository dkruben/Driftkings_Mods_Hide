# -*- coding: utf-8 -*-
from Event import Event
from gui.Scaleform.daapi.view.meta.ConsumablesPanelMeta import ConsumablesPanelMeta
from gui.Scaleform.framework import ScopeTemplates, ViewSettings, WindowLayer, g_entitiesFactories
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.shared.personality import ServicesLocator
from skeletons.gui.app_loader import GuiGlobalSpaceID

from DriftkingsCore import override, logInfo


class BigTextConsumablesPanel(View):
    onPanelInvalidated = Event()

    @staticmethod
    @ServicesLocator.appLoader.onGUISpaceEntered.__iadd__
    def __onGUISpaceEntered(spaceID):
        if spaceID != GuiGlobalSpaceID.BATTLE:
            return
        app = ServicesLocator.appLoader.getDefBattleApp()
        if app is not None:
            app.loadView(SFViewLoadParams(BigTextConsumablesPanel.__name__))

    def _populate(self):
        View._populate(self)
        self.onPanelInvalidated += self.invalidateRenderers

    def _dispose(self):
        self.onPanelInvalidated -= self.invalidateRenderers
        View._dispose(self)

    def invalidateRenderers(self):
        if self._isDAAPIInited():
            self.flashObject.invalidateRenderers()

    def py_log(self, *args):
        for a in args:
            print a,
        print


@override(ConsumablesPanelMeta, 'as_addEquipmentSlotS')
@override(ConsumablesPanelMeta, 'as_addOptionalDeviceSlotS')
@override(ConsumablesPanelMeta, 'as_addShellSlotS')
@override(ConsumablesPanelMeta, 'as_resetS')
def new_onPanelInvalidated(func, *args, **kwargs):
    func(*args, **kwargs)
    BigTextConsumablesPanel.onPanelInvalidated()


# noinspection PyArgumentList
g_entitiesFactories.addSettings(ViewSettings(BigTextConsumablesPanel.__name__, BigTextConsumablesPanel, 'BigTextConsumablesPanel.swf', WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
logInfo('BigTextConsumablesPanel', 'is loaded!')
