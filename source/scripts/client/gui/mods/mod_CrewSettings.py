# -*- coding: utf-8 -*-
import json
import logging
import os
from io import open

import BigWorld
from CurrentVehicle import g_currentVehicle
from external_strings_utils import unicode_from_utf8
from gui import SystemMessages
from gui.Scaleform.daapi.view.lobby.cyberSport.VehicleSelectorPopup import VehicleSelectorPopup
from gui.shared.gui_items.processors.tankman import TankmanReturn
from gui.shared.utils import decorators
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader, GuiGlobalSpaceID
from skeletons.gui.shared import IItemsCache

from DriftkingsCore import SimpleConfigInterface, Analytics, override, callback, cancelCallback, calculate_version

logger = logging.getLogger(__name__)


def getPreferencesDir():
    return os.path.normpath(os.path.dirname(unicode_from_utf8(BigWorld.wg_getPreferencesFilePath())[1]))


preferencesDir = getPreferencesDir()


def getCachePath():
    path = os.path.join(preferencesDir, 'Driftkings')
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def encodeData(data):
    """encode dict keys/values to utf-8."""
    if isinstance(data, dict):
        return {encodeData(key): encodeData(value) for key, value in data.iteritems()}
    elif isinstance(data, list):
        return [encodeData(element) for element in data]
    elif isinstance(data, (str, unicode)):
        return data.encode('utf-8')
    else:
        return data


def openJsonFile(path):
    """Gets a dict from JSON."""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as dataFile:
            try:
                return encodeData(json.load(dataFile, encoding='utf-8'))
            except ValueError:
                return encodeData(json.loads(dataFile.read(), encoding='utf-8'))


def writeJsonFile(path, data):
    """Creates a new json file in a folder or replace old."""
    with open(path, 'w', encoding='utf-8') as dataFile:
        dataFile.write(unicode(json.dumps(data, skipkeys=True, ensure_ascii=False, indent=2, sort_keys=True)))


def openIgnoredVehicles():
    path = os.path.join(getCachePath(), 'auto_prev_crew.json')
    if not os.path.exists(path):
        writeJsonFile(path, {'vehicles': []})
        return set()
    return set(openJsonFile(path).get('vehicles'))


ignored_vehicles = openIgnoredVehicles()


def updateIgnoredVehicles(vehicles):
    path = os.path.join(getCachePath(), 'auto_prev_crew.json')
    writeJsonFile(path, {'vehicles': sorted(vehicles)})


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'crewAutoReturn': False,
            'crewReturnByDefault': False
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
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
            'column2': [
            ]
        }
    

config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class Crew(object):
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        self.intCD = None
        self.__callbackID = None

    def init(self):
        vehicle = g_currentVehicle.item
        intCD = vehicle.intCD
        self.intCD = intCD

    def invalidate(self):
        self.intCD = None
        if self.__callbackID is not None:
            cancelCallback(self.__callbackID)
            self.__callbackID = None
    
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

    def handleVehicleChange(self):
        if not config.data['enabled']:
            return
        if config.data['crewAutoReturn'] and config.data['crewReturnByDefault']:
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
            if vehicle and vehicle.isInInventory and not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
                if config.data['enabled'] and config.data['crewAutoReturn']:
                    if updateIgnoredVehicles(str(vehicle.invID)):
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


# Handlers/AppLoader
def onGUISpaceEntered(spaceID):
    if spaceID == GuiGlobalSpaceID.LOBBY:
        g_crew.init()
        g_currentVehicle.onChanged += g_currentVehicle_onChanged
    elif spaceID in (GuiGlobalSpaceID.LOGIN, GuiGlobalSpaceID.BATTLE,):
        g_crew.invalidate()


# Handlers/g_currentVehicle
def g_currentVehicle_onChanged():
    try:
        g_crew.handleVehicleChange()
    except:
        logger.exception('g_currentVehicle_onChanged')


# Handlers/VehicleSelectorPopup
@override(VehicleSelectorPopup, 'onSelectVehicles')
def new__onSelectVehicles(func, self, items):
    func(self, items)
    try:
        g_crew.handlePopupSelect(items)
    except:
        logger.exception('VehicleSelectorPopup_onSelectVehicles')


# Handlers/AppLoader
dependency.instance(IAppLoader).onGUISpaceEntered += onGUISpaceEntered
