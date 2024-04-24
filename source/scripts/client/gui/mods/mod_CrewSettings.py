# -*- coding: utf-8 -*-
import json
import os
from io import open

import BigWorld
from CurrentVehicle import g_currentVehicle
from external_strings_utils import unicode_from_utf8
from frameworks.wulf import WindowLayer
from gui import SystemMessages
from gui.Scaleform.daapi.view.lobby.exchange.ExchangeXPWindow import ExchangeXPWindow
from gui.impl.dialogs import dialogs
from gui.impl.dialogs.builders import InfoDialogBuilder
from gui.impl.pub.dialog_window import DialogButtons
from gui.shared.gui_items.processors.tankman import TankmanReturn
from gui.shared.gui_items.processors.vehicle import VehicleTmenXPAccelerator
from gui.shared.utils import decorators
from gui.veh_post_progression.models.progression import PostProgressionCompletion
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader
from skeletons.gui.shared import IItemsCache
from wg_async import AsyncReturn, wg_async, wg_await

from DriftkingsCore import SimpleConfigInterface, Analytics, override, logInfo, logError
from DriftkingsInject import g_events

IMG_DIR = 'img://../mods/configs/Driftkings/Driftkings_GUI'


def getLogo(big=True):
    if big:
        return '<img src=\'%s/big.png\' width=\'500\' height=\'32\' vspace=\'16\'>' % IMG_DIR
    return '<img src=\'%s/small.png\' width=\'220\' height=\'14\' vspace=\'16\'>' % IMG_DIR


def getPreferencesDir():
    preferencesFilePath = unicode_from_utf8(BigWorld.wg_getPreferencesFilePath())[1]
    return os.path.normpath(os.path.dirname(preferencesFilePath))


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
    path = os.path.join(getCachePath(), 'crewIgnored.json')
    if not os.path.exists(path):
        writeJsonFile(path, {'vehicles': []})
        return set()
    return set(openJsonFile(path).get('vehicles'))


ignored_vehicles = openIgnoredVehicles()


def updateIgnoredVehicles(vehicles):
    path = os.path.join(getCachePath(), 'crewIgnored.json')
    writeJsonFile(path, {'vehicles': sorted(vehicles)})


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'crewReturn': False,
            'crewTraining': False,
            'crewAutoReturn': False
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_crewReturn_text': 'Crew Auto-Return',
            'UI_setting_crewReturn_tooltip': 'Return crew tanks.',
            'UI_setting_crewTraining_text': 'Crew Training',
            'UI_setting_crewTraining_tooltip': 'Monitors whether \'Field Upgrade\' is upgraded/available and enables or disables \'Expedited Crew Training\' accordingly',
            'UI_setting_crewAutoReturn_text': 'Crew Return By Default',
            'UI_setting_crewAutoReturn_tooltip': '',
            # crew dialogs
            'UI_dialog_apply': 'Apply',
            'UI_dialog_cancel': 'Cancel',
            'UI_dialog_ignore': 'Ignore',
            #
            'UI_crewDialogs': {
                'enabled': '<br>Enable accelerated crew training?',
                'disabled': '<br>Disable accelerated crew training?',
                'notAvailable': 'Field upgrades are not available for this vehicle.',
                'isFullXp': 'You have accumulated the necessary amount of experience to fully upgrade the field upgrade.',
                'isFullComplete': 'You have pumped the field upgrade to the highest possible level.',
                'needTurnOff': 'You do not have field upgrades, it is recommended to disable accelerated crew training.'
            }
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('crewReturn'),
                self.tb.createControl('crewTraining'),
            ],
            'column2': [
                self.tb.createControl('crewAutoReturn')
            ]
        }


class DialogBase(object):
    appLoader = dependency.descriptor(IAppLoader)

    @property
    def view(self):
        app = self.appLoader.getApp()
        if app is not None and app.containerManager is not None:
            return app.containerManager.getView(WindowLayer.VIEW)
        return None


class CrewDialog(DialogBase):

    @wg_async
    def showCrewDialog(self, vehicleName, message):
        builder = InfoDialogBuilder()
        builder.setFormattedTitle(''.join((getLogo(), vehicleName)))
        builder.setFormattedMessage(message)
        builder.addButton(DialogButtons.SUBMIT, None, True, rawLabel=config.i18n['UI_dialog_apply'])
        builder.addButton(DialogButtons.CANCEL, None, False, rawLabel=config.i18n['UI_dialog_cancel'])
        builder.addButton(DialogButtons.PURCHASE, None, False, rawLabel=config.i18n['UI_dialog_ignore'])
        result = yield wg_await(dialogs.show(builder.build(self.view)))
        raise AsyncReturn(result)


