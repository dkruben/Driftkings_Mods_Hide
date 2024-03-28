# -*- coding: utf-8 -*-
import random
from collections import OrderedDict
from functools import partial

import BattleReplay
import Keys
import SoundGroups
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
from Avatar import PlayerAvatar
from gui import InputHandler
from gui import TANKMEN_ROLES_ORDER_DICT
from gui.Scaleform.daapi.view.battle.shared.consumables_panel import ConsumablesPanel
from gui.battle_control.battle_constants import DEVICE_STATE_AS_DAMAGE, DEVICE_STATE_DESTROYED, VEHICLE_VIEW_STATE, DEVICE_STATE_NORMAL
from gui.shared.gui_items import Vehicle
from gui.shared.personality import ServicesLocator
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import SimpleConfigInterface, Analytics, checkKeys, getPlayer, callback, override


class ConfigInterface(SimpleConfigInterface):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.battle_ctrl = self.sessionProvider.shared.vehicleState
        self.consumablesPanel = None
        self.ctrl = None
        self.items = {
            'extinguisher': [251, 251, None, None],
            'medkit': [763, 1019, None, None],
            'repairkit': [1275, 1531, None, None]
        }
        self.complex_item = OrderedDict(
            {
                ('leftTrack', 'chassis'),
                ('rightTrack', 'chassis'),
                ('gunner1', 'gunner'),
                ('gunner2', 'gunner'),
                ('radioman1', 'radioman'),
                ('radioman2', 'radioman'),
                ('loader1', 'loader'),
                ('loader2', 'loader'),
                ('wheel0', 'wheel'),
                ('wheel1', 'wheel'),
                ('wheel2', 'wheel'),
                ('wheel3', 'wheel'),
                ('wheel4', 'wheel'),
                ('wheel5', 'wheel'),
                ('wheel6', 'wheel'),
                ('wheel7', 'wheel')
            }
        )
        self.chassis = ['chassis', 'leftTrack', 'rightTrack', 'wheel', 'wheel0', 'wheel1', 'wheel2', 'wheel3', 'wheel4', 'wheel5', 'wheel6', 'wheel7']
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED, self.__onComponentRegistered, EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_UNREGISTERED, self.__onComponentUnregistered, EVENT_BUS_SCOPE.GLOBAL)
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.9.5 (%(file_compile_date)s)'
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
            'UI_message_enabled': 'Enable|Disable Options.',
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
            'settingsVersion': 1,
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
            ]}

    def startBattle(self):
        self.ctrl = getPlayer().guiSessionProvider.shared
        InputHandler.g_instance.onKeyDown += self.onHotkeyPressed
        InputHandler.g_instance.onKeyUp += self.onHotkeyPressed
        if self.battle_ctrl is not None:
            self.battle_ctrl.onVehicleStateUpdated += self.autoUse
        if self.ctrl.equipments is not None:
            self.ctrl.equipments.onEquipmentUpdated += self.onEquipmentUpdated
        self.checkBattleStarted()

    def stopBattle(self):
        InputHandler.g_instance.onKeyDown -= self.onHotkeyPressed
        InputHandler.g_instance.onKeyUp -= self.onHotkeyPressed
        if self.battle_ctrl is not None:
            self.battle_ctrl.onVehicleStateUpdated -= self.autoUse
        if self.ctrl.equipments is not None:
            self.ctrl.equipments.onEquipmentUpdated -= self.onEquipmentUpdated
        for equipmentTag in self.items:
            self.items[equipmentTag][2] = None
            self.items[equipmentTag][3] = None

    def checkBattleStarted(self):
        if hasattr(getPlayer(), 'arena') and getPlayer().arena.period is 3:
            for equipmentTag in self.items:
                self.items[equipmentTag][2] = self.ctrl.equipments.getEquipment(
                    self.items[equipmentTag][0]) if self.ctrl.equipments.hasEquipment(
                    self.items[equipmentTag][0]) else None
                self.items[equipmentTag][3] = self.ctrl.equipments.getEquipment(
                    self.items[equipmentTag][1]) if self.ctrl.equipments.hasEquipment(
                    self.items[equipmentTag][1]) else None
        else:
            callback(0.1, self.checkBattleStarted)

    def useItem(self, equipmentTag, item=None):
        if not self.data['enabled']:
            return
        if BattleReplay.g_replayCtrl.isPlaying:
            return
        if self.ctrl is None:
            return

        sound = False
        equipment = self.ctrl.equipments.getEquipment(self.items[equipmentTag][0]) if self.ctrl.equipments.hasEquipment(
            self.items[equipmentTag][0]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            # noinspection PyProtectedMember
            self.consumablesPanel._handleEquipmentPressed(self.items[equipmentTag][0], item)
            sound = True
        else:
            if self.data['useGoldKits']:
                equipment = self.ctrl.equipments.getEquipment(
                    self.items[equipmentTag][1]) if self.ctrl.equipments.hasEquipment(
                    self.items[equipmentTag][1]) else None
                if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
                    # noinspection PyProtectedMember
                    self.consumablesPanel._handleEquipmentPressed(self.items[equipmentTag][1])
                    sound = True
        if sound:
            sound = SoundGroups.g_instance.getSound2D('vo_flt_repair')
            callback(1.0, sound.play)

    def useItemManual(self, equipmentTag, item=None):
        if not self.data['enabled']:
            return
        if BattleReplay.g_replayCtrl.isPlaying:
            return
        if self.ctrl is None:
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipmentTag][0]) if self.ctrl.equipments.hasEquipment(
            self.items[equipmentTag][0]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            # noinspection PyProtectedMember
            self.consumablesPanel._handleEquipmentPressed(self.items[equipmentTag][0], item)
            sound = SoundGroups.g_instance.getSound2D('vo_flt_repair')
            callback(1.0, sound.play)

    def useItemGold(self, equipmentTag):
        if not self.data['enabled']:
            return
        if BattleReplay.g_replayCtrl.isPlaying:
            return
        if self.ctrl is None:
            return
        equipment = self.ctrl.equipments.getEquipment(self.items[equipmentTag][1]) if self.ctrl.equipments.hasEquipment(
            self.items[equipmentTag][1]) else None
        if equipment is not None and equipment.isReady and equipment.isAvailableToUse:
            # noinspection PyProtectedMember
            self.consumablesPanel._handleEquipmentPressed(self.items[equipmentTag][1])
            sound = SoundGroups.g_instance.getSound2D('vo_flt_repair')
            callback(1.0, sound.play)

    def extinguishFire(self):
        if self.ctrl.vehicleState.getStateValue(VEHICLE_VIEW_STATE.FIRE):
            equipmentTag = 'extinguisher'
            if self.items[equipmentTag][2]:
                self.useItemManual(equipmentTag)

    def removeStun(self):
        if self.ctrl.vehicleState.getStateValue(VEHICLE_VIEW_STATE.STUN):
            equipmentTag = 'medkit'
            if self.items[equipmentTag][2]:
                self.useItemManual(equipmentTag)
            elif self.data['useGoldKits'] and self.items[equipmentTag][3]:
                self.useItemGold(equipmentTag)

    def repair(self, equipmentTag):
        specific = self.data['repairPriority'][Vehicle.getVehicleClassTag(getPlayer().vehicleTypeDescriptor.type.tags)][equipmentTag]
        if self.data['useGoldKits'] and self.items[equipmentTag][3]:
            equipment = self.items[equipmentTag][3]
            if equipment is not None:
                # noinspection PyUnresolvedReferences
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state != DEVICE_STATE_NORMAL]
                result = []
                for device in specific:
                    if device in self.complex_item:
                        itemName = self.complex_item[device]
                    else:
                        itemName = device
                    if itemName in devices:
                        result.append(device)
                if len(result) > 1:
                    self.useItemGold(equipmentTag)
                elif result:
                    self.useItemManual(equipmentTag, result[0])
        elif self.items[equipmentTag][2]:
            equipment = self.items[equipmentTag][2]
            if equipment is not None:
                # noinspection PyUnresolvedReferences
                devices = [name for name, state in equipment.getEntitiesIterator() if state and state != DEVICE_STATE_NORMAL]
                result = []
                for device in specific:
                    if device in self.complex_item:
                        itemName = self.complex_item[device]
                    else:
                        itemName = device
                    if itemName in devices:
                        result.append(device)
                if len(result) > 1:
                    self.useItemGold(equipmentTag)
                elif result:
                    self.useItemManual(equipmentTag, result[0])

    def repairAll(self):
        if self.ctrl is None:
            return
        if self.data['extinguishFire']:
            self.extinguishFire()
        if self.data['repairDevices']:
            self.repair('repairkit')
        if self.data['healCrew']:
            self.repair('medkit')
        if self.data['removeStun']:
            self.removeStun()
        if self.data['restoreChassis']:
            self.repairChassis()

    # noinspection PyUnusedLocal
    def onEquipmentUpdated(self, *args):
        self.repairAll()

    def repairChassis(self):
        if self.ctrl is None:
            return
        equipmentTag = 'repairkit'
        for intCD, equipment in self.ctrl.equipments.iterEquipmentsByTag(equipmentTag):
            if equipment.isReady and equipment.isAvailableToUse:
                devices = [name for name, state in equipment.getEntitiesIterator() if
                           state and state in DEVICE_STATE_DESTROYED]
                for name in devices:
                    if name in self.chassis:
                        self.useItem(equipmentTag, name)
                        return

    def onHotkeyPressed(self, event):
        if ServicesLocator.appLoader.getDefBattleApp():
            if checkKeys(self.data['buttonChassis']) and event.isKeyDown():
                self.repairChassis()
            if checkKeys(self.data['buttonRepair']) and event.isKeyDown():
                self.repairAll()

    def __onComponentRegistered(self, event):
        if event.alias == BATTLE_VIEW_ALIASES.CONSUMABLES_PANEL:
            self.consumablesPanel = event.componentPy
            self.startBattle()

    def __onComponentUnregistered(self, event):
        if event.alias == BATTLE_VIEW_ALIASES.CONSUMABLES_PANEL:
            self.stopBattle()

    def autoUse(self, state, value):
        if not self.data['autoRepair']:
            return
        if self.ctrl is None:
            return
        time = random.uniform(self.data['timerMin'], self.data['timerMax'])
        if self.data['extinguishFire'] and state == VEHICLE_VIEW_STATE.FIRE:
            callback(time, partial(self.useItem, 'extinguisher'))
            time += 0.1

        if state == VEHICLE_VIEW_STATE.DEVICES:
            deviceName, deviceState, actualState = value
            if deviceState in DEVICE_STATE_AS_DAMAGE:
                if deviceName in self.complex_item:
                    itemName = self.complex_item[deviceName]
                else:
                    itemName = deviceName
                equipmentTag = 'medkit' if deviceName in TANKMEN_ROLES_ORDER_DICT['enum'] else 'repairkit'
                # noinspection PyTypeChecker
                specific = self.data['repairPriority'][Vehicle.getVehicleClassTag(getPlayer().vehicleTypeDescriptor.type.tags)][equipmentTag]
                if itemName in specific:
                    if self.data['healCrew'] and equipmentTag == 'medkit':
                        callback(time, partial(self.useItem, 'medkit', deviceName))
                    if self.data['repairDevices'] and equipmentTag == 'repairkit':
                        callback(time, partial(self.useItem, 'repairkit', deviceName))
                        time += 0.1

        if self.data['removeStun'] and state == VEHICLE_VIEW_STATE.STUN:
            callback(time, partial(self.useItem, 'medkit'))


g_config = ConfigInterface()
analytics = Analytics(g_config.ID, g_config.version, 'UA-121940539-1')


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    g_config.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    g_config.stopBattle()


@override(ConsumablesPanel, '_onEquipmentAdded')
def new_onEquipmentAdded(func, *args):
    func(*args)
    g_config.consumablesPanel = args[0]
