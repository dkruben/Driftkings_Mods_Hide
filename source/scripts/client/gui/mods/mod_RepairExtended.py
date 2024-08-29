# -*- coding: utf-8 -*-
import random
from functools import partial

import BattleReplay
import Keys
import SoundGroups
from gui import InputHandler
from gui import TANKMEN_ROLES_ORDER_DICT
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.battle_control.battle_constants import DEVICE_STATE_AS_DAMAGE
from gui.battle_control.battle_constants import DEVICE_STATE_DESTROYED, VEHICLE_VIEW_STATE, DEVICE_STATE_NORMAL
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
from gui.shared.gui_items import Vehicle
from gui.shared.personality import ServicesLocator

from DriftkingsCore import SimpleConfigInterface, Analytics, checkKeys, getPlayer, callback, calculate_version

COMPLEX_ITEM = {
    'leftTrack0': 'chassis',
    'rightTrack0': 'chassis',
    'leftTrack1': 'chassis',
    'rightTrack1': 'chassis',
    'gunner1': 'gunner',
    'gunner2': 'gunner',
    'radioman1': 'radioman',
    'radioman2': 'radioman',
    'loader1': 'loader',
    'loader2': 'loader',
    'wheel0': 'wheel',
    'wheel1': 'wheel',
    'wheel2': 'wheel',
    'wheel3': 'wheel',
    'wheel4': 'wheel',
    'wheel5': 'wheel',
    'wheel6': 'wheel',
    'wheel7': 'wheel'
}