class CrewWorker(object):
    appLoader = dependency.descriptor(IAppLoader)
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        self.intCD = None
        self.isDialogVisible = False
        g_events.onVehicleChangedDelayed += self.updateCrew
        override(ExchangeXPWindow, 'as_vehiclesDataChangedS', self.new_onXPExchangeDataChanged)

    @property
    def view(self):
        app = self.appLoader.getApp()
        if app is not None and app.containerManager is not None:
            return app.containerManager.getView(WindowLayer.VIEW)
        return None

    @staticmethod
    def getLocalizedMessage(value, description):
        dialog = config.i18n['UI_crewDialogs']
        return '\n'.join((dialog[description], dialog['enabled'] if value else dialog['disabled']))

    @wg_async
    def showDialog(self, vehicle, value, description):
        self.isDialogVisible = True
        message = self.getLocalizedMessage(value, description)
        dialog_result = yield wg_await(CrewDialog.showCrewDialog(vehicle.userName, message))
        if dialog_result.result == DialogButtons.SUBMIT:
            self.accelerateCrewXp(vehicle, value)
        elif dialog_result.result == DialogButtons.PURCHASE:
            ignored_vehicles.add(vehicle.userName)
            updateIgnoredVehicles(ignored_vehicles)
        self.isDialogVisible = False

    @decorators.adisp_process('updateTankmen')
    def accelerateCrewXp(self, vehicle, value):
        result = yield VehicleTmenXPAccelerator(vehicle, value, confirmationEnabled=False).request()
        if result.success:
            logInfo('The accelerated crew training is %s for \'%s\'' % (value, vehicle.userName))

    @staticmethod
    def isPostProgressionFullXP(vehicle):
        iterator = vehicle.postProgression.iterOrderedSteps()
        currentXP = vehicle.xp
        needToProgress = sum(x.getPrice().xp for x in iterator if not x.isRestricted() and not x.isReceived())
        logInfo('isPPFullXP - %s: %s/%s' % (vehicle.userName, currentXP, needToProgress))
        return currentXP >= needToProgress

    def isAccelerateTraining(self, vehicle):
        dialog = config.i18n['UI_crewDialogs']
        if not vehicle.postProgressionAvailability(unlockOnly=True).result:
            return True, dialog['notAvailable']
        elif vehicle.postProgression.getCompletion() is PostProgressionCompletion.FULL:
            return True, dialog['isFullXp']
        elif self.isPostProgressionFullXP(vehicle):
            return True, dialog['isFullComplete']
        else:
            return False, dialog['needTurnOff']

    def accelerateCrewTraining(self, vehicle):
        if vehicle.userName in ignored_vehicles or not vehicle.isElite:
            return
        acceleration, description = self.isAccelerateTraining(vehicle)
        if vehicle.isXPToTman != acceleration and not self.isDialogVisible:
            self.showDialog(vehicle, acceleration, description)

    def isCrewAvailable(self, vehicle):
        lastCrewIDs = vehicle.lastCrew
        if lastCrewIDs is None:
            return False
        for lastTankMenInvID in lastCrewIDs:
            actualLastTankMan = self.itemsCache.items.getTankman(lastTankMenInvID)
            if actualLastTankMan is not None and actualLastTankMan.isInTank:
                lastTankManVehicle = self.itemsCache.items.getVehicle(actualLastTankMan.vehicleInvID)
                if lastTankManVehicle and lastTankManVehicle.isLocked:
                    return False
        return True

    def updateCrew(self, vehicle):
        if vehicle is None or vehicle.isLocked or vehicle.isInBattle or vehicle.isCrewLocked:
            return
        if not config.data['enabled']:
            return
        if config.data['crewReturn'] and self.intCD != vehicle.intCD:
            if not vehicle.isCrewFull and self.isCrewAvailable(vehicle):
                self.processReturnCrew(vehicle)
            self.intCD = vehicle.intCD
        if config.data['crewTraining']:
            self.accelerateCrewTraining(vehicle)
        if config.data['crewAutoReturn']:
            self.processReturnCrewForVehicleSelectorPopup(vehicle)

    @decorators.adisp_process('crewReturning')
    def processReturnCrew(self, vehicle):
        result = yield TankmanReturn(vehicle).request()
        if result.userMsg:
            SystemMessages.pushI18nMessage(result.userMsg, type=result.sysMsgType)
            logInfo('%s: %s' % (vehicle.userName, result.userMsg))

    @decorators.adisp_process('crewReturning')
    def processReturnCrewForVehicleSelectorPopup(self, vehicle):
        if not (vehicle.isCrewFull or vehicle.isInBattle or vehicle.isLocked):
            yield TankmanReturn(vehicle).request()

    @decorators.adisp_process('unloading')
    def processUnloadCrew(self):
        result = yield TankmanUnload(g_currentVehicle.item.invID).request()
        if result.userMsg:
            SystemMessages.pushI18nMessage(result.userMsg, type=result.sysMsgType)
            logInfo('%s' % result.userMsg)

    def new_onXPExchangeDataChanged(self, func, b_self, data, *args, **kwargs):
        try:
            ID = 'id'
            CANDIDATE = 'isSelectCandidate'
            for vehicleData in data['vehicleList']:
                vehicle = self.itemsCache.items.getItemByCD(vehicleData[ID])
                check, _ = self.isAccelerateTraining(vehicle)
                vehicleData[CANDIDATE] &= check
        except Exception as error:
            logError('CrewProcessor onXPExchangeDataChanged: {}'.format(repr(error)))
        finally:
            return func(b_self, data, *args, **kwargs)


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')
