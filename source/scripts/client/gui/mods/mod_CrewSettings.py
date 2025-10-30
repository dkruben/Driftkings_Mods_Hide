# -*- coding: utf-8 -*-
import json
import os
from io import open

import BigWorld
from CurrentVehicle import g_currentVehicle
from external_strings_utils import unicode_from_utf8
from gui.shared.utils.requesters import REQ_CRITERIA
from gui import SystemMessages
from gui.Scaleform.daapi.view.lobby.cyberSport.VehicleSelectorPopup import VehicleSelectorPopup
from gui.shared.gui_items.processors.tankman import TankmanReturn, TankmanUnload
from gui.shared.utils import decorators
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader, GuiGlobalSpaceID
from skeletons.gui.shared import IItemsCache

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, callback, cancelCallback, calculate_version, logException


def getCachePath():
    path = os.path.join(os.path.normpath(os.path.dirname(unicode_from_utf8(BigWorld.wg_getPreferencesFilePath())[1])), 'Driftkings')
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def encodeData(data):
    if isinstance(data, dict):
        return {encodeData(key): encodeData(value) for key, value in data.iteritems()}
    elif isinstance(data, list):
        return [encodeData(element) for element in data]
    elif isinstance(data, (str, unicode)):
        return data.encode('utf-8')
    else:
        return data


def openJsonFile(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as dataFile:
        return encodeData(json.load(dataFile, encoding='utf-8'))


def writeJsonFile(path, data):
    with open(path, 'w', encoding='utf-8') as dataFile:
        dataFile.write(unicode(json.dumps(data, skipkeys=True, ensure_ascii=False, indent=2, sort_keys=True)))
    return True


def openIgnoredVehicles():
    path = os.path.join(getCachePath(), 'auto_prev_crew.json')
    if not os.path.exists(path):
        writeJsonFile(path, {'vehicles': []})
        return set()
    data = openJsonFile(path)
    return set(data.get('vehicles', []))


def updateIgnoredVehicles(vehicles):
    path = os.path.join(getCachePath(), 'auto_prev_crew.json')
    if isinstance(vehicles, (str, unicode)):
        vehicles_set = ignored_vehicles.copy()
        vehicles_set.add(vehicles)
        vehicles = vehicles_set
    return writeJsonFile(path, {'vehicles': sorted(vehicles)})


def removeIgnoredVehicle(vehicle_id):
    vehicles_set = ignored_vehicles.copy()
    if str(vehicle_id) in vehicles_set:
        vehicles_set.remove(str(vehicle_id))
        return writeJsonFile(os.path.join(getCachePath(), 'auto_prev_crew.json'), {'vehicles': sorted(vehicles_set)})
    return False


def clearIgnoredVehicles():
    return writeJsonFile(os.path.join(getCachePath(), 'auto_prev_crew.json'), {'vehicles': []})


ignored_vehicles = openIgnoredVehicles()


class ConfigInterface(DriftkingsConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.2.0 (%(file_compile_date)s)'  # Updated version
        self.author = 'Maintenance by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'crewAutoReturn': False,
            'crewReturnByDefault': False,
            'autoReturnDelay': 1.5,  # New configurable delay
            'showNotifications': True,  # New option to toggle notifications
            'excludePremiumVehicles': False  # New option to exclude premium vehicles
        }
        self.i18n = {
            'UI_description': 'Crew Settings',
            'UI_version': calculate_version(self.version),
            'UI_setting_crewAutoReturn_text': 'Crew Auto Return',
            'UI_setting_crewAutoReturn_tooltip': 'Automatically return crew to their vehicle',
            'UI_setting_crewReturnByDefault_text': 'Crew Return By Default',
            'UI_setting_crewReturnByDefault_tooltip': 'Return crew by default when switching vehicles',
            'UI_setting_autoReturnDelay_text': 'Auto Return Delay (seconds)',
            'UI_setting_autoReturnDelay_tooltip': 'Delay before automatically returning crew',
            'UI_setting_showNotifications_text': 'Show Notifications',
            'UI_setting_showNotifications_tooltip': 'Show system notifications when crew is returned',
            'UI_setting_excludePremiumVehicles_text': 'Exclude Premium Vehicles',
            'UI_setting_excludePremiumVehicles_tooltip': 'Do not auto-return crew for premium vehicles',
            'UI_message_crewReturned': 'Crew has been returned to vehicle',
            'UI_message_crewNotAvailable': 'Crew is not available for return'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('crewAutoReturn'),
                self.tb.createControl('crewReturnByDefault'),
                self.tb.createSlider('autoReturnDelay', 0.5, 5.0, 0.5),
                self.tb.createControl('showNotifications')
            ],
            'column2': [
                self.tb.createControl('excludePremiumVehicles')
            ]
        }


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


