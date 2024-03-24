# -*- coding: utf-8 -*-
import codecs
import collections
import json
import os
import threading
from Queue import Queue
from functools import partial

import Keys
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from CurrentVehicle import g_currentVehicle
from PlayerEvents import g_playerEvents
from constants import ARENA_BONUS_TYPE
from gui import InputHandler
from gui.Scaleform.daapi.view.lobby.LobbyView import LobbyView
from gui.impl.lobby.crew.widget.crew_widget import CrewWidget
from gui.battle_control.arena_info import vos_collections
from gui.battle_control.battle_constants import VEHICLE_DEVICE_IN_COMPLEX_ITEM, VEHICLE_VIEW_STATE
from gui.battle_control.controllers import feedback_events
from gui.shared.personality import ServicesLocator
from messenger.formatters.service_channel import BattleResultsFormatter

from DriftkingsCore import SimpleConfigInterface, Analytics, override, logError, callback, getPlayer, getEntity


CHASSIS_ALL_ITEMS = frozenset(VEHICLE_DEVICE_IN_COMPLEX_ITEM.keys() + VEHICLE_DEVICE_IN_COMPLEX_ITEM.values())
DAMAGE_EVENTS = frozenset([BATTLE_EVENT_TYPE.RADIO_ASSIST, BATTLE_EVENT_TYPE.TRACK_ASSIST, BATTLE_EVENT_TYPE.STUN_ASSIST, BATTLE_EVENT_TYPE.DAMAGE, BATTLE_EVENT_TYPE.TANKING, BATTLE_EVENT_TYPE.RECEIVED_DAMAGE])


class ConfigInterface(SimpleConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'battleShow': True,
            'hangarShow': True,
            'battlePos': {'x': 60, 'y': -255},
            'lobbyPos': {'x': 325, 'y': 505}
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_label_text': 'Calculator Credits in Battle, +1000 or -1000 silver difference: that\'s normal dispersion, if greater: Play one battle without damage.',
            'UI_setting_label1_text': 'Wait until the battle is complete without escape into the hangar. Income: Green Victory, Red Defeat, Outcome: ammo and consumables.',
            'UI_setting_label2_text': 'Additional info in battle: Press Alt and Control buttons',

            'UI_setting_hangarShow_text': 'Show in hangar',
            'UI_setting_hangarShow_tooltip': '',
            'UI_setting_battleShow_text': 'Show in battle',
            'UI_setting_battleShow_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        infoSLabel = self.tb.createLabel('label')
        infoSLabel['text'] += ''

        infoSLabel1 = self.tb.createLabel('label1')
        infoSLabel1['text'] += ''

        infoSLabel2 = self.tb.createLabel('label2')
        infoSLabel2['text'] += ''
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('hangarShow'),
                self.tb.createControl('battleShow'),
                infoSLabel,
                infoSLabel1,
                infoSLabel2
            ],
            'column2': []
        }


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class MyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        super(MyJSONEncoder, self).__init__(*args, **kwargs)
        self.current_indent = 0
        self.current_indent_str = ''
        self.indent = 4

    def encode(self, o):
        if isinstance(o, (list, tuple)):
            primitives_only = True
            for item in o:
                if isinstance(item, (list, tuple, dict)):
                    primitives_only = False
                    break
            output = []
            if primitives_only:
                for item in o:
                    output.append(json.dumps(item, ensure_ascii=False, encoding='utf-8-sig'))
                return '[ ' + ', '.join(output) + ' ]'
            else:
                self.current_indent += self.indent
                self.current_indent_str = ''.join([' ' for i in range(self.current_indent)])
                for item in o:
                    output.append(self.current_indent_str + self.encode(item))
                self.current_indent -= self.indent
                self.current_indent_str = ''.join([' ' for i in range(self.current_indent)])
                return '[\n' + ',\n'.join(output) + '\n' + self.current_indent_str + ']'
        elif isinstance(o, dict):
            output = []
            self.current_indent += self.indent
            self.current_indent_str = ''.join([' ' for i in range(self.current_indent)])
            for key, value in o.iteritems():
                output.append(self.current_indent_str + json.dumps(key, ensure_ascii=False, encoding='utf-8-sig') + ': ' + self.encode(value))
            self.current_indent -= self.indent
            self.current_indent_str = ''.join([' ' for i in range(self.current_indent)])
            return '{\n' + ',\n'.join(output) + '\n' + self.current_indent_str + '}'
        else:
            return json.dumps(o, ensure_ascii=False, encoding='utf-8-sig')


class DateTimesMetaLobby(View):

    def __init__(self):
        super(DateTimesMetaLobby, self).__init__()

    def _populate(self):
        # noinspection PyProtectedMember
        super(DateTimesMetaLobby, self)._populate()

    def _dispose(self):
        # noinspection PyProtectedMember
        super(DateTimesMetaLobby, self)._dispose()

    def as_startUpdateLobbyS(self, *args):
        return self.flashObject.as_startUpdateLobby(*args) if self._isDAAPIInited() else None

    def as_creditCalcLobbyS(self, text):
        return self.flashObject.as_creditCalcLobby(text) if self._isDAAPIInited() else None

    def as_clearSceneS(self):
        return self.flashObject.as_clearScene() if self._isDAAPIInited() else None


