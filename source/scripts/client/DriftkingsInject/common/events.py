from Event import SafeEvent
from gui.shared.personality import ServicesLocator
from skeletons.gui.app_loader import GuiGlobalSpaceID

__all__ = ('g_events',)


class Events(object):
    def __init__(self):
        self.onBattleClosed = SafeEvent()
        self.onBattleLoaded = SafeEvent()
        #
        self.onAltKey = SafeEvent()
        self.onVehicleChanged = SafeEvent()
        self.onVehicleChangedDelayed = SafeEvent()
        self.onDispersionAngleChanged = SafeEvent()
        self.onMarkerColorChanged = SafeEvent()
        self.onArmorChanged = SafeEvent()
        self.onUpdateVehicle = SafeEvent()
        self.onUpdateBlur = SafeEvent()

        ServicesLocator.appLoader.onGUISpaceEntered += self.onGUISpaceEntered
        ServicesLocator.appLoader.onGUISpaceLeft += self.onGUISpaceLeft

    @staticmethod
    def onGUISpaceEntered(spaceID):
        if spaceID == GuiGlobalSpaceID.BATTLE:
            g_events.onBattleLoaded()

    @staticmethod
    def onGUISpaceLeft(spaceID):
        if spaceID == GuiGlobalSpaceID.BATTLE:
            g_events.onBattleClosed()


g_events = Events()