class Crew(object):
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        self.intCD = None
        self.__callbackID = None
        self.last_operation_time = 0

    def init(self):
        if g_currentVehicle.isPresent():
            vehicle = g_currentVehicle.item
            self.intCD = vehicle.intCD

    def invalidate(self):
        self.intCD = None
        if self.__callbackID is not None:
            cancelCallback(self.__callbackID)
            self.__callbackID = None

    @decorators.adisp_process('crewReturning')
    def processReturnCrew(self, print_message=True):
        if not g_currentVehicle.isPresent():
            return
        result = yield TankmanReturn(g_currentVehicle.item).request()
        if result and result.userMsg and print_message and config.data['showNotifications']:
            SystemMessages.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    @decorators.adisp_process('crewReturning')
    def processReturnCrewForVehicleSelectorPopup(self, vehicle):
        if vehicle and not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
            yield TankmanReturn(vehicle).request()

    @decorators.adisp_process('unloading')
    def processUnloadCrew(self):
        if not g_currentVehicle.isPresent():
            return
        result = yield TankmanUnload(g_currentVehicle.item.invID).request()
        if result and result.userMsg and config.data['showNotifications']:
            SystemMessages.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    def handleVehicleChange(self):
        if not config.data['enabled']:
            return
        if config.data['crewAutoReturn'] and config.data['crewReturnByDefault']:
            if self.__callbackID is not None:
                cancelCallback(self.__callbackID)
                self.__callbackID = None
            if not g_currentVehicle.isPresent():
                return
            vehicle = g_currentVehicle.item
            intCD = vehicle.intCD
            if config.data['excludePremiumVehicles'] and vehicle.isPremium:
                return
            if intCD != self.intCD:
                self.__callbackID = callback(config.data['autoReturnDelay'], self.returnCrew)
                self.intCD = intCD

    @logException
    def handlePopupSelect(self, items):
        if not items or not config.data['enabled'] or not config.data['crewAutoReturn']:
            return
        if len(items) == 1:
            cd = int(items[0])
            vehicle = self.itemsCache.items.getItemByCD(cd)
            if vehicle and vehicle.isInInventory and not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
                if config.data['excludePremiumVehicles'] and vehicle.isPremium:
                    return
                vehicle_id = str(vehicle.invID)
                if updateIgnoredVehicles(vehicle_id):
                    self.processReturnCrewForVehicleSelectorPopup(vehicle)

    def isLastCrewAvailable(self):
        if not g_currentVehicle.isPresent():
            return False
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
        if not g_currentVehicle.isPresent():
            return
        if not g_currentVehicle.isInHangar() or g_currentVehicle.isInBattle() or g_currentVehicle.isLocked() or g_currentVehicle.isCrewFull():
            return
        if not self.isLastCrewAvailable():
            if config.data['showNotifications']:
                SystemMessages.pushMessage(config.i18n['UI_message_crewNotAvailable'], type=SystemMessages.SM_TYPE.Warning)
            return
        self.processReturnCrew()

    def toggleAutoReturnForCurrentVehicle(self):
        if not g_currentVehicle.isPresent():
            return False
        vehicle_id = str(g_currentVehicle.item.invID)
        if vehicle_id in ignored_vehicles:
            removeIgnoredVehicle(vehicle_id)
            if config.data['showNotifications']:
                SystemMessages.pushMessage('Auto-return enabled for this vehicle', type=SystemMessages.SM_TYPE.Information)
            return True
        else:
            updateIgnoredVehicles(vehicle_id)
            if config.data['showNotifications']:
                SystemMessages.pushMessage("Auto-return disabled for this vehicle", type=SystemMessages.SM_TYPE.Information)
            return False

    def getCrewInfo(self):
        if not g_currentVehicle.isPresent():
            return None
        vehicle = g_currentVehicle.item
        crew_info = {'vehicle_name': vehicle.userName, 'crew_complete': vehicle.isCrewFull(), 'crew_members': []}
        for slotIdx, tankman in vehicle.crew:
            if tankman is not None:
                crew_info['crew_members'].append({'name': tankman.fullUserName, 'role': tankman.roleUserName, 'level': tankman.level, 'skills': [skill.userName for skill in tankman.skills]})
            else:
                crew_info['crew_members'].append(None)
        return crew_info

    def returnAllCrews(self):
        vehicles = self.itemsCache.items.getVehicles(REQ_CRITERIA.INVENTORY)
        for vehicle in vehicles.values():
            if not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
                self.processReturnCrewForVehicleSelectorPopup(vehicle)


g_crew = Crew()


@override(VehicleSelectorPopup, 'onSelectVehicles')
@logException
def new__onSelectVehicles(func, self, items):
    func(self, items)
    g_crew.handlePopupSelect(items)


class Register(object):
    def __init__(self):
        try:
            appLoader = dependency.instance(IAppLoader)
            appLoader.onGUISpaceEntered += self.onGUISpaceEntered
            appLoader.onGUISpaceLeft += self.onGUISpaceLeft
        except Exception:
            pass

    def onGUISpaceEntered(self, spaceID):
        if spaceID == GuiGlobalSpaceID.LOBBY:
            g_crew.init()
            g_currentVehicle.onChanged += self.onChanged

    def onGUISpaceLeft(self, spaceID):
        if spaceID == GuiGlobalSpaceID.LOBBY:
            g_crew.invalidate()
            g_currentVehicle.onChanged -= self.onChanged

    @staticmethod
    @logException
    def onChanged():
        g_crew.handleVehicleChange()


Register()
