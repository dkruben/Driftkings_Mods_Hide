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

from DriftkingsCore import DriftkingsConfigInterface, Analytics, checkKeys, getPlayer, callback, cancelCallback, calculate_version

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


class ConfigInterface(DriftkingsConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.1.6 (%(file_compile_date)s)'
        self.author = ' (orig by spoter, refactored by DriftKings)'
        self.defaultKeys = {'buttonRepair': [Keys.KEY_SPACE], 'buttonChassis': [[Keys.KEY_LALT, Keys.KEY_RALT]]}
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
analytics = Analytics(config.ID, config.version)


class Repair(object):

    def __init__(self):
        self.player = None
        self.ctrl = None
        self.consumablesPanel = None
        self.battleStarted = False
        self._inputRetryCallback = None
        self._inputBound = False
        self.pendingAutoCallbacks = {}
        self.items = {
            'extinguisher': [251, 251, None, None],
            'medkit': [763, 1019, None, None],
            'repairkit': [1275, 1531, None, None]
        }
        self.base_markers = {
            'extinguisher': set(['handExtinguishers']),
            'medkit': set(['smallMedkit']),
            'repairkit': set(['smallRepairkit'])
        }
        self.gold_markers = {
            'extinguisher': set(['autoExtinguishers']),
            'medkit': set(['largeMedkit']),
            'repairkit': set(['largeRepairkit'])
        }
        self.complex_item = {
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
        self.chassis = ['chassis', 'leftTrack', 'rightTrack', 'leftTrack0', 'rightTrack0', 'leftTrack1', 'rightTrack1', 'wheel', 'wheel0', 'wheel1', 'wheel2', 'wheel3', 'wheel4', 'wheel5', 'wheel6', 'wheel7']
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED, self.__onComponentRegistered, EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_UNREGISTERED, self.__onComponentUnregistered, EVENT_BUS_SCOPE.GLOBAL)

    def startBattle(self):
        self.player = getPlayer()
        if self.player is None or not hasattr(self.player, 'guiSessionProvider'):
            return
        self.ctrl = self.player.guiSessionProvider.shared
        if self.ctrl is None or self.battleStarted:
            return
        self.battleStarted = True
        self._bindInputHandlers()
        # auto use
        if self.ctrl.vehicleState is not None:
            self.ctrl.vehicleState.onVehicleStateUpdated += self.autoUse
        # update equipments
        if self.ctrl.equipments is not None:
            self.ctrl.equipments.onEquipmentUpdated += self.onEquipmentUpdated
        self.checkBattleStarted()

    def stopBattle(self):
        self._unbindInputHandlers()
        # auto use
        if self.ctrl is not None and self.ctrl.vehicleState is not None:
            self.ctrl.vehicleState.onVehicleStateUpdated -= self.autoUse
        # update equipments
        if self.ctrl is not None and self.ctrl.equipments is not None:
            self.ctrl.equipments.onEquipmentUpdated -= self.onEquipmentUpdated
        #
        self.battleStarted = False
        self._clearPendingAutoCallbacks()
        for equipment_tag in self.items:
            self.items[equipment_tag][2] = None
            self.items[equipment_tag][3] = None
        self.items['repairkit'][1] = 1531
        self.player = None
        self.ctrl = None
        self.consumablesPanel = None

    def checkBattleStarted(self):
        if self.ctrl is None or self.player is None:
            return
        if hasattr(self.player, 'arena') and self.player.arena and self.player.arena.period == 3:
            self._refreshEquipmentCache()
        else:
            callback(0.1, self.checkBattleStarted)

    def useItem(self, equipment_tag, item=None):
        if not self._canUseConsumable():
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][0]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][0]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            self._activateEquipment(self.items[equipment_tag][0], item)
        else:
            if config.data['useGoldKits']:
                equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][1]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][1]) else None
                if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
                    self._activateEquipment(self.items[equipment_tag][1], item)

    def useItemManual(self, equipment_tag, item=None):
        if not self._canUseConsumable(requireControl=True):
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][0]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][0]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            self._activateEquipment(self.items[equipment_tag][0], item)

    def useItemGold(self, equipment_tag, item=None):
        if not self._canUseConsumable(requireControl=True):
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipment_tag][1]) if self.ctrl.equipments.hasEquipment(self.items[equipment_tag][1]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            self._activateEquipment(self.items[equipment_tag][1], item)

    def extinguishFire(self):
        if self.ctrl is None:
            return
        if self.ctrl.vehicleState.getStateValue(VEHICLE_VIEW_STATE.FIRE):
            equipment_tag = 'extinguisher'
            if self.items[equipment_tag][2]:
                self.useItemManual(equipment_tag)

    def removeStun(self):
        if self.ctrl is None:
            return
        if self.ctrl.vehicleState.getStateValue(VEHICLE_VIEW_STATE.STUN):
            equipment_tag = 'medkit'
            if self.items[equipment_tag][2]:
                self.useItemManual(equipment_tag)
            elif config.data['useGoldKits'] and self.items[equipment_tag][3]:
                self.useItemGold(equipment_tag)

    def repair(self, equipment_tag):
        if self.ctrl is None or self.player is None:
            return
        specific = self._getRepairPriority(equipment_tag)
        if config.data['useGoldKits'] and self.items[equipment_tag][3]:
            equipment = self.items[equipment_tag][3]
            if equipment is not None:
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state != DEVICE_STATE_NORMAL]
                result = []
                for device in devices:
                    if device in self.complex_item:
                        itemName = self.complex_item[device]
                    else:
                        itemName = device
                    if itemName in specific:
                        result.append(device)
                if len(result) > 1:
                    self.useItemGold(equipment_tag)
                elif result:
                    self.useItemGold(equipment_tag, result[0])
        elif self.items[equipment_tag][2]:
            equipment = self.items[equipment_tag][2]
            if equipment is not None:
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state != DEVICE_STATE_NORMAL]
                result = []
                for device in devices:
                    if device in self.complex_item:
                        itemName = self.complex_item[device]
                    else:
                        itemName = device
                    if itemName in specific:
                        result.append(device)
                if result:
                    self.useItemManual(equipment_tag, result[0])

    def repairAll(self):
        if self.ctrl is None:
            return
        self_vehicle = self.player.getVehicleAttached()
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
        self._refreshEquipmentCache()

    def repairChassis(self):
        if self.ctrl is None:
            return
        self_vehicle = self.player.getVehicleAttached()
        if self_vehicle is None:
            return
        if self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id:
            return
        equipment_tag = 'repairkit'
        for intCD, equipment in self.ctrl.equipments.iterEquipmentsByTag(equipment_tag):
            if equipment.isReady and equipment.isAvailableToUse:
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state == DEVICE_STATE_DESTROYED]
                for name in devices:
                    if name in self.chassis:
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
        if not self._canUseConsumable(requireControl=True):
            return
        time = self._getAutoDelay()
        if config.data['extinguishFire'] and state == VEHICLE_VIEW_STATE.FIRE and bool(value):
            self._scheduleAutoUse('extinguisher', time)
            time += 0.1

        if state == VEHICLE_VIEW_STATE.DEVICES:
            for deviceName, deviceState in self._extractDeviceUpdates(value):
                if deviceState in DEVICE_STATE_AS_DAMAGE:
                    itemName = self.complex_item.get(deviceName, deviceName)
                    equipmentTag = 'medkit' if itemName in TANKMEN_ROLES_ORDER_DICT['enum'] else 'repairkit'
                    # noinspection PyTypeChecker
                    specific = self._getRepairPriority(equipmentTag)
                    if itemName in specific:
                        if config.data['healCrew'] and equipmentTag == 'medkit':
                            self._scheduleAutoUse('medkit', time, deviceName)
                        if config.data['repairDevices'] and equipmentTag == 'repairkit':
                            self._scheduleAutoUse('repairkit', time, deviceName)
                            time += 0.1

        stunDuration = getattr(value, 'duration', None)
        hasStun = stunDuration > 0 if stunDuration is not None else bool(value)
        if config.data['removeStun'] and state == VEHICLE_VIEW_STATE.STUN and hasStun:
            self._scheduleAutoUse('medkit', time)

    def _canUseConsumable(self, requireControl=False):
        if not config.data['enabled']:
            return False
        replayCtrl = getattr(BattleReplay, 'g_replayCtrl', None)
        if replayCtrl is not None and replayCtrl.isPlaying:
            return False
        if self.ctrl is None or self.player is None:
            return False
        self_vehicle = self.player.getVehicleAttached()
        if self_vehicle is None:
            return False
        if requireControl and (self.ctrl.vehicleState is None or self.ctrl.vehicleState.getControllingVehicleID() != self_vehicle.id):
            return False
        return True

    def _activateEquipment(self, intCD, item=None):
        if self.ctrl is None or self.player is None:
            return False
        changeResult = self.ctrl.equipments.changeSetting(intCD, entityName=item, avatar=self.player)
        if isinstance(changeResult, tuple):
            result = bool(changeResult[0])
        else:
            result = bool(changeResult)
        if result:
            sound = SoundGroups.g_instance.getSound2D('vo_flt_repair')
            callback(1.0, sound.play)
        return result

    def _scheduleAutoUse(self, equipment_tag, delay, item=None):
        if equipment_tag in self.pendingAutoCallbacks:
            cancelCallback(self.pendingAutoCallbacks.pop(equipment_tag))
        self.pendingAutoCallbacks[equipment_tag] = callback(delay, partial(self._processAutoUse, equipment_tag, item))

    def _processAutoUse(self, equipment_tag, item=None):
        self.pendingAutoCallbacks.pop(equipment_tag, None)
        if not config.data['autoRepair'] or not self._canUseConsumable(requireControl=True):
            return
        if self.items[equipment_tag][2] is None and self.items[equipment_tag][3] is None:
            self._refreshEquipmentCache()
        self.useItem(equipment_tag, item)

    def _clearPendingAutoCallbacks(self):
        for callbackID in self.pendingAutoCallbacks.values():
            cancelCallback(callbackID)
        self.pendingAutoCallbacks.clear()

    def _bindInputHandlers(self):
        if self._inputRetryCallback is not None:
            cancelCallback(self._inputRetryCallback)
            self._inputRetryCallback = None
        if InputHandler.g_instance is None:
            self._inputRetryCallback = callback(0.2, self._bindInputHandlers)
            return
        if not self._inputBound:
            InputHandler.g_instance.onKeyDown += self.onHotkeyPressed
            InputHandler.g_instance.onKeyUp += self.onHotkeyPressed
            self._inputBound = True

    def _unbindInputHandlers(self):
        if self._inputRetryCallback is not None:
            cancelCallback(self._inputRetryCallback)
            self._inputRetryCallback = None
        if self._inputBound and InputHandler.g_instance is not None:
            InputHandler.g_instance.onKeyDown -= self.onHotkeyPressed
            InputHandler.g_instance.onKeyUp -= self.onHotkeyPressed
        self._inputBound = False

    def _getRepairPriority(self, equipment_tag):
        vehicle_class = Vehicle.getVehicleClassTag(self.player.vehicleTypeDescriptor.type.tags)
        priorities = config.data['repairPriority']
        class_priorities = priorities.get(vehicle_class, priorities['AllAvailableVariables'])
        return class_priorities[equipment_tag]

    def _refreshEquipmentCache(self):
        if self.ctrl is None or self.ctrl.equipments is None:
            return
        for equipment_tag in self.items:
            self.items[equipment_tag][2] = None
            self.items[equipment_tag][3] = None
            for intCD, equipment in self.ctrl.equipments.iterEquipmentsByTag(equipment_tag):
                marker = self._getEquipmentMarker(equipment)
                if marker in self.base_markers[equipment_tag] and self.items[equipment_tag][2] is None:
                    self.items[equipment_tag][0] = intCD
                    self.items[equipment_tag][2] = equipment
                    continue
                if marker in self.gold_markers[equipment_tag] and self.items[equipment_tag][3] is None:
                    self.items[equipment_tag][1] = intCD
                    self.items[equipment_tag][3] = equipment
                    continue
                if self.items[equipment_tag][2] is None:
                    self.items[equipment_tag][0] = intCD
                    self.items[equipment_tag][2] = equipment
                elif self.items[equipment_tag][3] is None:
                    self.items[equipment_tag][1] = intCD
                    self.items[equipment_tag][3] = equipment

    @staticmethod
    def _extractDeviceUpdates(value):
        updates = []
        if isinstance(value, dict):
            iterable = value.itervalues() if hasattr(value, 'itervalues') else value.values()
        elif isinstance(value, (list, tuple)):
            if len(value) >= 2 and isinstance(value[0], string_types):
                iterable = (value,)
            else:
                iterable = value
        else:
            iterable = ()

        for entry in iterable:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2 and isinstance(entry[0], string_types):
                updates.append((entry[0], entry[1]))
        return updates

    @staticmethod
    def _getAutoDelay():
        min_delay = config.data.get('timerMin', 0.3)
        max_delay = config.data.get('timerMax', 0.8)
        try:
            min_delay = float(min_delay)
        except (TypeError, ValueError):
            min_delay = 0.3
        try:
            max_delay = float(max_delay)
        except (TypeError, ValueError):
            max_delay = 0.8
        if min_delay > max_delay:
            min_delay, max_delay = max_delay, min_delay
        return random.uniform(min_delay, max_delay)

    @staticmethod
    def _getEquipmentMarker(equipment):
        getter = getattr(equipment, 'getMarker', None)
        if callable(getter):
            return getter()
        return None

    def __onComponentRegistered(self, event):
        if event.alias == BATTLE_VIEW_ALIASES.CONSUMABLES_PANEL:
            self.consumablesPanel = event.componentPy
            self.startBattle()

    def __onComponentUnregistered(self, event):
        if event.alias == BATTLE_VIEW_ALIASES.CONSUMABLES_PANEL:
            self.stopBattle()


g_repairExtended = Repair()