class CreditsCalculator(DateTimesMetaLobby):
    def __init__(self):
        super(CreditsCalculator, self).__init__()
        self.coEffTable()
        self.COEFFICIENTS['USE_DATA'] = False
        self.AVERAGES = [(1.37, 1.37), (1.13, 1.28), (1.04, 1.35), (1.029, 1.42), (1.04, 1.5), (0.92, 1.3), (0.82, 1.4), (0.75, 1.5), (0.72, 0.72), (0.71, 0.72)]
        self.coEffDefaults = [0.53, 0.583, 0.6, 0.605, 0.62, 0.625, 0.63, 0.632, 0.633, 0.64, 0.65, 0.659, 0.66, 0.67, 0.6745, 0.68, 0.69, 0.7, 0.702, 0.708, 0.71,
                              0.711, 0.715, 0.72, 0.721, 0.724, 0.725, 0.73, 0.732, 0.734, 0.735, 0.745, 0.75, 0.751, 0.752, 0.753, 0.756, 0.759, 0.76, 0.764, 0.77,
                              0.774, 0.776, 0.777, 0.779, 0.78, 0.782, 0.783, 0.787, 0.788, 0.79, 0.791, 0.793, 0.795, 0.797, 0.798, 0.8, 0.802, 0.804, 0.805, 0.817,
                              0.82, 0.824, 0.825, 0.828, 0.83, 0.835, 0.836, 0.84, 0.847, 0.85, 0.854, 0.858, 0.861, 0.865, 0.868, 0.873, 0.874, 0.88, 0.883, 0.892,
                              0.894, 0.899, 0.9, 0.901, 0.906, 0.907, 0.909, 0.912, 0.9125, 0.915, 0.918, 0.922, 0.925, 0.928, 0.93, 0.931, 0.932, 0.935, 0.943, 0.945,
                              0.95, 0.964, 0.968, 0.969, 0.975, 0.976, 0.98, 0.987, 0.99, 0.997, 1.0, 1.0044, 1.0074, 1.012, 1.018, 1.02, 1.025, 1.026, 1.03, 1.0336,
                              1.044, 1.045, 1.046, 1.05, 1.053, 1.057, 1.07, 1.077, 1.08, 1.085, 1.086, 1.088, 1.089, 1.09, 1.0902, 1.093, 1.094, 1.1, 1.102, 1.104,
                              1.108, 1.109, 1.11, 1.113, 1.115, 1.12, 1.122, 1.127, 1.128, 1.129, 1.14, 1.1425, 1.15, 1.154, 1.1585, 1.168, 1.17, 1.1782, 1.18, 1.199,
                              1.2, 1.21, 1.219, 1.22, 1.25, 1.253, 1.2558, 1.26, 1.27, 1.276, 1.3, 1.311, 1.3145, 1.33, 1.35, 1.36, 1.365, 1.38, 1.4, 1.419, 1.43, 1.437,
                              1.44, 1.445, 1.45, 1.46, 1.4734, 1.48, 1.485, 1.49, 1.5, 1.52, 1.53, 1.55, 1.56, 1.57, 1.575, 1.59, 1.6, 1.62, 1.63, 1.637, 1.64, 1.65, 1.67,
                              1.75, 1.81]
        self.PATH = ''.join(['./mods/configs/Driftkings/%s/' % config.ID])
        self.readJson()
        self.PREMIUM_ACC = self.COEFFICIENTS['USE_DATA']
        self.iconCredits = '<img src=\'img://gui/maps/icons/quests/bonuses/big/credits.png\' vspace=\'-7\' width=\'20\' height=\'20\'/>'
        self.textWin = ''
        self.textDEFEAT = ''
        self.tempResults = {}
        self.item = None
        self.altMode = False
        self.ctrlMode = False
        self.hangarOutcome = 0
        self.hangarItems = {}
        self.hangarAmmo = {}
        self.killed = False
        self.repairCost = 0
        self.costRepairs = {}
        self.usedItems = {}
        self.hangarHeader = ''
        #
        self.name = None
        self.vehicleName = None
        self.level = None
        self.listAlly = None
        self.SPOT = int()
        self.ASSIST = int()
        self.DAMAGE_SELF_SPOT = int()
        self.DAMAGE_OTHER_SPOT = int()
        self.DAMAGE_UNKNOWN_SPOT = int()
        self.DAMAGE_STUN = int()
        self.DAMAGE_ASSIST = int()
        self.WinResult = int()
        self.WinResultMin = int()
        self.DefeatResult = int()
        self.DefeatResultMin = int()
        self.premium = int()
        self.compactDescr = None
        self.balanceCoeff = None
        self.recalculatedMessage = ''

    def _populate(self):
        super(CreditsCalculator, self)._populate()
        self.as_startUpdateLobbyS(config.data)

    def _dispose(self):
        super(CreditsCalculator, self)._dispose()

    def byte_ify(self, inputs):
        if inputs:
            if isinstance(inputs, dict):
                return {self.byte_ify(key): self.byte_ify(value) for key, value in inputs.iteritems()}
            elif isinstance(inputs, list):
                return [self.byte_ify(element) for element in inputs]
            elif isinstance(inputs, unicode):
                return inputs.encode('utf-8')
            else:
                return inputs
        return inputs

    def writeJson(self):
        if not os.path.exists(self.PATH):
            os.makedirs(self.PATH)
        with codecs.open(self.PATH + 'sw_templates.json', 'w', encoding='utf-8-sig') as json_file:
            data = json.dumps(collections.OrderedDict(sorted(self.COEFFICIENTS.items(), key=lambda t: t[0])), sort_keys=True, indent=4, ensure_ascii=False, encoding='utf-8-sig', separators=(',', ': '), cls=MyJSONEncoder)
            json_file.write('%s' % self.byte_ify(data))
            json_file.close()

    def readJson(self):
        if os.path.isfile(self.PATH + 'sw_templates.json'):
            try:
                with codecs.open(self.PATH + 'sw_templates.json', 'r', encoding='utf-8-sig') as json_file:
                    data = json_file.read().decode('utf-8-sig')
                    self.COEFFICIENTS.update(self.byte_ify(json.loads(data)))
                    json_file.close()
            except StandardError:
                self.writeJson()
        else:
            self.writeJson()

    def getHangarData(self, isPremium):
        if self.COEFFICIENTS['USE_DATA'] != isPremium:
            self.COEFFICIENTS['USE_DATA'] = isPremium
            self.writeJson()
        self.PREMIUM_ACC = isPremium
        outcome = 0
        for installedItem in g_currentVehicle.item.battleBoosters.installed.getItems():
            price = installedItem.buyPrices.getSum().price.credits
            outcome += price if not installedItem.inventoryCount else 0
        self.hangarOutcome = outcome

        self.hangarItems = {}
        for installedItem in g_currentVehicle.item.consumables.installed.getItems():
            price = installedItem.buyPrices.getSum().price.credits
            self.hangarItems[installedItem.intCD] = [price if not installedItem.inventoryCount else 0, price if not installedItem.inventoryCount else installedItem.getSellPrice().price.credits]
        self.hangarAmmo = {}
        for ammo in g_currentVehicle.item.gun.defaultAmmo:
            self.hangarAmmo[ammo.intCD] = [ammo.buyPrices.getSum().price.credits if not ammo.inventoryCount else ammo.getSellPrice().price.credits, 0, 0]

    def timer(self):
        vehicle = getPlayer().getVehicleAttached()
        if vehicle:
            self.startBattle()
            return
        callback(0.1, self.timer)

    def code(self, compactDescr, balanceCoEff):
        test = '%s' % compactDescr
        self.COEFFICIENTS[test] = balanceCoEff
        self.writeJson()
        return test, self.COEFFICIENTS[test]

    def deCode(self, compactDescr):
        test = '%s' % compactDescr
        if test in self.COEFFICIENTS:
            return test, round(self.COEFFICIENTS[test], 6)
        return test, 0.0

    def startBattle(self):
        self.altMode = False
        self.ctrlMode = False
        player = getPlayer()
        InputHandler.g_instance.onKeyDown += self.keyPressed
        InputHandler.g_instance.onKeyUp += self.keyPressed
        player.arena.onVehicleKilled += self.onVehicleKilled
        ammoCtrl = player.guiSessionProvider.shared.ammo
        if ammoCtrl is not None:
            ammoCtrl.onShellsAdded += self.onShellsAdded
            ammoCtrl.onShellsUpdated += self.onShellsUpdated
        vehicle = player.getVehicleAttached()
        self.costRepairs.update(
            {
                'gun': vehicle.typeDescriptor.gun.maxRepairCost,
                'engine': vehicle.typeDescriptor.engine.maxRepairCost,
                'turretRotator': vehicle.typeDescriptor.turret.turretRotatorHealth.maxRepairCost,
                'surveyingDevice': vehicle.typeDescriptor.turret.surveyingDeviceHealth.maxRepairCost,
                'ammoBay': vehicle.typeDescriptor.hull.ammoBayHealth.maxRepairCost,
                'radio': vehicle.typeDescriptor.radio.maxRepairCost,
                'fuelTank': vehicle.typeDescriptor.fuelTank.maxRepairCost,
                'chassis': vehicle.typeDescriptor.chassis.maxRepairCost
            }
        )
        self.costRepairs.update({name: vehicle.typeDescriptor.chassis.maxRepairCost for name in CHASSIS_ALL_ITEMS})
        if not self.hangarItems:
            self.hangarItems = {763: (3000, 3000), 1019: (20000, 20000), 1275: (3000, 3000), 1531: (20000, 20000), 1787: (5000, 5000), 4859: (20000, 20000), 4091: (20000, 20000), 2299: (20000, 20000), 2555: (20000, 20000), 3067: (20000, 20000), 251: (3000, 3000), 3323: (3000, 3000), 4347: (5000, 5000), 3579: (20000, 20000), 15867: (20000, 20000), 25851: (20000, 20000), 16123: (20000, 20000), 2043: (5000, 5000), 16379: (20000, 20000), 16635: (20000, 20000), 4603: (20000, 20000), 507: (20000, 20000)}
        self.usedItems = {}
        self.item = None
        self.name = vehicle.typeDescriptor.name
        self.vehicleName = player.guiSessionProvider.getCtx().getPlayerFullNameParts(vID=vehicle.id).vehicleName
        self.level = vehicle.typeDescriptor.level
        self.textWin = ''
        self.textDEFEAT = ''
        player = getPlayer()
        arenaDP = player.guiSessionProvider.getArenaDP()
        self.listAlly = vos_collections.AllyItemsCollection().ids(arenaDP)
        self.listAlly.remove(player.playerVehicleID)
        self.PREMIUM_ACC = self.COEFFICIENTS['USE_DATA']
        self.readJson()
        self.SPOT = 0
        self.ASSIST = 0
        self.DAMAGE_SELF_SPOT = 0
        self.DAMAGE_OTHER_SPOT = 0
        self.DAMAGE_UNKNOWN_SPOT = 0
        self.DAMAGE_STUN = 0
        self.DAMAGE_ASSIST = 0
        self.WinResult = 0
        self.WinResultMin = 0
        self.DefeatResult = 0
        self.DefeatResultMin = 0
        self.premium = 1.5 if self.PREMIUM_ACC else 1.0
        self.compactDescr, self.balanceCoeff = self.deCode(vehicle.typeDescriptor.type.compactDescr)
        if not self.balanceCoeff:
            ids = 1 if 'premium' in vehicle.typeDescriptor.type.tags else 0
            self.balanceCoeff = self.AVERAGES[self.level - 1][ids]
        self.killed = False
        self.repairCost = 0
        self.calc()

    @staticmethod
    def canSpotTarget(targetVehicle):
        distSq = (targetVehicle.position - getPlayer().getOwnVehiclePosition()).lengthSquared
        if distSq < 10000:
            return True

        circularVisionRadius = getPlayer().guiSessionProvider.shared.feedback.getVehicleAttrs()['circularVisionRadius']
        if distSq < circularVisionRadius * circularVisionRadius * 0.75 * 0.75:
            return True

        return False

    @staticmethod
    def canNeverSpotTarget(targetVehicle):
        distSq = (targetVehicle.position - getPlayer().getOwnVehiclePosition()).lengthSquared
        circularVisionRadius = getPlayer().guiSessionProvider.shared.feedback.getVehicleAttrs()['circularVisionRadius']
        if distSq > circularVisionRadius * circularVisionRadius:
            return True
        return False

    def onBattleEvents(self, events):
        player = getPlayer()
        guiSessionProvider = player.guiSessionProvider
        radio = 0
        track = 0
        stun = 0
        if guiSessionProvider.shared.vehicleState.getControllingVehicleID() == player.playerVehicleID:
            for data in events:
                feedbackEvent = feedback_events.PlayerFeedbackEvent.fromDict(data)
                eventType = feedbackEvent.getBattleEventType()
                targetID = feedbackEvent.getTargetID()
                if eventType == BATTLE_EVENT_TYPE.SPOTTED:
                    vehicle = getEntity(targetID)
                    self.SPOT += 1
                    if vehicle and 'SPG' in vehicle.typeDescriptor.type.tags:
                        self.SPOT += 1
                if eventType in DAMAGE_EVENTS:
                    extra = feedbackEvent.getExtra()
                    if extra:
                        if eventType == BATTLE_EVENT_TYPE.RADIO_ASSIST:
                            radio += extra.getDamage()
                        if eventType == BATTLE_EVENT_TYPE.TRACK_ASSIST:
                            track += extra.getDamage()
                        if eventType == BATTLE_EVENT_TYPE.STUN_ASSIST:
                            stun += extra.getDamage()
                        if eventType == BATTLE_EVENT_TYPE.DAMAGE:
                            arenaDP = guiSessionProvider.getArenaDP()
                            if arenaDP.isEnemyTeam(arenaDP.getVehicleInfo(targetID).team):
                                vehicle = getEntity(targetID)
                                if vehicle:
                                    if vehicle.stunInfo > 0.0:
                                        self.DAMAGE_STUN += extra.getDamage()
                                    elif self.canSpotTarget(vehicle):
                                        self.DAMAGE_SELF_SPOT += extra.getDamage()
                                    elif self.canNeverSpotTarget(vehicle):
                                        self.DAMAGE_OTHER_SPOT += extra.getDamage()
                                    else:
                                        self.DAMAGE_UNKNOWN_SPOT += extra.getDamage()
        data = [radio, track, stun]
        self.ASSIST += max(data)
        self.calc()

    def deviceTouched(self, state, _):
        if self.killed:
            return
        player = getPlayer()
        ctrl = player.guiSessionProvider.shared
        self.repairCost = 0
        if state == VEHICLE_VIEW_STATE.DEVICES:
            self.repairCost = 0
            repairs = 0
            for equipment in ctrl.equipments.iterEquipmentsByTag('repairkit'):
                for itemName, deviceState in equipment[1].getEntitiesIterator():
                    if deviceState == 'destroyed':
                        if itemName in self.costRepairs:
                            repairs += self.costRepairs[itemName]
                    if deviceState == 'critical':
                        if itemName in self.costRepairs:
                            repairs += self.costRepairs[itemName] / 2
            self.repairCost += int(round(repairs))
        self.calc()

    def onVehicleKilled(self, target_id, *_):
        player = getPlayer()
        vehicle = player.getVehicleAttached()
        if target_id == vehicle.id:
            self.killed = True
            self.calc()
            # return
            getMaxRepairCost = vehicle.typeDescriptor.getMaxRepairCost() - vehicle.typeDescriptor.maxHealth
            self.repairCost = int(round(getMaxRepairCost - getMaxRepairCost * vehicle.health / round(vehicle.typeDescriptor.maxHealth)))
            ctrl = player.guiSessionProvider.shared
            repairs = 0
            for equipment in ctrl.equipments.iterEquipmentsByTag('repairkit'):
                for itemName, deviceState in equipment[1].getEntitiesIterator():
                    if deviceState == 'destroyed':
                        if itemName in self.costRepairs:
                            repairs += self.costRepairs[itemName]
                    if deviceState == 'critical':
                        if itemName in self.costRepairs:
                            repairs += self.costRepairs[itemName] / 2
            self.repairCost += int(repairs)
            self.calc()

    def battleOutcome(self):
        player = getPlayer()
        ctrl = player.guiSessionProvider.shared
        price = self.hangarOutcome
        if not self.killed:
            try:
                for item in ctrl.equipments.getOrderedEquipmentsLayout():
                    if item and item[0] in self.hangarItems:
                        prevQuantity = item[1].getPrevQuantity()
                        quantity = item[1].getQuantity()
                        if item[0] not in self.usedItems:
                            self.usedItems[item[0]] = [not prevQuantity and quantity < 65535, self.hangarItems[item[0]][1], self.hangarItems[item[0]][1]]
                        if prevQuantity > 0 and 1 < quantity < 65535:
                            self.usedItems[item[0]][0] = True
            except StandardError:
                pass
        for equipment in self.usedItems:
            if self.usedItems[equipment][0]:
                price += self.usedItems[equipment][1]
        for ammo in self.hangarAmmo:
            if self.hangarAmmo[ammo][1]:
                price += self.hangarAmmo[ammo][0] * self.hangarAmmo[ammo][1]
        return int(round(price))

    def onShellsAdded(self, intCD, _, quantity, __, ___):
        if intCD in self.hangarAmmo:
            self.hangarAmmo[intCD][2] = quantity
            self.calc()

    def onShellsUpdated(self, intCD, quantity, *_):
        if intCD in self.hangarAmmo:
            self.hangarAmmo[intCD][1] = self.hangarAmmo[intCD][2] - quantity
            self.calc()

    def calc(self, hangar=False):
        if not config.data['enabled']:
            return
        assistCoeff = 5
        spotCoeff = 100
        damageStunCoeff = 7.7
        damageSpottedCoeff = 7.5
        damageSelfCoeff = 10
        defeatCredits = self.level * 700
        winCredits = self.level * 1300

        assistCredits = self.ASSIST * assistCoeff
        spotCredits = self.SPOT * spotCoeff
        stunCredits = self.DAMAGE_STUN * damageStunCoeff

        damageMinCredits = self.DAMAGE_SELF_SPOT * damageSelfCoeff + (self.DAMAGE_UNKNOWN_SPOT + self.DAMAGE_OTHER_SPOT) * damageSpottedCoeff
        damageMaxCredits = (self.DAMAGE_SELF_SPOT + self.DAMAGE_UNKNOWN_SPOT) * damageSelfCoeff + self.DAMAGE_OTHER_SPOT * damageSpottedCoeff

        outcomeCredits = self.battleOutcome()

        self.DefeatResult = int(int(self.balanceCoeff * int(defeatCredits + assistCredits + spotCredits + damageMaxCredits + stunCredits) - 0.5) * self.premium + 0.5)
        self.DefeatResultMin = int(int(self.balanceCoeff * int(defeatCredits + assistCredits + spotCredits + damageMinCredits + stunCredits) - 0.5) * self.premium + 0.5)

        self.WinResult = int(int(self.balanceCoeff * int(winCredits + assistCredits + spotCredits + damageMaxCredits + stunCredits) - 0.5) * self.premium + 0.5)
        self.WinResultMin = int(int(self.balanceCoeff * int(winCredits + assistCredits + spotCredits + damageMinCredits + stunCredits) - 0.5) * self.premium + 0.5)

        if not hangar:
            textWinner = self.correctedText(self.WinResultMin, self.WinResult, outcomeCredits)
            textDefeat = self.correctedText(self.DefeatResult, self.DefeatResult, outcomeCredits)
            colorWin = '#80D639'
            colorDefeat = '#FF6347'
            self.textWin = '<font size=\'20\' color=\'%s\'>~%s%s</font>' % (colorWin, self.iconCredits, textWinner)
            self.textDEFEAT = '<font size=\'20\' color=\'%s\'>~%s%s</font>' % (colorDefeat, self.iconCredits, textDefeat)
            if self.compactDescr not in self.tempResults:
                vehicle = getPlayer().getVehicleAttached()
                self.tempResults[self.compactDescr] = {
                    'descr': vehicle.typeDescriptor.type.compactDescr,
                    'premium': self.premium,
                    'damage': self.DAMAGE_SELF_SPOT + self.DAMAGE_UNKNOWN_SPOT + self.DAMAGE_OTHER_SPOT + self.DAMAGE_STUN,
                    'assist': self.ASSIST,
                    'spot': self.SPOT,
                    'level': self.level,
                    'name': self.name.replace(':', '_'),
                    'repairCost': int(round(vehicle.typeDescriptor.getMaxRepairCost() - vehicle.typeDescriptor.maxHealth)),
                    'clearRepair': False,
                }
            self.tempResults[self.compactDescr]['damage'] = self.DAMAGE_SELF_SPOT + self.DAMAGE_UNKNOWN_SPOT + self.DAMAGE_OTHER_SPOT + self.DAMAGE_STUN
            self.tempResults[self.compactDescr]['assist'] = self.ASSIST
            self.tempResults[self.compactDescr]['spot'] = self.SPOT
            if self.tempResults[self.compactDescr]['repairCost'] == self.repairCost:
                self.tempResults[self.compactDescr]['clearRepair'] = True
            else:
                self.tempResults[self.compactDescr]['clearRepair'] = False
            # as_BATTLE
            # flash.setCreditsText(self.textWin if not self.altMode else self.textDEFEAT)

    def keyPressed(self, event):
        player = getPlayer()
        if not player.arena:
            return
        if player.arena.bonusType != ARENA_BONUS_TYPE.REGULAR:
            return
        isKeyDownTrigger = event.isKeyDown()
        if event.key in [Keys.KEY_LALT, Keys.KEY_RALT]:
            if isKeyDownTrigger:
                self.altMode = True
            if event.isKeyUp():
                self.altMode = False
            self.calc()
        if event.key in [Keys.KEY_LCONTROL, Keys.KEY_RCONTROL]:
            if isKeyDownTrigger:
                self.ctrlMode = True
            if event.isKeyUp():
                self.ctrlMode = False
            self.calc()

    def correctedText(self, xMin, xMax, outcome):
        out = '<font color=\'#FF0000\'> -%s</font>' % outcome if outcome else ''
        if xMin != xMax:
            if self.ctrlMode:
                return '%s[%s]%s' % (xMin, int(xMax * 1.05), out)
            return '%s%s' % (xMin, out)
        return '%s%s' % (xMax, out)

    def stopBattle(self):
        player = getPlayer()
        self.ctrlMode = False
        self.altMode = False
        player.arena.onVehicleKilled -= self.onVehicleKilled
        ammoCtrl = player.guiSessionProvider.shared.ammo
        if ammoCtrl is not None:
            ammoCtrl.onShellsAdded -= self.onShellsAdded
            ammoCtrl.onShellsUpdated -= self.onShellsUpdated
        InputHandler.g_instance.onKeyDown -= self.keyPressed
        InputHandler.g_instance.onKeyUp -= self.keyPressed
        self.hangarOutcome = 0
        self.hangarItems = {}
        self.hangarAmmo = {}
        self.killed = False
        self.repairCost = 0
        self.costRepairs = {}
        self.usedItems = {}

    def hangarMessage(self):
        if not config.data['enabled']:
            return
        if ServicesLocator.hangarSpace is not None and ServicesLocator.hangarSpace.inited:
            self.recalculatedMessage = '<font size=\'20\' color=\"#FFE041\">%s</font>\n' % self.hangarHeader
            if self.textWin or self.textDEFEAT:
                textWinner = self.correctedText(self.WinResultMin, self.WinResult, 0)
                textDefeat = self.correctedText(self.DefeatResult, self.DefeatResult, 0)
                colorWin = '#80D639'
                colorDefeat = '#FF6347'
                self.textWin = '<font size=\'20\' color=\'%s\'>~%s%s</font>' % (colorWin, self.iconCredits, textWinner)
                self.textDEFEAT = '<font size=\'20\' color=\'%s\'>~%s%s</font>' % (colorDefeat, self.iconCredits, textDefeat)
                self.recalculatedMessage += '  ' + self.textWin + '<font size=\'20\' color=\'#FFE041\'> %s </font>' % self.vehicleName + self.textDEFEAT
            self.timerMessage()

    def timerMessage(self):
        if not config.data['hangarShow']:
            return
        if g_currentVehicle.item:
            self.as_creditCalcLobbyS(self.recalculatedMessage)
            return
        callback(1.0, self.timerMessage)

    @staticmethod
    def tester(credits, premiumCoEff, winCoEff, level, assist, spot):
        result = []
        winCoEff = 1300 if winCoEff else 700
        pool = {
            1: (99, 0.1),
            2: (999, 0.01),
            3: (9999, 0.001),
            4: (99999, 0.0001),
            5: (999999, 0.00001),
        }
        for ranged in pool:
            boosterCoEff = 0.0
            for i in xrange(pool[ranged][0]):
                boosterCoEff = round(boosterCoEff + pool[ranged][1], ranged)
                if credits == int(int(boosterCoEff * int(level * winCoEff + assist * 5 + spot * 100) - 0.5) * premiumCoEff + 0.5):
                    result.append(boosterCoEff)
            if result:
                return result
        return result

    def sortValues(self, value):  # debug=False
        try:
            index = self.coEffDefaults.index(filter(lambda x: value <= x + 0.0005, self.coEffDefaults)[0])
            return self.coEffDefaults[index]
        except StandardError:
            return value

    def sortResult(self, first, second, testCoEff):
        if first and second:
            check1 = self.sortValues(round(sum(first) / len(first), 5))
            check2 = self.sortValues(round(sum(second) / len(second), 5))
            if check1 == testCoEff or check2 == testCoEff:
                return testCoEff
            if check1 == check2:
                return check1
            if check1 in second:
                return check1
            if check2 in first:
                return check2
        return 0.0

    def resultReCalc(self, typeCompDescr, isWin, credits, originalCredits, spot, assist, damage, _):
        self.readJson()
        vehicleCompDesc, testCoEff = self.deCode(typeCompDescr)
        if vehicleCompDesc in self.tempResults:
            if not damage:
                checkCorrectedBattleData = credits / float(originalCredits)
                premiumCoEff = 1.0 if checkCorrectedBattleData < 1.01 else 1.5
                winCoEff = 1300 if isWin else 700
                level = self.tempResults[vehicleCompDesc]['level']
                result1 = self.tester(originalCredits, 1.0, isWin, level, assist, spot)
                result2 = self.tester(credits, 1.5, isWin, level, assist, spot)

                checkData = int(int(1.0 * int(level * winCoEff + assist * 5 + spot * 100) - 0.5) * premiumCoEff + 0.5)
                if premiumCoEff > 1.1:
                    coEff1 = round(checkData / originalCredits, 4)
                else:
                    coEff1 = round(originalCredits / checkData, 4)
                check = self.sortResult(result1, result2, coEff1)
                self.readJson()
                checkData *= premiumCoEff
                coEff2 = round(credits / checkData, 4)
                checkAgain = self.sortResult(result1, result2, coEff2)
                if checkAgain and check != checkAgain:
                    check = checkAgain
                if coEff1 == coEff2 and coEff1 != 1.0:
                    self.compactDescr, self.balanceCoeff = self.code(typeCompDescr, coEff2)
                    self.readJson()
                else:
                    if check:
                        self.compactDescr, self.balanceCoeff = self.code(typeCompDescr, check)
                        self.readJson()

    def receiveBattleResult(self, _, battleResults):
        playerVehicles = battleResults['personal'].itervalues().next()
        if not playerVehicles:
            return
        assist = max(playerVehicles['damageAssistedRadio'], playerVehicles['damageAssistedTrack'], playerVehicles['damageAssistedStun'])
        spot = playerVehicles['spotted']
        damage = playerVehicles['damageDealt']
        repair = playerVehicles['repair']
        self.resultReCalc(playerVehicles['typeCompDescr'], battleResults['common']['winnerTeam'] == playerVehicles['team'], playerVehicles['factualCredits'], playerVehicles['originalCredits'], spot, assist, damage, repair)

    def coEffTable(self):
        self.COEFFICIENTS = {}
        self.COEFFICIENTS.update({
            # italy
            # lightTank
            '161': 1.4,  # lvl:1 italy_It04_Fiat_3000
            '417': 1.1,  # lvl:2 italy_It05_Carro_L6_40
            # mediumTank
            '673': 1.15,  # lvl:2 italy_It06_M14_41
            '929': 1.1,  # lvl:3 italy_It03_M15_42
            '1185': 1.0,  # lvl:4 italy_It07_P26_40
            '1441': 1.0,  # lvl:5 italy_It11_P43
            '1697': 0.9,  # lvl:6 italy_It10_P43_bis
            '1953': 0.8,  # lvl:7 italy_It09_P43_ter
            '2209': 0.7,  # lvl:8 italy_It14_P44_Pantera
            '51361': 1.5,  # lvl:8 italy_It13_Progetto_M35_mod_46  !!!!PREMIUM
            '2465': 0.72,  # lvl:9 italy_It12_Prototipo_Standard_B
            '2721': 0.73,  # lvl:10 italy_It08_Progetto_M40_mod_65
            # heavyTank
            '3745': 0.708,  # lvl:8 italy_It17_Progetto_CC55_mod_54
            '2977': 1.05,  # lvl:10 italy_It15_Rinoceronte
        })
        self.COEFFICIENTS.update({
            # sweden
            # lightTank
            '129': 1.4,  # lvl:1 sweden_S05_Strv_M21_29
            '51841': 1.2,  # lvl:2 sweden_S15_L_60  !!!!PREMIUM
            '385': 1.102,  # lvl:2 sweden_S03_Strv_M38
            '641': 1.05,  # lvl:3 sweden_S12_Strv_M40
            # mediumTank
            '897': 1.05,  # lvl:4 sweden_S04_Lago_I
            '1153': 1.1,  # lvl:5 sweden_S02_Strv_M42
            '51585': 1.2,  # lvl:6 sweden_S01_Strv_74_A2  !!!!PREMIUM
            '1409': 0.9,  # lvl:6 sweden_S07_Strv_74
            '1665': 0.8,  # lvl:7 sweden_S13_Leo
            '4993': 0.7,  # lvl:8 sweden_S29_UDES_14_5
            '52609': 1.6,  # lvl:8 sweden_S23_Strv_81_sabaton  !!!!PREMIUM
            '52353': 1.6,  # lvl:8 sweden_S23_Strv_81  !!!!PREMIUM
            '53121': 1.5,  # lvl:8 sweden_S26_Lansen_C  !!!!PREMIUM
            '5249': 0.72,  # lvl:9 sweden_S27_UDES_16
            '5505': 0.73,  # lvl:10 sweden_S28_UDES_15_16
            # heavyTank
            '1921': 0.8,  # lvl:8 sweden_S18_EMIL_1951_E1
            '52865': 1.5,  # lvl:8 sweden_S25_EMIL_51  !!!!PREMIUM
            '2177': 0.73,  # lvl:9 sweden_S17_EMIL_1952_E2
            '53889': 0.73,  # lvl:10 sweden_S16_Kranvagn_bob
            '2433': 0.71,  # lvl:10 sweden_S16_Kranvagn
            # AT-SPG
            '2689': 1.05,  # lvl:2 sweden_S09_L_120_TD
            '2945': 0.95,  # lvl:3 sweden_S20_Ikv_72
            '3201': 0.93,  # lvl:4 sweden_S19_Sav_M43
            '3457': 0.98,  # lvl:5 sweden_S14_Ikv_103
            '3713': 0.901,  # lvl:6 sweden_S08_Ikv_65_Alt_2
            '3969': 0.8,  # lvl:7 sweden_S06_Ikv_90_Typ_B_Bofors
            '52097': 1.6,  # lvl:8 sweden_S22_Strv_S1  !!!!PREMIUM
            '4225': 0.72,  # lvl:8 sweden_S21_UDES_03
            '4481': 0.7,  # lvl:9 sweden_S10_Strv_103_0_Series
            '4737': 0.63,  # lvl:10 sweden_S11_Strv_103B
        })
        self.COEFFICIENTS.update({
            # poland
            # lightTank
            '1169': 1.419,  # lvl:1 poland_Pl14_4TP
            '1425': 1.1,  # lvl:2 poland_Pl09_7TP
            '401': 1.3,  # lvl:2 poland_Pl01_TKS_20mm  !!!!PREMIUM
            '1681': 1.1,  # lvl:3 poland_Pl06_10TP
            '1937': 1.018,  # lvl:4 poland_Pl07_14TP
            # mediumTank
            '2193': 1.0044,  # lvl:5 poland_Pl12_25TP_KSUST_II
            '2449': 0.9,  # lvl:6 poland_Pl10_40TP_Habicha
            '145': 1.25,  # lvl:6 poland_Pl03_PzV_Poland  !!!!PREMIUM
            '51345': 1.25,  # lvl:6 poland_Pl16_T34_85_Rudy  !!!!PREMIUM
            # heavyTank
            '2705': 0.858,  # lvl:7 poland_Pl11_45TP_Habicha
            '913': 1.5,  # lvl:8 poland_Pl08_50TP_prototyp  !!!!PREMIUM
            '2961': 0.791,  # lvl:8 poland_Pl13_53TP_Markowskiego
            '3217': 0.73,  # lvl:9 poland_Pl05_50TP_Tyszkiewicza
            '3473': 0.71,  # lvl:10 poland_Pl15_60TP_Lewandowskiego
        })
        self.COEFFICIENTS.update({
            # japan
            # lightTank
            '609': 1.3,  # lvl:1 japan_J01_NC27
            '3169': 1.2996,  # lvl:2 japan_J02_Te_Ke  !!!!PREMIUM
            '865': 1.1,  # lvl:2 japan_J03_Ha_Go
            '2401': 1.1,  # lvl:3 japan_J04_Ke_Ni
            '2145': 1.1,  # lvl:3 japan_J07_Chi_Ha
            '2913': 1.2,  # lvl:4 japan_J06_Ke_Ho
            # mediumTank
            '353': 1.2,  # lvl:2 japan_J15_Chi_Ni
            '5985': 1.1,  # lvl:2 japan_J26_Type_89
            '1633': 1.1,  # lvl:4 japan_J09_Chi_He
            '1377': 1.0,  # lvl:5 japan_J08_Chi_Nu
            '51553': 1.5,  # lvl:5 japan_J12_Chi_Nu_Kai  !!!!PREMIUM
            '1889': 0.85,  # lvl:6 japan_J10_Chi_To
            '1121': 0.77,  # lvl:7 japan_J11_Chi_Ri
            '52065': 1.5,  # lvl:8 japan_J18_STA_2_3  !!!!PREMIUM
            '52833': 1.5,  # lvl:8 japan_J30_Edelweiss  !!!!PREMIUM
            '2657': 0.69,  # lvl:8 japan_J13_STA_1
            '3425': 0.75,  # lvl:9 japan_J14_Type_61
            '3681': 0.73,  # lvl:10 japan_J16_ST_B1
            # heavyTank
            '4705': 1.05,  # lvl:3 japan_J21_Type_91
            '4449': 1.05,  # lvl:4 japan_J22_Type_95
            '5729': 1.05,  # lvl:5 japan_J23_Mi_To
            '52321': 1.2,  # lvl:6 japan_J19_Tiger_I_Jpn  !!!!PREMIUM
            '5473': 0.9,  # lvl:6 japan_J24_Mi_To_130_tons
            '5217': 0.83,  # lvl:7 japan_J28_O_I_100
            '4961': 0.8,  # lvl:8 japan_J27_O_I_120
            '52577': 1.5,  # lvl:8 japan_J29_Nameless  !!!!PREMIUM
            '4193': 0.71,  # lvl:9 japan_J25_Type_4
            '3937': 0.73,  # lvl:10 japan_J20_Type_2605
        })
        self.COEFFICIENTS.update({
            # china
            # lightTank
            '1329': 1.419,  # lvl:1 china_Ch06_Renault_NC31
            '2353': 1.128,  # lvl:2 china_Ch07_Vickers_MkE_Type_BT26
            '4401': 1.0074,  # lvl:3 china_Ch08_Type97_Chi_Ha
            '3121': 1.0336,  # lvl:4 china_Ch09_M5
            '4913': 0.925,  # lvl:6 china_Ch15_59_16
            '64817': 1.35,  # lvl:6 china_Ch24_Type64  !!!!PREMIUM
            '3377': 0.78,  # lvl:7 china_Ch16_WZ_131
            '305': 1.4,  # lvl:7 china_Ch02_Type62  !!!!PREMIUM
            '3889': 0.6745,  # lvl:8 china_Ch17_WZ131_1_WZ132
            '62001': 1.5,  # lvl:8 china_Ch42_WalkerBulldog_M41D  !!!!PREMIUM
            '5681': 0.67,  # lvl:9 china_Ch28_WZ_132A
            '5937': 0.66,  # lvl:10 china_Ch29_Type_62C_prot
            # mediumTank
            '4657': 1.11,  # lvl:5 china_Ch21_T34
            '5169': 0.909,  # lvl:6 china_Ch20_Type58
            '1073': 0.78,  # lvl:7 china_Ch04_T34_1
            '64049': 1.575,  # lvl:8 china_Ch14_T34_3  !!!!PREMIUM
            '49': 1.575,  # lvl:8 china_Ch01_Type59  !!!!PREMIUM
            '561': 1.575,  # lvl:8 china_Ch01_Type59_Gold  !!!!PREMIUM
            '63793': 1.5,  # lvl:8 china_Ch26_59_Patton  !!!!PREMIUM
            '1585': 0.708,  # lvl:8 china_Ch05_T34_2
            '1841': 0.71,  # lvl:9 china_Ch18_WZ-120
            '63537': 0.73,  # lvl:10 china_Ch25_121_mod_1971B  !!!!PREMIUM
            '4145': 0.73,  # lvl:10 china_Ch19_121
            # heavyTank
            '3633': 0.874,  # lvl:7 china_Ch10_IS2
            '65073': 1.575,  # lvl:8 china_Ch03_WZ_111_A  !!!!PREMIUM
            '2865': 0.782,  # lvl:8 china_Ch11_110
            '817': 1.575,  # lvl:8 china_Ch03_WZ-111  !!!!PREMIUM
            '64561': 1.55,  # lvl:8 china_Ch23_112  !!!!PREMIUM
            '2097': 0.7,  # lvl:9 china_Ch12_111_1_2_3
            '5425': 0.774,  # lvl:10 china_Ch22_113
            '6193': 0.77,  # lvl:10 china_Ch41_WZ_111_5A
            # AT-SPG
            '6449': 1.05,  # lvl:2 china_Ch30_T-26G_FT
            '6705': 0.95,  # lvl:3 china_Ch31_M3G_FT
            '6961': 0.9,  # lvl:4 china_Ch32_SU-76G_FT
            '7217': 0.95,  # lvl:5 china_Ch33_60G_FT
            '7473': 0.9,  # lvl:6 china_Ch34_WZ131G_FT
            '7729': 0.8,  # lvl:7 china_Ch35_T-34-2G_FT
            '7985': 0.72,  # lvl:8 china_Ch36_WZ111_1G_FT
            '63281': 1.5,  # lvl:8 china_Ch39_WZ120_1G_FT  !!!!PREMIUM
            '8241': 0.7,  # lvl:9 china_Ch37_WZ111G_FT
            '8497': 0.62,  # lvl:10 china_Ch38_WZ113G_FT
        })
        self.COEFFICIENTS.update({
            # czech
            # lightTank
            '113': 1.4,  # lvl:1 czech_Cz06_Kolohousenka
            '369': 1.1,  # lvl:2 czech_Cz03_LT_vz35
            '625': 1.05,  # lvl:3 czech_Cz10_LT_vz38
            # mediumTank
            '881': 1.0,  # lvl:4 czech_Cz11_V_8_H
            '1137': 1.0,  # lvl:5 czech_Cz09_T_24
            '51569': 1.3,  # lvl:6 czech_Cz01_Skoda_T40  !!!!PREMIUM
            '1393': 0.9,  # lvl:6 czech_Cz08_T_25
            '1649': 0.77,  # lvl:7 czech_Cz05_T34_100
            '1905': 0.72,  # lvl:8 czech_Cz07_TVP_46
            '51825': 1.5,  # lvl:8 czech_Cz13_T_27  !!!!PREMIUM
            '2161': 0.71,  # lvl:9 czech_Cz02_TVP_T50
            '2417': 0.73,  # lvl:10 czech_Cz04_T50_51
            # heavyTank
        })
        self.COEFFICIENTS.update({
            # uk
            # lightTank
            '5201': 1.199,  # lvl:1 uk_GB03_Cruiser_Mk_I
            '593': 1.1,  # lvl:2 uk_GB14_M2
            '54865': 1.2996,  # lvl:2 uk_GB76_Mk_VIC  !!!!PREMIUM
            '6993': 1.089,  # lvl:2 uk_GB69_Cruiser_Mk_II
            '4945': 1.026,  # lvl:3 uk_GB04_Valentine
            '1361': 1.0,  # lvl:3 uk_GB15_Stuart_I
            '7761': 1.09,  # lvl:3 uk_GB58_Cruiser_Mk_III
            '7505': 1.089,  # lvl:4 uk_GB59_Cruiser_Mk_IV
            '6481': 1.077,  # lvl:5 uk_GB60_Covenanter
            '2129': 1.057,  # lvl:6 uk_GB20_Crusader
            '59729': 0.7799,  # lvl:7 uk_GB104_GSR_3301_Setter
            '59473': 0.68,  # lvl:8 uk_GB102_LHMTV
            '58449': 1.5,  # lvl:8 uk_GB101_FV1066_Senlac  !!!!PREMIUM
            '58705': 0.6701,  # lvl:9 uk_GB103_GSOR3301_AVR_FS
            '58961': 0.66,  # lvl:10 uk_GB100_Manticore
            # mediumTank
            '81': 1.637,  # lvl:1 uk_GB01_Medium_Mark_I
            '337': 1.253,  # lvl:2 uk_GB05_Vickers_Medium_Mk_II
            '2385': 1.089,  # lvl:3 uk_GB06_Vickers_Medium_Mk_III
            '849': 1.026,  # lvl:4 uk_GB07_Matilda
            '52817': 1.26,  # lvl:4 uk_GB33_Sentinel_AC_I  !!!!PREMIUM
            '1617': 1.0,  # lvl:4 uk_GB17_Grant_I
            '12881': 1.0,  # lvl:5 uk_GB50_Sherman_III
            '53585': 1.53,  # lvl:5 uk_GB68_Matilda_Black_Prince  !!!!PREMIUM
            '57169': 1.3,  # lvl:6 uk_GB95_Ekins_Firefly_M4A4  !!!!PREMIUM
            '56145': 1.22,  # lvl:6 uk_GB35_Sentinel_AC_IV  !!!!PREMIUM
            '1105': 0.932,  # lvl:6 uk_GB21_Cromwell
            '55889': 1.25,  # lvl:6 uk_GB85_Cromwell_Berlin  !!!!PREMIUM
            '3665': 0.85,  # lvl:6 uk_GB19_Sherman_Firefly
            '5457': 0.77,  # lvl:7 uk_GB22_Comet
            '56913': 1.5,  # lvl:8 uk_GB94_Centurion_Mk5-1_RAAC  !!!!PREMIUM
            '15441': 1.55,  # lvl:8 uk_GB87_Chieftain_T95_turret  !!!!PREMIUM
            '5969': 0.825,  # lvl:8 uk_GB23_Centurion
            '55633': 1.6,  # lvl:8 uk_GB70_N_FV4202_105  !!!!PREMIUM
            '5713': 0.73,  # lvl:9 uk_GB24_Centurion_Mk3
            '7249': 0.73,  # lvl:10 uk_GB86_Centurion_Action_X
            '14929': 0.73,  # lvl:10 uk_GB70_FV4202_105
            # heavyTank
            '54353': 1.4,  # lvl:5 uk_GB51_Excelsior  !!!!PREMIUM
            '2897': 1.115,  # lvl:5 uk_GB08_Churchill_I
            '53841': 1.38,  # lvl:6 uk_GB63_TOG_II  !!!!PREMIUM
            '4689': 0.98,  # lvl:6 uk_GB09_Churchill_VII
            '3153': 0.836,  # lvl:7 uk_GB10_Black_Prince
            '55121': 1.3,  # lvl:7 uk_GB52_A45  !!!!PREMIUM
            '56657': 1.5,  # lvl:8 uk_GB93_Caernarvon_AX  !!!!PREMIUM
            '3921': 0.825,  # lvl:8 uk_GB11_Caernarvon
            '4433': 0.752,  # lvl:9 uk_GB12_Conqueror
            '15697': 0.745,  # lvl:10 uk_GB91_Super_Conqueror
            '6225': 0.745,  # lvl:10 uk_GB13_FV215b  !!!!PREMIUM
            '57937': 0.73,  # lvl:10 uk_GB98_T95_FV4201_Chieftain  !!!!PREMIUM
            '15185': 0.73,  # lvl:10 uk_GB84_Chieftain_Mk6  !!!!PREMIUM
            # AT-SPG
            '8273': 1.1,  # lvl:2 uk_GB39_Universal_CarrierQF2
            '8017': 0.9,  # lvl:4 uk_GB42_Valentine_AT
            '9041': 0.945,  # lvl:4 uk_GB57_Alecto
            '13393': 0.95,  # lvl:5 uk_GB44_Archer
            '8785': 0.997,  # lvl:5 uk_GB73_AT2
            '9553': 0.9,  # lvl:6 uk_GB74_AT8
            '57681': 1.43,  # lvl:6 uk_GB96_Excalibur  !!!!PREMIUM
            '14417': 0.9,  # lvl:6 uk_GB45_Achilles_IIC
            '9809': 1.012,  # lvl:6 uk_GB40_Gun_Carrier_Churchill
            '54097': 1.38,  # lvl:7 uk_GB71_AT_15A  !!!!PREMIUM
            '10065': 0.795,  # lvl:7 uk_GB75_AT7
            '14161': 0.75,  # lvl:7 uk_GB41_Challenger
            '59985': 1.5,  # lvl:8 uk_GB99_Turtle_Mk1  !!!!PREMIUM
            '8529': 0.724,  # lvl:8 uk_GB72_AT15
            '14673': 0.71,  # lvl:8 uk_GB80_Charioteer
            '13137': 0.65,  # lvl:9 uk_GB81_FV4004
            '52561': 0.715,  # lvl:9 uk_GB32_Tortoise
            '9297': 0.583,  # lvl:10 uk_GB48_FV215b_183  !!!!PREMIUM
            '13905': 0.6,  # lvl:10 uk_GB83_FV4005
            '15953': 0.583,  # lvl:10 uk_GB92_FV217
            # SPG
            '10577': 1.15,  # lvl:2 uk_GB25_Loyd_Gun_Carriage
            '54609': 1.81,  # lvl:3 uk_GB78_Sexton_I  !!!!PREMIUM
            '3409': 1.09,  # lvl:3 uk_GB27_Sexton
            '10833': 1.05,  # lvl:4 uk_GB26_Birch_Gun
            '11089': 1.1,  # lvl:5 uk_GB28_Bishop
            '11857': 1.0,  # lvl:6 uk_GB77_FV304
            '11345': 0.8,  # lvl:7 uk_GB29_Crusader_5inch
            '12113': 0.75,  # lvl:8 uk_GB79_FV206
            '11601': 0.75,  # lvl:9 uk_GB30_FV3805
            '12369': 0.77,  # lvl:10 uk_GB31_Conqueror_Gun
        })
        self.COEFFICIENTS.update({
            # france
            # lightTank
            '577': 1.63,  # lvl:1 france_F01_RenaultFT
            '43329': 1.2,  # lvl:2 france_F111_AM39_Gendron_Somua  !!!!PREMIUM
            '15169': 1.1,  # lvl:2 france_F50_FCM36_20t
            '1601': 1.276,  # lvl:2 france_F02_D1
            '15937': 1.1,  # lvl:2 france_F49_RenaultR35
            '1345': 1.219,  # lvl:2 france_F12_Hotchkiss_H35
            '43841': 1.09,  # lvl:2 france_F42_AMR_35  !!!!PREMIUM
            '5953': 1.113,  # lvl:3 france_F13_AMX38
            '2881': 1.046,  # lvl:4 france_F14_AMX40
            '14145': 1.0,  # lvl:5 france_F62_ELC_AMX
            '17985': 0.87,  # lvl:6 france_F109_AMD_Panhard_178B
            '6465': 0.873,  # lvl:6 france_F15_AMX_12t
            '5185': 0.824,  # lvl:7 france_F16_AMX_13_75
            '63297': 1.3998,  # lvl:7 france_F69_AMX13_57_100_GrandFinal  !!!!PREMIUM
            '18241': 0.7799,  # lvl:7 france_F107_Hotchkiss_EBR
            '63809': 1.4,  # lvl:7 france_F69_AMX13_57_100  !!!!PREMIUM
            '43585': 1.5,  # lvl:8 france_F106_Panhard_EBR_75_Mle1954  !!!!PREMIUM
            '17473': 0.68,  # lvl:8 france_F87_Batignolles-Chatillon_12t
            '18497': 0.68,  # lvl:8 france_F110_Lynx_6x6
            '61505': 1.5,  # lvl:8 france_F97_ELC_EVEN_90  !!!!PREMIUM
            '4929': 0.67,  # lvl:9 france_F17_AMX_13_90
            '18753': 0.6701,  # lvl:9 france_F100_Panhard_EBR_90
            '17217': 0.66,  # lvl:10 france_F88_AMX_13_105
            '19009': 0.66,  # lvl:10 france_F108_Panhard_EBR_105
            # mediumTank
            '13121': 1.0,  # lvl:3 france_F44_Somua_S35
            '321': 1.025,  # lvl:3 france_F03_D2
            '14913': 1.0,  # lvl:4 france_F70_SARL42
            '4417': 1.05,  # lvl:5 france_F11_Renault_G1R
            '60737': 1.25,  # lvl:6 france_F113_Bretagne_Panther  !!!!PREMIUM
            '63553': 1.5,  # lvl:8 france_F68_AMX_Chasseur_de_char_46  !!!!PREMIUM
            '63041': 1.5,  # lvl:8 france_F73_M4A1_Revalorise  !!!!PREMIUM
            '62529': 1.6,  # lvl:8 france_F19_Lorraine40t  !!!!PREMIUM
            '5697': 0.817,  # lvl:9 france_F75_Char_de_25t
            '15681': 0.75,  # lvl:9 france_F71_AMX_30_prototype
            '15425': 0.73,  # lvl:10 france_F72_AMX_30
            '3649': 0.75,  # lvl:10 france_F18_Bat_Chatillon25t
            # heavyTank
            '1089': 1.08,  # lvl:4 france_F04_B1
            '6721': 1.08,  # lvl:5 france_F05_BDR_G1B
            '2625': 0.906,  # lvl:6 france_F06_ARL_44
            '6977': 0.795,  # lvl:7 france_F07_AMX_M4_1945
            '62273': 1.5,  # lvl:8 france_F84_Somua_SM  !!!!PREMIUM
            '16449': 0.8,  # lvl:8 france_F81_Char_de_65t
            '62017': 1.6,  # lvl:8 france_F74_AMX_M4_1949_Liberte  !!!!PREMIUM
            '64065': 1.445,  # lvl:8 france_F65_FCM_50t  !!!!PREMIUM
            '3137': 0.793,  # lvl:8 france_F08_AMX_50_100
            '62785': 1.6,  # lvl:8 france_F74_AMX_M4_1949  !!!!PREMIUM
            '3905': 0.702,  # lvl:9 france_F09_AMX_50_120
            '16705': 0.72,  # lvl:9 france_F83_AMX_M4_Mle1949_Bis
            '6209': 0.75,  # lvl:10 france_F10_AMX_50B
            '16961': 0.71,  # lvl:10 france_F82_AMX_M4_Mle1949_Ter
            # AT-SPG
            '7745': 0.99,  # lvl:2 france_F30_RenaultFT_AC
            '8257': 0.918,  # lvl:3 france_F52_RenaultUE57
            '2369': 1.3,  # lvl:3 france_F27_FCM_36Pak40  !!!!PREMIUM
            '9793': 0.969,  # lvl:4 france_F32_Somua_Sau_40
            '61249': 1.45,  # lvl:5 france_F112_M10_RBFM  !!!!PREMIUM
            '10049': 0.907,  # lvl:5 france_F33_S_35CA
            '11585': 0.912,  # lvl:6 france_F34_ARL_V39
            '10817': 0.787,  # lvl:7 france_F35_AMX_AC_Mle1946
            '12097': 0.71,  # lvl:8 france_F36_AMX_AC_Mle1948
            '61761': 1.5,  # lvl:8 france_F89_Canon_dassaut_de_105  !!!!PREMIUM
            '11073': 0.7,  # lvl:9 france_F37_AMX50_Foch
            '13889': 0.53,  # lvl:10 france_F64_AMX_50Fosh_155  !!!!PREMIUM
            '17729': 0.5299,  # lvl:10 france_F64_AMX_50Fosh_B
            # SPG
            '833': 1.15,  # lvl:2 france_F20_RenaultBS
            '3393': 1.08,  # lvl:3 france_F21_Lorraine39_L_AM
            '14657': 1.086,  # lvl:4 france_F66_AMX_Ob_Am105
            '4161': 1.104,  # lvl:5 france_F22_AMX_105AM
            '2113': 1.35,  # lvl:5 france_F28_105_leFH18B2  !!!!PREMIUM
            '4673': 1.122,  # lvl:6 france_F23_AMX_13F3AM
            '28225': 1.5,  # lvl:6 france_F23_AMX_13F3AM_MapsTraining_Dummy_SPG_2
            '7233': 0.9,  # lvl:7 france_F24_Lorraine155_50
            '7489': 0.71,  # lvl:8 france_F25_Lorraine155_51
            '14401': 0.64,  # lvl:9 france_F67_Bat_Chatillon155_55
            '11841': 0.78,  # lvl:10 france_F38_Bat_Chatillon155_58
        })
        self.COEFFICIENTS.update({
            # usa
            # lightTank
            '40993': 1.5,  # lvl:1 usa_A01_T1_Cunningham_bot
            '545': 1.365,  # lvl:1 usa_A01_T1_Cunningham
            '51489': 1.27,  # lvl:2 usa_A19_T2_lt  !!!!PREMIUM
            '53537': 1.45,  # lvl:2 usa_A74_T1_E6  !!!!PREMIUM
            '41761': 1.4,  # lvl:2 usa_A22_M5_Stuart_bootcamp
            '55073': 1.3,  # lvl:2 usa_A93_T7_Combat_Car  !!!!PREMIUM
            '41505': 1.5,  # lvl:2 usa_A03_M3_Stuart_bootcamp
            '1825': 1.102,  # lvl:2 usa_A02_M2_lt
            '289': 1.07,  # lvl:3 usa_A03_M3_Stuart
            '52001': 1.26,  # lvl:3 usa_A33_MTLS-1G14  !!!!PREMIUM
            '52769': 1.57,  # lvl:3 usa_A43_M22_Locust  !!!!PREMIUM
            '5153': 1.08,  # lvl:4 usa_A22_M5_Stuart
            '9761': 1.0,  # lvl:5 usa_A34_M24_Chaffee
            '5409': 1.1,  # lvl:5 usa_A23_M7_med
            '16673': 0.85,  # lvl:6 usa_A94_T37
            '15137': 0.88,  # lvl:6 usa_A71_T21
            '15649': 0.78,  # lvl:7 usa_A103_T71E1
            '19745': 0.78,  # lvl:7 usa_A112_T71E2R
            '17953': 0.68,  # lvl:8 usa_A97_M41_Bulldog
            '57889': 1.5,  # lvl:8 usa_A99_T92_LT  !!!!PREMIUM
            '18209': 0.67,  # lvl:9 usa_A100_T49
            '19489': 0.66,  # lvl:10 usa_A116_XM551
            # mediumTank
            '5665': 1.127,  # lvl:2 usa_A24_T2_med
            '41249': 1.4,  # lvl:2 usa_A24_T2_med_bot
            '34593': 1.26,  # lvl:3 usa_A148_Convertible_Medium_Tank_T3  !!!!PREMIUM
            '4897': 1.044,  # lvl:3 usa_A25_M2_med
            '3105': 1.109,  # lvl:4 usa_A04_M3_Grant
            '52257': 1.59,  # lvl:5 usa_A44_M4A2E4  !!!!PREMIUM
            '12577': 1.4,  # lvl:5 usa_A78_M4_Improved  !!!!PREMIUM
            '1057': 0.968,  # lvl:5 usa_A05_M4_Sherman
            '51745': 1.55,  # lvl:5 usa_A62_Ram-II  !!!!PREMIUM
            '59681': 1.22,  # lvl:6 usa_A118_M4_Thunderbolt  !!!!PREMIUM
            '1313': 0.868,  # lvl:6 usa_A06_M4A3E8_Sherman
            '56097': 1.22,  # lvl:6 usa_A104_M4A3E8A  !!!!PREMIUM
            '10017': 0.854,  # lvl:6 usa_A36_Sherman_Jumbo
            '11809': 1.3,  # lvl:7 usa_A86_T23E3  !!!!PREMIUM
            '1569': 0.776,  # lvl:7 usa_A07_T20
            '59937': 1.3,  # lvl:7 usa_A121_M26_Cologne  !!!!PREMIUM
            '2337': 1.6,  # lvl:8 usa_A08_T23
            '57377': 1.5,  # lvl:8 usa_A111_T25_Pilot  !!!!PREMIUM
            '14625': 0.67,  # lvl:8 usa_A90_T69
            '57121': 1.575,  # lvl:8 usa_A63_M46_Patton_KR  !!!!PREMIUM
            '34081': 1.45,  # lvl:8 usa_A149_AMBT  !!!!PREMIUM
            '62241': 1.5,  # lvl:8 usa_A127_TL_1_LPC  !!!!PREMIUM
            '13345': 1.575,  # lvl:8 usa_A80_T26_E4_SuperPershing  !!!!PREMIUM
            '53793': 1.5,  # lvl:8 usa_A81_T95_E2  !!!!PREMIUM
            '5921': 0.708,  # lvl:8 usa_A35_Pershing
            '8993': 0.751,  # lvl:9 usa_A63_M46_Patton
            '15905': 0.73,  # lvl:10 usa_A92_M60  !!!!PREMIUM
            '14113': 0.734,  # lvl:10 usa_A120_M48A5
            # heavyTank
            '3361': 1.094,  # lvl:5 usa_A09_T1_hvy
            '33': 1.62,  # lvl:5 usa_A21_T14  !!!!PREMIUM
            '801': 0.932,  # lvl:6 usa_A10_M6
            '3873': 0.836,  # lvl:7 usa_A11_T29
            '52513': 1.67,  # lvl:8 usa_A45_M6A2E1  !!!!PREMIUM
            '58657': 1.5,  # lvl:8 usa_A115_Chrysler_K_GF  !!!!PREMIUM
            '4385': 0.828,  # lvl:8 usa_A12_T32
            '59169': 1.575,  # lvl:8 usa_A117_T26E5_Patriot  !!!!PREMIUM
            '2849': 1.575,  # lvl:8 usa_A13_T34_hvy  !!!!PREMIUM
            '58913': 1.575,  # lvl:8 usa_A117_T26E5  !!!!PREMIUM
            '61985': 1.5,  # lvl:8 usa_A124_T54E2  !!!!PREMIUM
            '61729': 0.7799,  # lvl:9 usa_A125_AEP_1  !!!!PREMIUM
            '9505': 0.735,  # lvl:9 usa_A66_M103
            '15393': 0.7,  # lvl:9 usa_A89_T54E1
            '10785': 0.735,  # lvl:10 usa_A69_T110E5
            '14881': 0.73,  # lvl:10 usa_A67_T57_58
            '64801': 1.59,  # lvl:10 usa_A69_T110E5_bob
            '35361': 0.968,  # lvl:10 usa_A69_T110E5_cl  !!!!PREMIUM
            # AT-SPG
            '6177': 1.05,  # lvl:2 usa_A46_T3
            '6433': 0.95,  # lvl:3 usa_A109_T56_GMC
            '7713': 0.835,  # lvl:4 usa_A29_T40
            '10273': 0.899,  # lvl:4 usa_A57_M8A1
            '10529': 0.964,  # lvl:5 usa_A58_T67
            '6945': 0.976,  # lvl:5 usa_A30_M10_Wolverine
            '11553': 0.798,  # lvl:6 usa_A41_M18_Hellcat
            '7201': 0.861,  # lvl:6 usa_A31_M36_Slagger
            '61217': 1.2998,  # lvl:6 usa_A123_T78  !!!!PREMIUM
            '62497': 0.7979,  # lvl:7 usa_A130_Super_Hellcat  !!!!PREMIUM
            '56609': 1.4,  # lvl:7 usa_A102_T28_concept  !!!!PREMIUM
            '56353': 1.35,  # lvl:7 usa_A101_M56  !!!!PREMIUM
            '9249': 0.817,  # lvl:7 usa_A64_T25_AT
            '11041': 0.732,  # lvl:7 usa_A72_T25_2
            '8225': 0.724,  # lvl:8 usa_A39_T28
            '60449': 1.5,  # lvl:8 usa_A122_TS-5  !!!!PREMIUM
            '11297': 0.711,  # lvl:8 usa_A68_T28_Prototype
            '2593': 0.721,  # lvl:9 usa_A14_T30
            '8737': 0.69,  # lvl:9 usa_A40_T95
            '13857': 0.632,  # lvl:10 usa_A85_T110E3
            '13089': 0.625,  # lvl:10 usa_A83_T110E4
            # SPG
            '2081': 1.2,  # lvl:2 usa_A107_T1_HMC
            '3617': 1.1,  # lvl:3 usa_A16_M7_Priest
            '18465': 1.1,  # lvl:3 usa_A108_T18_HMC
            '4641': 1.08,  # lvl:4 usa_A17_M37
            '18721': 1.1,  # lvl:4 usa_A27_T82
            '4129': 1.17,  # lvl:5 usa_A18_M41
            '16417': 1.02,  # lvl:6 usa_A87_M44
            '7969': 0.83,  # lvl:7 usa_A32_M12
            '7457': 0.7,  # lvl:8 usa_A37_M40M43
            '16161': 0.69,  # lvl:9 usa_A88_M53_55
            '8481': 0.8,  # lvl:10 usa_A38_T92
        })
        self.COEFFICIENTS.update({
            # germany
            # lightTank
            '3089': 1.311,  # lvl:1 germany_G12_Ltraktor
            '2065': 1.0902,  # lvl:2 germany_G06_PzII
            '785': 1.093,  # lvl:2 germany_G07_Pz35t
            '47633': 1.2,  # lvl:2 germany_G139_MKA  !!!!PREMIUM
            '12817': 1.25,  # lvl:2 germany_G53_PzI
            '52497': 1.0,  # lvl:2 germany_G33_H39_captured  !!!!PREMIUM
            '60433': 1.2,  # lvl:2 germany_G108_PzKpfwII_AusfD  !!!!PREMIUM
            '4881': 1.085,  # lvl:3 germany_G102_Pz_III
            '63505': 1.2997,  # lvl:3 germany_G117_Toldi_III  !!!!PREMIUM
            '12561': 1.0,  # lvl:3 germany_G63_PzI_ausf_C
            '3345': 0.987,  # lvl:3 germany_G08_Pz38t
            '13073': 1.0,  # lvl:3 germany_G82_Pz_II_AusfG
            '51729': 1.2,  # lvl:3 germany_G36_PzII_J  !!!!PREMIUM
            '54801': 1.5,  # lvl:3 germany_G50_T-15  !!!!PREMIUM
            '8209': 1.053,  # lvl:4 germany_G52_Pz38_NA
            '6161': 1.05,  # lvl:4 germany_G25_PzII_Luchs
            '5393': 1.02,  # lvl:5 germany_G26_VK1602
            '25617': 0.817,  # lvl:6 germany_G158_VK2801_105_SPXXI  !!!!PREMIUM
            '10001': 0.825,  # lvl:6 germany_G66_VK2801
            '18961': 0.78,  # lvl:7 germany_G113_SP_I_C
            '14353': 1.4,  # lvl:7 germany_G85_Auf_Panther  !!!!PREMIUM
            '20241': 0.68,  # lvl:8 germany_G126_HWK_12
            '50961': 1.4,  # lvl:8 germany_G120_M41_90_GrandFinal  !!!!PREMIUM
            '47377': 1.5,  # lvl:8 germany_G140_HWK_30  !!!!PREMIUM
            '64017': 1.4,  # lvl:8 germany_G120_M41_90  !!!!PREMIUM
            '18449': 0.67,  # lvl:9 germany_G103_RU_251
            '19985': 0.66,  # lvl:10 germany_G125_Spz_57_Rh
            # mediumTank
            '51985': 1.26,  # lvl:3 germany_G34_S35_captured  !!!!PREMIUM
            '59665': 1.22,  # lvl:3 germany_G100_Gtraktor_Krupp  !!!!PREMIUM
            '17169': 1.0,  # lvl:3 germany_G83_Pz_IV_AusfA
            '13585': 1.1,  # lvl:4 germany_G86_VK2001DB
            '4369': 1.129,  # lvl:4 germany_G10_PzIII_AusfJ
            '17425': 1.05,  # lvl:4 germany_G80_Pz_IV_AusfD
            '54545': 1.52,  # lvl:5 germany_G46_T-25  !!!!PREMIUM
            '63249': 1.3999,  # lvl:5 germany_G116_Turan_III_prot  !!!!PREMIUM
            '6417': 1.168,  # lvl:5 germany_G28_PzIII_IV
            '2577': 1.1,  # lvl:5 germany_G13_VK3001H
            '55057': 1.4,  # lvl:5 germany_G70_PzIV_Hydro  !!!!PREMIUM
            '18193': 1.1,  # lvl:5 germany_G81_Pz_IV_AusfH
            '51473': 1.48,  # lvl:5 germany_G32_PzV_PzIV  !!!!PREMIUM
            '61457': 1.4,  # lvl:5 germany_G107_PzKpfwIII_AusfK  !!!!PREMIUM
            '57361': 1.26,  # lvl:6 germany_G77_PzIV_Schmalturm  !!!!PREMIUM
            '14097': 0.9,  # lvl:6 germany_G87_VK3002DB_V1
            '15889': 0.85,  # lvl:6 germany_G96_VK3002M
            '57617': 1.56,  # lvl:7 germany_G78_Panther_M10  !!!!PREMIUM
            '4113': 0.759,  # lvl:7 germany_G24_VK3002DB
            '1297': 0.805,  # lvl:7 germany_G03_PzV_Panther
            '8465': 0.791,  # lvl:8 germany_G64_Panther_II
            '60177': 1.5,  # lvl:8 germany_G106_PzKpfwPanther_AusfF  !!!!PREMIUM
            '64273': 1.5,  # lvl:8 germany_G119_Pz58_Mutz  !!!!PREMIUM
            '13841': 0.67,  # lvl:8 germany_G88_Indien_Panzer
            '63761': 1.0,  # lvl:8 germany_G119_Panzer58  !!!!PREMIUM
            '10257': 0.779,  # lvl:9 germany_G54_E-50
            '60945': 0.8,  # lvl:9 germany_G105_T-55_NVA_DDR  !!!!PREMIUM
            '14865': 0.75,  # lvl:9 germany_G91_Pro_Ag_A
            '14609': 0.75,  # lvl:10 germany_G89_Leopard1
            '12305': 0.73,  # lvl:10 germany_G73_E50_Ausf_M
            # heavyTank
            '52241': 1.36,  # lvl:4 germany_G35_B-1bis_captured  !!!!PREMIUM
            '13329': 1.05,  # lvl:4 germany_G90_DW_II
            '59409': 1.4,  # lvl:5 germany_G122_VK6501H  !!!!PREMIUM
            '49169': 1.2,  # lvl:6 germany_G136_Tiger_131  !!!!PREMIUM
            '2321': 0.931,  # lvl:6 germany_G15_VK3601H
            '52753': 1.2,  # lvl:6 germany_G137_PzVI_Tiger_217  !!!!PREMIUM
            '7185': 1.018,  # lvl:6 germany_G27_VK3001P
            '529': 0.901,  # lvl:7 germany_G04_PzVI_Tiger_I
            '62993': 1.5,  # lvl:7 germany_G118_VK4503  !!!!PREMIUM
            '10769': 0.804,  # lvl:7 germany_G57_PzVI_Tiger_P
            '46865': 1.5,  # lvl:8 germany_G143_E75_TS  !!!!PREMIUM
            '10513': 0.892,  # lvl:8 germany_G67_VK4502A
            '54289': 1.65,  # lvl:8 germany_G51_Lowe  !!!!PREMIUM
            '19729': 0.83,  # lvl:8 germany_G115_Typ_205B
            '5137': 0.854,  # lvl:8 germany_G16_PzVIB_Tiger_II
            '48913': 1.5,  # lvl:8 germany_G138_VK168_02  !!!!PREMIUM
            '56081': 1.5,  # lvl:8 germany_G141_VK7501K  !!!!PREMIUM
            '48145': 1.5,  # lvl:8 germany_G138_VK168_02_Mauerbrecher  !!!!PREMIUM
            '18705': 0.76,  # lvl:9 germany_G110_Typ_205
            '7441': 0.788,  # lvl:9 germany_G58_VK4502P
            '9745': 0.753,  # lvl:9 germany_G55_E-75
            '6929': 0.84,  # lvl:10 germany_G42_Maus
            '9489': 0.764,  # lvl:10 germany_G56_E-100
            '19473': 0.73,  # lvl:10 germany_G134_PzKpfw_VII
            '58641': 0.73,  # lvl:10 germany_G92_VK7201  !!!!PREMIUM
            # AT-SPG
            '3601': 0.987,  # lvl:2 germany_G21_PanzerJager_I
            '6673': 0.915,  # lvl:3 germany_G20_Marder_II
            '17937': 0.85,  # lvl:4 germany_G101_StuG_III
            '1809': 0.9125,  # lvl:4 germany_G09_Hetzer
            '11281': 0.85,  # lvl:4 germany_G39_Marder_III
            '1041': 1.0044,  # lvl:5 germany_G05_StuG_40_AusfG
            '60689': 1.5,  # lvl:5 germany_G104_Stug_IV  !!!!PREMIUM
            '16145': 0.95,  # lvl:5 germany_G76_Pz_Sfl_IVc
            '57105': 1.35,  # lvl:6 germany_G41_DickerMax  !!!!PREMIUM
            '1553': 0.98,  # lvl:6 germany_G17_JagdPzIV
            '11793': 0.95,  # lvl:6 germany_G40_Nashorn
            '55569': 1.3,  # lvl:7 germany_G48_E-25  !!!!PREMIUM
            '11025': 0.75,  # lvl:7 germany_G43_Sturer_Emil
            '61713': 1.3,  # lvl:7 germany_G109_Steyr_WT  !!!!PREMIUM
            '3857': 0.825,  # lvl:7 germany_G18_JagdPanther
            '50193': 1.5,  # lvl:8 germany_G114_Rheinmetall_Skorpian  !!!!PREMIUM
            '62481': 1.5,  # lvl:8 germany_G114_Skorpian  !!!!PREMIUM
            '48401': 1.5,  # lvl:8 germany_G112_KanonenJagdPanzer_105  !!!!PREMIUM
            '11537': 0.725,  # lvl:8 germany_G71_JagdPantherII
            '7697': 0.725,  # lvl:8 germany_G37_Ferdinand
            '16657': 0.72,  # lvl:8 germany_G99_RhB_Waffentrager
            '55313': 1.55,  # lvl:8 germany_G65_JagdTiger_SdKfz_185  !!!!PREMIUM
            '61969': 1.5,  # lvl:8 germany_G112_KanonenJagdPanzer  !!!!PREMIUM
            '16401': 0.7,  # lvl:9 germany_G97_Waffentrager_IV
            '7953': 0.68,  # lvl:9 germany_G44_JagdTiger
            '16913': 0.6,  # lvl:10 germany_G98_Waffentrager_E100
            '12049': 0.659,  # lvl:10 germany_G72_JagdPz_E100
            '19217': 0.6,  # lvl:10 germany_G121_Grille_15_L63
            # SPG
            '15121': 1.33,  # lvl:2 germany_G93_GW_Mk_VIe
            '2833': 1.18,  # lvl:3 germany_G11_Bison_I
            '5905': 1.08,  # lvl:3 germany_G19_Wespe
            '4625': 1.18,  # lvl:4 germany_G22_Sturmpanzer_II
            '15633': 1.03,  # lvl:4 germany_G95_Pz_Sfl_IVb
            '5649': 1.12,  # lvl:5 germany_G23_Grille
            '273': 1.17,  # lvl:6 germany_G02_Hummel
            '8977': 0.85,  # lvl:7 germany_G49_G_Panther
            '15377': 0.78,  # lvl:8 germany_G94_GW_Tiger_P
            '8721': 0.7,  # lvl:9 germany_G45_G_Tiger
            '9233': 0.82,  # lvl:10 germany_G61_G_E
        })
        self.COEFFICIENTS.update({
            # ussr
            # lightTank
            '3329': 0.918,  # lvl:1 ussr_R11_MS-1
            '1025': 0.95,  # lvl:2 ussr_R08_BT-2
            '41473': 1.75,  # lvl:2 ussr_R86_LTP_bootcamp
            '15361': 0.82,  # lvl:2 ussr_R42_T-60
            '4609': 0.892,  # lvl:2 ussr_R09_T-26
            '54529': 1.09,  # lvl:2 ussr_R84_Tetrarch_LL  !!!!PREMIUM
            '52737': 1.6,  # lvl:3 ussr_R67_M3_LL  !!!!PREMIUM
            '60929': 1.3,  # lvl:3 ussr_R105_BT_7A  !!!!PREMIUM
            '15105': 0.85,  # lvl:3 ussr_R43_T-70
            '3073': 0.836,  # lvl:3 ussr_R22_T-46
            '53505': 1.3145,  # lvl:3 ussr_R56_T-127  !!!!PREMIUM
            '52225': 1.3,  # lvl:3 ussr_R34_BT-SV  !!!!PREMIUM
            '769': 0.975,  # lvl:4 ussr_R03_BT-7
            '52481': 1.575,  # lvl:4 ussr_R31_Valentine_LL  !!!!PREMIUM
            '15873': 1.02,  # lvl:4 ussr_R44_T80
            '9729': 1.4,  # lvl:5 ussr_R70_T_50_2
            '9473': 0.964,  # lvl:5 ussr_R41_T-50
            '16641': 0.83,  # lvl:6 ussr_R101_MT25
            '19457': 0.78,  # lvl:7 ussr_R131_Tank_Gavalov
            '45569': 1.5,  # lvl:8 ussr_R158_LT_432  !!!!PREMIUM
            '18433': 0.68,  # lvl:8 ussr_R107_LTB
            '18177': 0.67,  # lvl:9 ussr_R109_T54S
            '19201': 0.66,  # lvl:10 ussr_R132_VNII_100LT
            # mediumTank
            '47873': 1.3,  # lvl:3 ussr_R143_T_29  !!!!PREMIUM
            '33281': 1.5,  # lvl:4 ussr_R185_T_34_L_11_1941  !!!!PREMIUM
            '52993': 1.437,  # lvl:4 ussr_R68_A-32  !!!!PREMIUM
            '1537': 0.997,  # lvl:4 ussr_R06_T-28
            '61441': 1.52,  # lvl:4 ussr_R118_T28_F30  !!!!PREMIUM
            '1': 1.094,  # lvl:5 ussr_R04_T-34
            '34305': 1.48,  # lvl:5 ussr_R193_M4A2_T_34  !!!!PREMIUM
            '51457': 1.5,  # lvl:5 ussr_R32_Matilda_II_LL  !!!!PREMIUM
            '47105': 1.45,  # lvl:5 ussr_R154_T_34E_1943  !!!!PREMIUM
            '58113': 1.22,  # lvl:6 ussr_R108_T34_85M  !!!!PREMIUM
            '12289': 0.83,  # lvl:6 ussr_R57_A43
            '2561': 0.906,  # lvl:6 ussr_R07_T-34-85
            '59393': 1.25,  # lvl:6 ussr_R117_T34_85_Rudy  !!!!PREMIUM
            '57089': 1.25,  # lvl:7 ussr_R98_T44_85  !!!!PREMIUM
            '35073': 1.5,  # lvl:7 ussr_R195_T34M_54  !!!!PREMIUM
            '8961': 0.928,  # lvl:7 ussr_R46_KV-13
            '6657': 0.858,  # lvl:7 ussr_R23_T-43
            '12545': 0.77,  # lvl:7 ussr_R59_A44
            '32257': 1.5,  # lvl:8 ussr_R180_Object_274_A  !!!!PREMIUM
            '48897': 1.5,  # lvl:8 ussr_R122_T44_100B  !!!!PREMIUM
            '13313': 0.67,  # lvl:8 ussr_R60_Object416
            '47617': 1.5,  # lvl:8 ussr_R146_STG  !!!!PREMIUM
            '59905': 1.5,  # lvl:8 ussr_R112_T54_45  !!!!PREMIUM
            '61953': 1.5,  # lvl:8 ussr_R122_T44_100  !!!!PREMIUM
            '46337': 1.5,  # lvl:8 ussr_R127_T44_100_U  !!!!PREMIUM
            '62977': 1.5,  # lvl:8 ussr_R127_T44_100_P  !!!!PREMIUM
            '47361': 1.5,  # lvl:8 ussr_R146_STG_Tday  !!!!PREMIUM
            '46081': 1.5,  # lvl:8 ussr_R127_T44_100_K  !!!!PREMIUM
            '4353': 0.802,  # lvl:8 ussr_R20_T-44
            '17665': 0.75,  # lvl:9 ussr_R104_Object_430_II
            '7937': 0.82,  # lvl:9 ussr_R40_T-54
            '33793': 1.52,  # lvl:9 ussr_R187_Object_590  !!!!PREMIUM
            '15617': 0.73,  # lvl:10 ussr_R95_Object_907  !!!!PREMIUM
            '21761': 0.73,  # lvl:10 ussr_R144_K_91
            '34049': 1.5,  # lvl:10 ussr_R97_Object_140_cl  !!!!PREMIUM
            '17153': 0.73,  # lvl:10 ussr_R96_Object_430B
            '13825': 0.78,  # lvl:10 ussr_R87_T62A
            '16897': 0.82,  # lvl:10 ussr_R97_Object_140
            '19969': 0.73,  # lvl:10 ussr_R148_Object_430_U
            # heavyTank
            '54017': 1.4734,  # lvl:5 ussr_R38_KV-220  !!!!PREMIUM
            '33025': 1.3,  # lvl:5 ussr_R186_KV_1_Screened  !!!!PREMIUM
            '51713': 1.575,  # lvl:5 ussr_R33_Churchill_LL  !!!!PREMIUM
            '11777': 1.0,  # lvl:5 ussr_R80_KV1
            '18689': 0.912,  # lvl:6 ussr_R13_KV-1s
            '11265': 0.922,  # lvl:6 ussr_R72_T150
            '2817': 0.583,  # lvl:6 ussr_R106_KV85
            '10497': 0.868,  # lvl:6 ussr_R77_KV2
            '49921': 1.5,  # lvl:7 ussr_R133_KV_122  !!!!PREMIUM
            '59137': 1.35,  # lvl:7 ussr_R71_IS_2B  !!!!PREMIUM
            '46593': 1.35,  # lvl:7 ussr_R156_IS_2M  !!!!PREMIUM
            '5889': 0.894,  # lvl:7 ussr_R39_KV-3
            '513': 0.935,  # lvl:7 ussr_R01_IS
            '9217': 1.5,  # lvl:8 ussr_R61_Object252  !!!!PREMIUM
            '63233': 1.5,  # lvl:8 ussr_R128_KV4_Kreslavskiy  !!!!PREMIUM
            '48641': 1.5,  # lvl:8 ussr_R134_Object_252K  !!!!PREMIUM
            '49665': 1.5,  # lvl:8 ussr_R134_Object_252U  !!!!PREMIUM
            '20481': 0.8,  # lvl:8 ussr_R139_IS_M
            '58881': 1.5,  # lvl:8 ussr_R113_Object_730  !!!!PREMIUM
            '11009': 0.922,  # lvl:8 ussr_R73_KV4
            '44289': 1.5,  # lvl:8 ussr_R165_Object_703_II  !!!!PREMIUM
            '62721': 1.5,  # lvl:8 ussr_R123_Kirovets_1  !!!!PREMIUM
            '53249': 1.5,  # lvl:8 ussr_R54_KV-5  !!!!PREMIUM
            '5377': 0.797,  # lvl:8 ussr_R19_IS-3
            '60417': 1.5,  # lvl:8 ussr_R115_IS-3_auto  !!!!PREMIUM
            '19713': 0.77,  # lvl:9 ussr_R151_Object_257_2
            '20737': 0.77,  # lvl:9 ussr_R153_Object_705
            '10753': 0.756,  # lvl:9 ussr_R63_ST_I
            '11521': 0.777,  # lvl:9 ussr_R81_IS8
            '6145': 0.783,  # lvl:10 ussr_R90_IS_4M
            '7169': 0.788,  # lvl:10 ussr_R45_IS-7
            '32001': 1.5,  # lvl:10 ussr_R178_Object_780  !!!!PREMIUM
            '20993': 0.73,  # lvl:10 ussr_R145_Object_705_A
            '22017': 0.73,  # lvl:10 ussr_R155_Object_277
            '58369': 0.7,  # lvl:10 ussr_R110_Object_260  !!!!PREMIUM
            '46849': 0.7,  # lvl:10 ussr_R157_Object_279R  !!!!PREMIUM
            # AT-SPG
            '5121': 0.964,  # lvl:2 ussr_R10_AT-1
            '41729': 1.75,  # lvl:2 ussr_R50_SU76I_bootcamp
            '54273': 1.2,  # lvl:3 ussr_R50_SU76I  !!!!PREMIUM
            '6913': 0.724,  # lvl:4 ussr_R25_GAZ-74b
            '6401': 0.795,  # lvl:4 ussr_R24_SU-76
            '53761': 1.3,  # lvl:5 ussr_R78_SU_85I  !!!!PREMIUM
            '257': 0.975,  # lvl:5 ussr_R02_SU-85
            '54785': 1.43,  # lvl:6 ussr_R49_SU100Y  !!!!PREMIUM
            '3585': 0.854,  # lvl:6 ussr_R17_SU-100
            '2305': 0.847,  # lvl:7 ussr_R18_SU-152
            '10241': 0.72,  # lvl:7 ussr_R74_SU100M1
            '59649': 1.35,  # lvl:7 ussr_R116_ISU122C_Berlin  !!!!PREMIUM
            '55297': 1.44,  # lvl:7 ussr_R89_SU122_44  !!!!PREMIUM
            '9985': 0.798,  # lvl:8 ussr_R58_SU-101
            '31745': 1.6,  # lvl:8 ussr_R177_ISU_152K_BL10  !!!!PREMIUM
            '48385': 1.5,  # lvl:8 ussr_R135_T_103  !!!!PREMIUM
            '58625': 1.0,  # lvl:8 ussr_R111_ISU130  !!!!PREMIUM
            '7425': 0.711,  # lvl:8 ussr_R47_ISU-152
            '8193': 0.62,  # lvl:9 ussr_R53_Object_704
            '12033': 0.702,  # lvl:9 ussr_R75_SU122_54
            '32769': 1.4734,  # lvl:9 ussr_R183_K_91_PT  !!!!PREMIUM
            '14337': 0.633,  # lvl:10 ussr_R93_Object263B
            '20225': 0.63,  # lvl:10 ussr_R149_Object_268_4
            '13569': 0.605,  # lvl:10 ussr_R88_Object268
            # SPG
            '3841': 0.98,  # lvl:2 ussr_R16_SU-18
            '7681': 0.964,  # lvl:3 ussr_R66_SU-26
            '4865': 1.044,  # lvl:4 ussr_R14_SU-5
            '16385': 1.12,  # lvl:5 ussr_R100_SU122A
            '5633': 1.0,  # lvl:6 ussr_R26_SU-8
            '16129': 0.945,  # lvl:7 ussr_R91_SU14_1
            '1793': 0.935,  # lvl:7 ussr_R15_S-51
            '4097': 0.78,  # lvl:8 ussr_R27_SU-14
            '8449': 0.68,  # lvl:9 ussr_R51_Object_212
            '8705': 0.76,  # lvl:10 ussr_R52_Object_261
        })


