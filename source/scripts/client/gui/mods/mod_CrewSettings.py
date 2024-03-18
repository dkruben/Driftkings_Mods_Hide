# -*- coding: utf-8 -*-
import logging

# import BigWorld
from CurrentVehicle import g_currentVehicle
from gui import SystemMessages
from gui.Scaleform.daapi.view.lobby.cyberSport.VehicleSelectorPopup import VehicleSelectorPopup
from gui.shared.gui_items.processors.tankman import TankmanReturn
from gui.shared.utils import decorators
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader, GuiGlobalSpaceID
from skeletons.gui.shared import IItemsCache

from DriftkingsCore import SimpleConfigInterface, Analytics, override, loadJson, callback, cancelCallback, getAccountDBID

logger = logging.getLogger(__name__)


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        self.vehicle = {}
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'crewAutoReturn': True,
            'crewReturnByDefault': True
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_crewAutoReturn_text': 'Crew Auto Return',
            'UI_setting_crewAutoReturn_tooltip': '',
            'UI_setting_crewReturnByDefault_text': 'Crew Return By Default',
            'UI_setting_crewReturnByDefault_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('crewAutoReturn'),
                self.tb.createControl('crewReturnByDefault')
            ],
            'column2': []
        }

    def readCurrentSettings(self, quiet=True):
        self.vehicle = loadJson(self.ID, 'crewIgnored', self.vehicle, self.configPath)


# Crew class
class Crew(object):
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        self.intCD = None
        self.__callbackID = None

    def init(self):
        vehicle = g_currentVehicle.item
        intCD = vehicle.intCD
        self.intCD = intCD

    @decorators.adisp_process('crewReturning')
    def processReturnCrew(self, print_message=True):
        result = yield TankmanReturn(g_currentVehicle.item).request()
        if len(result.userMsg) and print_message:
            SystemMessages.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    @decorators.adisp_process('crewReturning')
    def processReturnCrewForVehicleSelectorPopup(self, vehicle):
        if not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
            yield TankmanReturn(vehicle).request()

    @decorators.adisp_process('unloading')
    def processUnloadCrew(self):
        result = yield TankmanUnload(g_currentVehicle.item.invID).request()
        if result.userMsg:
            SystemMessages.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    def invalidate(self):
        self.intCD = None
        if self.__callbackID is not None:
            cancelCallback(self.__callbackID)
            self.__callbackID = None

    def handleVehicleChange(self):
        if config.data['enabled'] and config.data['crewAutoReturn'] and config.data['crewReturnByDefault']:
            if self.__callbackID is not None:
                cancelCallback(self.__callbackID)
                self.__callbackID = None
            vehicle = g_currentVehicle.item
            intCD = vehicle.intCD
            if intCD != self.intCD:
                self.__callbackID = callback(1.5, self.returnCrew)
                self.intCD = intCD

    def handlePopupSelect(self, items):
        if len(items) == 1:
            cd = int(items[0])
            vehicle = self.itemsCache.items.getItemByCD(cd)
            vid = str(vehicle.invID)
            if vehicle and vehicle.isInInventory and not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
                if config.data['enabled'] and config.data['crewAutoReturn']:
                    if vid not in config.vehicle:
                        config.vehicle = {'vehicles': [vid]}
                        if vid in config.vehicle:
                            # config.vehicle = loadJson(config.ID, 'crewIgnored', config.vehicle, config.configPath, True, quiet=not config.vehicle)
                            self.processReturnCrewForVehicleSelectorPopup(vehicle)

    def isLastCrewAvailable(self):
        vehicle = g_currentVehicle.item
        lastCrewIDs = vehicle.lastCrew
        if lastCrewIDs is None:
            return False
        for lastTankmenInvID in lastCrewIDs:
            actualLastTankman = self.itemsCache.items.getTankman(lastTankmenInvID)
            if actualLastTankman is not None and actualLastTankman.isInTank:
                lastTankmanVehicle = self.itemsCache.items.getVehicle(actualLastTankman.vehicleInvID)
                if lastTankmanVehicle and lastTankmanVehicle.isLocked:
                    return False
        return True

    def returnCrew(self):
        self.__callbackID = None
        if not g_currentVehicle.isInHangar() or g_currentVehicle.isInBattle() or g_currentVehicle.isLocked() or g_currentVehicle.isCrewFull():
            return
        if not self.isLastCrewAvailable():
            return
        self.processReturnCrew()


g_crew = Crew()
config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


# Handlers/VehicleSelectorPopup
@override(VehicleSelectorPopup, 'onSelectVehicles')
def new__onSelectVehicles(func, self, items):
    func(self, items)
    try:
        g_crew.handlePopupSelect(items)
    except:
        logger.exception('VehicleSelectorPopup_onSelectVehicles')


# Handlers/AppLoader
def _onGUISpaceEntered(spaceID):
    if spaceID == GuiGlobalSpaceID.LOBBY:
        g_crew.init()
        g_currentVehicle.onChanged += g_currentVehicle_onChanged
    elif spaceID in (GuiGlobalSpaceID.LOGIN, GuiGlobalSpaceID.BATTLE, ):
        g_crew.invalidate()


# Handlers/g_currentVehicle
def g_currentVehicle_onChanged():
    try:
        g_crew.handleVehicleChange()
    except:
        logger.exception('g_currentVehicle_onChanged')


dependency.instance(IAppLoader).onGUISpaceEntered += _onGUISpaceEntered
g_currentVehicle.onChanged -= g_currentVehicle_onChanged