CHASSIS = ['chassis', 'leftTrack', 'rightTrack', 'leftTrack0', 'rightTrack0', 'leftTrack1', 'rightTrack1', 'wheel', 'wheel0', 'wheel1', 'wheel2', 'wheel3', 'wheel4', 'wheel5', 'wheel6', 'wheel7']


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.0.0 (%(file_compile_date)s)'
        self.author = ' (orig by spoter)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.defaultKeys = {
            'buttonRepair': [Keys.KEY_SPACE],
            'buttonChassis': [[Keys.KEY_LALT, Keys.KEY_RALT]]
        }
        self.data = {
            'enabled': True,
            'buttonChassis': self.defaultKeys['buttonChassis'],
            'buttonRepair': self.defaultKeys['buttonRepair'],
            'autoRepair': True,
            'removeStun': True,
            'extinguishFire': True,
            'healCrew': True,
            'repairDevices': True,
            'restoreChassis': False,
            'useGoldKits': True,
            'timerMin': 0.3,
            'timerMax': 0.8,
            'repairPriority': {
                'lightTank': {
                    'medkit': ['driver', 'commander', 'gunner', 'loader'],
                    'repairkit': ['engine', 'ammoBay', 'gun', 'turretRotator', 'fuelTank']
                },
                'mediumTank': {
                    'medkit': ['loader', 'driver', 'commander', 'gunner'],
                    'repairkit': ['turretRotator', 'engine', 'ammoBay', 'gun', 'fuelTank']
                },
                'heavyTank': {
                    'medkit': ['commander', 'loader', 'gunner', 'driver'],
                    'repairkit': ['turretRotator', 'ammoBay', 'engine', 'gun', 'fuelTank']
                },
                'SPG': {
                    'medkit': ['commander', 'loader', 'gunner', 'driver'],
                    'repairkit': ['ammoBay', 'engine', 'gun', 'turretRotator', 'fuelTank']
                },
                'AT-SPG': {
                    'medkit': ['loader', 'gunner', 'commander', 'driver'],
                    'repairkit': ['ammoBay', 'gun', 'engine', 'turretRotator', 'fuelTank']
                },
                'AllAvailableVariables': {
                    'medkit': ['commander', 'gunner', 'driver', 'radioman', 'loader'],
                    'repairkit': ['engine', 'ammoBay', 'gun', 'turretRotator', 'chassis', 'surveyingDevice', 'radio', 'fuelTank', 'wheel']
                }
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_buttonChassis_text': 'Button: Restore Chassis',
            'UI_setting_buttonChassis_tooltip': '',
            'UI_setting_buttonRepair_text': 'Button: Smart Repair',
            'UI_setting_buttonRepair_tooltip': '',
            'UI_setting_removeStun_text': 'Remove stun',
            'UI_setting_removeStun_tooltip': '',
            'UI_setting_useGoldKits_text': 'Use Gold Kits',
            'UI_setting_useGoldKits_tooltip': '',
            'UI_setting_timerMin_text': 'Min delay auto usage',
            'UI_setting_timerMin_format': ' sec.',
            'UI_setting_timerMax_text': 'Max delay auto usage',
            'UI_setting_timerMax_format': ' sec.',
            'UI_setting_extinguishFire_text': 'Extinguish fire',
            'UI_setting_extinguishFire_tooltip': '',
            'UI_setting_healCrew_text': 'Heal crew',
            'UI_setting_healCrew_tooltip': '',
            'UI_setting_restoreChassis_text': 'Restore chassis',
            'UI_setting_restoreChassis_tooltip': '',
            'UI_setting_repairDevices_text': 'Repair devices',
            'UI_setting_repairDevices_tooltip': '',
            'UI_setting_autoRepair_text': 'Auto usage',
            'UI_setting_autoRepair_tooltip': ''
        }

        super(ConfigInterface, self).init()

    def createTemplate(self):
        xMin = self.i18n['UI_setting_timerMin_format']
        xMax = self.i18n['UI_setting_timerMax_format']
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createHotKey('buttonChassis'),
                self.tb.createHotKey('buttonRepair'),
                self.tb.createControl('useGoldKits'),
                self.tb.createControl('autoRepair'),
                self.tb.createSlider('timerMin', 0.1, 0.5, 0.1, '{{value}}%s' % xMin),
                self.tb.createSlider('timerMax', 0.6, 3.0, 0.1, '{{value}}%s' % xMax)
            ],
            'column2': [
                self.tb.createControl('restoreChassis'),
                self.tb.createControl('removeStun'),
                self.tb.createControl('extinguishFire'),
                self.tb.createControl('healCrew'),
                self.tb.createControl('repairDevices')
            ]
        }


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class Repair(object):

    def __init__(self):
        self.ctrl = None
        # self.vehicleCtrl = None
        self.consumablesPanel = None
        self.items = {
            'extinguisher': [251, 251, None, None],
            'medkit': [763, 1019, None, None],
            'repairkit': [1275, 1531, None, None]
        }
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED, self.__onComponentRegistered, EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_UNREGISTERED, self.__onComponentUnregistered, EVENT_BUS_SCOPE.GLOBAL)

    def startBattle(self):
        #
        self.ctrl = getPlayer().guiSessionProvider.shared
        #
        InputHandler.g_instance.onKeyDown += self.onHotkeyPressed
        InputHandler.g_instance.onKeyUp += self.onHotkeyPressed
        # auto use
        if self.ctrl.vehicleState is not None:
            self.ctrl.vehicleState.onVehicleStateUpdated += self.autoUse
        # update equipments
        if self.ctrl.equipments is not None:
            self.ctrl.equipments.onEquipmentUpdated += self.onEquipmentUpdated
        #
        self.checkBattleStarted()

    def stopBattle(self):
        InputHandler.g_instance.onKeyDown -= self.onHotkeyPressed
        InputHandler.g_instance.onKeyUp -= self.onHotkeyPressed
        # auto use
        if self.ctrl.vehicleState is not None:
            self.ctrl.vehicleState.onVehicleStateUpdated -= self.autoUse
        # update equipments
        if self.ctrl.equipments is not None:
            self.ctrl.equipments.onEquipmentUpdated -= self.onEquipmentUpdated
        #
        for equipment_tag in self.items:
            self.items[equipment_tag][2] = None
            self.items[equipment_tag][3] = None
        self.items['repairkit'][1] = 1531

    def checkBattleStarted(self):
        if hasattr(getPlayer(), 'arena') and getPlayer().arena.period is 3:
            for equipment_tag in self.items:
                self.items[equipment_tag][2] = self.ctrl.equipments.getEquipment(self.items[equipment_tag][0]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][0]) else None
                self.items[equipment_tag][3] = self.ctrl.equipments.getEquipment(self.items[equipment_tag][1]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][1]) else None
            equipment_tag = 'repairkit'
            if self.ctrl.equipments.hasEquipment(46331):
                self.items[equipment_tag][1] = 46331
                self.items[equipment_tag][3] = self.ctrl.equipments.getEquipment(self.items[equipment_tag][1]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][1]) else None
        else:
            callback(0.1, self.checkBattleStarted)

    def useItem(self, equipment_tag, item=None):
        if not config.data['enabled']:
            return
        if BattleReplay.g_replayCtrl.isPlaying:
            return
        if self.ctrl is None:
            return
        self_vehicle = getPlayer().getVehicleAttached()
        if self_vehicle is None:
            return
        sound = False
        equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][0]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][0]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            # noinspection PyProtectedMember
            self.consumablesPanel._handleEquipmentPressed(self.items[equipment_tag][0], item)
            sound = True
        else:
            if config.data['useGoldKits']:
                equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][1]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][1]) else None
                if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
                    # noinspection PyProtectedMember
                    self.consumablesPanel._handleEquipmentPressed(self.items[equipment_tag][1])
                    sound = True
        if sound:
            sound = SoundGroups.g_instance.getSound2D('vo_flt_repair')
            callback(1.0, sound.play)

    def useItemManual(self, equipment_tag, item=None):
        if not config.data['enabled']:
            return
        if BattleReplay.g_replayCtrl.isPlaying:
            return
        if self.ctrl is None:
            return
        self_vehicle = getPlayer().getVehicleAttached()
        if self_vehicle is None:
            return
        if self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id:
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][0]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][0]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            # noinspection PyProtectedMember
            self.consumablesPanel._handleEquipmentPressed(self.items[equipment_tag][0], item)
            sound = SoundGroups.g_instance.getSound2D('vo_flt_repair')
            callback(1.0, sound.play)

    def useItemGold(self, equipment_tag):
        if not config.data['enabled']:
            return
        if BattleReplay.g_replayCtrl.isPlaying:
            return
        if self.ctrl is None:
            return
        self_vehicle = getPlayer().getVehicleAttached()
        if self_vehicle is None:
            return
        if self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id:
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][1]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][1]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            # noinspection PyProtectedMember
            self.consumablesPanel._handleEquipmentPressed(self.items[equipment_tag][1])
            sound = SoundGroups.g_instance.getSound2D('vo_flt_repair')
            callback(1.0, sound.play)

    def extinguishFire(self):
        if self.ctrl.vehicleState.getStateValue(VEHICLE_VIEW_STATE.FIRE):
            equipment_tag = 'extinguisher'
            if self.items[equipment_tag][2]:
                self.useItemManual(equipment_tag)

    def removeStun(self):
        if self.ctrl.vehicleState.getStateValue(VEHICLE_VIEW_STATE.STUN):
            equipment_tag = 'medkit'
            if self.items[equipment_tag][2]:
                self.useItemManual(equipment_tag)
            elif config.data['useGoldKits'] and self.items[equipment_tag][3]:
                self.useItemGold(equipment_tag)

    def repair(self, equipment_tag):
        specific = config.data['repairPriority'][Vehicle.getVehicleClassTag(getPlayer().vehicleTypeDescriptor.type.tags)][equipment_tag]
        if config.data['useGoldKits'] and self.items[equipment_tag][3]:
            equipment = self.items[equipment_tag][3]
            if equipment is not None:
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state != DEVICE_STATE_NORMAL]
                result = []
                for device in devices:
                    if device in COMPLEX_ITEM:
                        itemName = COMPLEX_ITEM[device]
                    else:
                        itemName = device
                    if itemName in specific:
                        result.append(device)
                if len(result) > 1:
                    self.useItemGold(equipment_tag)
                elif result:
                    self.useItemManual(equipment_tag, result[0])
        elif self.items[equipment_tag][2]:
            equipment = self.items[equipment_tag][2]
            if equipment is not None:
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state != DEVICE_STATE_NORMAL]
                result = []
                for device in devices:
                    if device in COMPLEX_ITEM:
                        itemName = COMPLEX_ITEM[device]
                    else:
                        itemName = device
                    if itemName in specific:
                        result.append(device)
                if len(result) > 1:
                    self.useItemGold(equipment_tag)
                elif result:
                    self.useItemManual(equipment_tag, result[0])

    def repairAll(self):
        if self.ctrl is None:
            return
        self_vehicle = getPlayer().getVehicleAttached()
        if self_vehicle is None:
            return
        if self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id:
            return
        if config.data['extinguishFire']:
            self.extinguishFire()
        if config.data['repairDevices']:
            self.repair('repairkit')
        if config.data['healCrew']:
            self.repair('medkit')
        if config.data['removeStun']:
            self.removeStun()
        if config.data['restoreChassis']:
            self.repairChassis()

    def onEquipmentUpdated(self, *_):
        self.repairAll()

    def repairChassis(self):
        if self.ctrl is None:
            return
        self_vehicle = getPlayer().getVehicleAttached()
        if self_vehicle is None:
            return
        if self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id:
            return
        equipment_tag = 'repairkit'
        for intCD, equipment in self.ctrl.equipments.iterEquipmentsByTag(equipment_tag):
            if equipment.isReady and equipment.isAvailableToUse:
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state in DEVICE_STATE_DESTROYED]
                for name in devices:
                    if name in CHASSIS:
                        self.useItem(equipment_tag, name)
                        return

    def onHotkeyPressed(self, event):
        if ServicesLocator.appLoader.getDefBattleApp():
            if checkKeys(config.data['buttonChassis']) and event.isKeyDown():
                self.repairChassis()
            if checkKeys(config.data['buttonRepair']) and event.isKeyDown():
                self.repairAll()

    def autoUse(self, state, value):
        if not config.data['autoRepair']:
            return
        if self.ctrl is None:
            return
        self_vehicle = getPlayer().getVehicleAttached()
        if self_vehicle is None:
            return
        if self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id:
            return
        time = random.uniform(config.data['timerMin'], config.data['timerMax'])
        if config.data['extinguishFire'] and state == VEHICLE_VIEW_STATE.FIRE:
            callback(time, partial(self.useItem, 'extinguisher'))
            time += 0.1

        if state == VEHICLE_VIEW_STATE.DEVICES:
            deviceName, deviceState, actualState = value
            if deviceState in DEVICE_STATE_AS_DAMAGE:
                if deviceName in COMPLEX_ITEM:
                    itemName = COMPLEX_ITEM[deviceName]
                else:
                    itemName = deviceName
                equipment_tag = 'medkit' if deviceName in TANKMEN_ROLES_ORDER_DICT['enum'] else 'repairkit'
                specific = config.data['repairPriority'][Vehicle.getVehicleClassTag(getPlayer().vehicleTypeDescriptor.type.tags)][equipment_tag]
                if itemName in specific:
                    if config.data['healCrew'] and equipment_tag == 'medkit':
                        callback(time, partial(self.useItem, 'medkit', deviceName))
                    if config.data['repairDevices'] and equipment_tag == 'repairkit':
                        callback(time, partial(self.useItem, 'repairkit', deviceName))
                        time += 0.1

        if config.data['removeStun'] and state == VEHICLE_VIEW_STATE.STUN:
            callback(time, partial(self.useItem, 'medkit'))

    def __onComponentRegistered(self, event):
        if event.alias == BATTLE_VIEW_ALIASES.CONSUMABLES_PANEL:
            self.consumablesPanel = event.componentPy
            self.startBattle()

    def __onComponentUnregistered(self, event):
        if event.alias == BATTLE_VIEW_ALIASES.CONSUMABLES_PANEL:
            self.stopBattle()


Repair()