class BattleResultParser(object):
    def __init__(self):
        self.Threads = True
        self.ArenaIDQueue = Queue()
        self.ResultsCache = []
        self.ResultsAvailable = threading.Event()
        self.thread = threading.Thread(target=self.WaitResult)
        self.thread.setDaemon(True)
        self.thread.setName('WaitResult')
        self.thread.start()

    def CheckCallback(self, ArenaUniqueID, ErrorCode, battleResults):
        if ErrorCode in [-3, -5]:
            callback(1.0, lambda: self.ArenaIDQueue.put(ArenaUniqueID))
        elif ErrorCode >= 0:
            if ArenaUniqueID in self.ResultsCache:
                return
            calc.receiveBattleResult(True, battleResults)

    def WaitResult(self):
        while self.Threads:
            ArenaUniqueID = self.ArenaIDQueue.get()
            self.ResultsAvailable.wait()
            try:
                getPlayer().battleResultsCache.get(ArenaUniqueID, partial(self.CheckCallback, ArenaUniqueID))
            except StandardError:
                pass


# config = Config()
calc = CreditsCalculator()
results = BattleResultParser()


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(func, *args):
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        calc.timer()
    func(*args)


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new__destroyGUI(func, *args):
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        calc.stopBattle()
    func(*args)


@override(CrewWidget, '_CrewWidget__updateWidgetModel')
def new__updateWidgetModel(func, self):
    result = func(self)
    if g_currentVehicle.item:
        try:
            status = g_currentVehicle.itemsCache.items.stats.activePremiumExpiryTime > 0
        except StandardError:
            status = False
        try:
            calc.getHangarData(status)
        except Exception as e:
            logError('CreditCalc crew:', e)
    return result


@override(PlayerAvatar, 'onBattleEvents')
def new__onBattleEvents(func, self, events):
    func(self, events)
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        calc.onBattleEvents(events)


@override(LobbyView, '_populate')
def new__Populate(func, self):
    func(self)
    callback(3.0, calc.hangarMessage)


@override(BattleResultsFormatter, 'format')
def new__format(func, self, message, *args):
    arenaUniqueID = message.data.get('arenaUniqueID', 0)
    results.ArenaIDQueue.put(arenaUniqueID)
    return func(self, message, *args)


def onAccountBecomePlayer():
    results.ResultsAvailable.set()


def IntoBattle():
    results.ResultsAvailable.clear()



g_entitiesFactories.addSettings(ViewSettings(AS_ALIASES, CreditsCalculator, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))


g_playerEvents.onBattleResultsReceived += calc.receiveBattleResult
g_playerEvents.onAvatarReady += IntoBattle
g_playerEvents.onAccountBecomePlayer += onAccountBecomePlayer


def fini():
    results.Threads = False


def jsonGenerator(nations, onlyNew=False):
    import os as _os
    import codecs as _codecs
    import json as _json
    from CurrentVehicle import g_currentVehicle as g_currentVehicle
    COEFFICIENTS = {}
    PATH = ''.join(['./mods/configs/Driftkings/%s/' % config.ID])
    if _os.path.isfile(PATH + 'sw_templates.json'):
        try:
            with _codecs.open(PATH + 'sw_templates.json', 'r', encoding='utf-8-sig') as fl:
                data = fl.read().decode('utf-8-sig')
                COEFFICIENTS.update(calc.byte_ify(_json.loads(data)))
                fl.close()
        except StandardError:
            COEFFICIENTS.update({})

    def deCode(compactDescr):
        test = '%s' % compactDescr
        if test in COEFFICIENTS:
            return test, round(COEFFICIENTS[test], 6)
        return test, 0.0
    items = g_currentVehicle.itemsCache.items.getVehicles()

    def getData(_nation, _role):
        text = ''
        for level in xrange(1, 11):
            for compactDescr in items:
                vehicle = items[compactDescr]
                if vehicle.nationName == _nation and vehicle.descriptor.level == level and vehicle.type == _role:
                    vehicleCompDesc, balance_co_eff = deCode(compactDescr)
                    thatPremium = ' !!!!PREMIUM' if vehicle.isPremium or vehicle.isPremiumIGR else ''
                    details = '#lvl:%s %s %s' % (vehicle.descriptor.level, vehicle.name.replace(':', '_'), thatPremium)
                    if not balance_co_eff:
                        text += "#'%s': %s, %s https://premomer.org/tank.php?id=%s\n" % (compactDescr, None, details, compactDescr)
                    if not onlyNew and balance_co_eff:
                        text += "'%s': %s, %s\n" % (compactDescr, balance_co_eff, details)
    if not nations:
        nations = ['ussr', 'germany', 'uk', 'japan', 'usa', 'china', 'france', 'czech', 'sweden', 'poland', 'italy']
    roles = ['lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG']
    for nation in nations:
        for _role in roles:
            getData(nation, _role)
