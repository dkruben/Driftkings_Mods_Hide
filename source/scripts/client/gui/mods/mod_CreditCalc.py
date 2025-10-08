# -*- coding: utf-8 -*-
import codecs
import collections
import json
import os
import threading
from Queue import Queue
from functools import partial

import BattleReplay
from Event import SafeEvent
import Keys
import ResMgr
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from CurrentVehicle import g_currentVehicle
from PlayerEvents import g_playerEvents
from constants import ARENA_BONUS_TYPE
from frameworks.wulf import WindowLayer
from gui import InputHandler
from gui.Scaleform.daapi.view.lobby.LobbyView import LobbyView
from gui.Scaleform.daapi.view.meta.CrewOperationsPopOverMeta import CrewOperationsPopOverMeta
from gui.Scaleform.framework import ScopeTemplates, ViewSettings, g_entitiesFactories
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.HANGAR_ALIASES import HANGAR_ALIASES
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.arena_info import vos_collections
from gui.battle_control.battle_constants import VEHICLE_DEVICE_IN_COMPLEX_ITEM, VEHICLE_VIEW_STATE
from gui.battle_control.controllers import feedback_events
from gui.impl.lobby.crew.widget.crew_widget import CrewWidget
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
from gui.shared.formatters import icons
from gui.shared.gui_items import Vehicle
from gui.shared.personality import ServicesLocator
from helpers import getLanguageCode
from messenger.formatters.service_channel import BattleResultsFormatter
from gambiter import g_guiFlash
from gambiter.flash import COMPONENT_ALIGN, COMPONENT_EVENT, COMPONENT_TYPE

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, getPlayer, getEntity, callback, calculate_version


CHASSIS_ALL_ITEMS = frozenset(VEHICLE_DEVICE_IN_COMPLEX_ITEM.keys() + VEHICLE_DEVICE_IN_COMPLEX_ITEM.values())
DAMAGE_EVENTS = frozenset([BATTLE_EVENT_TYPE.RADIO_ASSIST, BATTLE_EVENT_TYPE.TRACK_ASSIST, BATTLE_EVENT_TYPE.STUN_ASSIST, BATTLE_EVENT_TYPE.DAMAGE, BATTLE_EVENT_TYPE.TANKING, BATTLE_EVENT_TYPE.RECEIVED_DAMAGE])

DEBUG = True
DEBUG_COEFF = True


class ConfigInterface(DriftkingsConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = '(spoter) re-coded by Driftkings'
        self.data = {
            'enabled': True,
            'battle_x': 60,
            'battle_y': -252,
            'hangar_x': 325.0,
            'hangar_y': 505.0,
            'battleBackground': True,
            'battleShow': True,
            'hangarBackground': True,
            'hangarShow': True,
            'showDebugInfo': False,
            'autoSaveCoefficients': True
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_label_text': 'Calc Credits in Battle:',
            'UI_setting_label_tooltip': '+1000 or -1000 silver difference: that\'s normal dispersion, if greater: Play one battle without damage.',
            'UI_setting_label1_text': 'Wait until the battle:',
            'UI_setting_label1_tooltip': 'Is complete without escape into the hangar. Income: Green Victory, Red Defeat, Outcome: ammo and consumables.',
            'UI_setting_label2_text': 'Additional info in battle: Press Alt and Control buttons',
            'UI_setting_battleBackground_text': 'Background in battle',
            'UI_setting_battleBackground_tooltip': 'Enables/disables background for the text in battle',
            'UI_setting_hangarBackground_text': 'Background in hangar',
            'UI_setting_hangarBackground_tooltip': 'Enables/disables background for the text in hangar',
            'UI_setting_hangarShow_text': 'Show in hangar',
            'UI_setting_hangarShow_tooltip': 'Shows or hides credit calculator information in the hangar',
            'UI_setting_battleShow_text': 'Show in battle',
            'UI_setting_battleShow_tooltip': 'Shows or hides credit calculator information during battle',
            'UI_setting_battle_x_text': 'Battle text position: X',
            'UI_setting_battle_x_tooltip': 'Adjusts the horizontal position of the text during battle',
            'UI_setting_battle_y_text': 'Battle text position: Y',
            'UI_setting_battle_y_tooltip': 'Adjusts the vertical position of the text during battle',
            'UI_setting_hangar_x_text': 'Hangar text position: X',
            'UI_setting_hangar_x_tooltip': 'Adjusts the horizontal position of the text in hangar',
            'UI_setting_hangar_y_text': 'Hangar text position: Y',
            'UI_setting_hangar_y_tooltip': 'Adjusts the vertical position of the text in hangar',
            'UI_setting_showDebugInfo_text': 'Show debug information',
            'UI_setting_showDebugInfo_tooltip': 'Displays debug information useful for troubleshooting',
            'UI_setting_autoSaveCoefficients_text': 'Auto-save tank coefficients',
            'UI_setting_autoSaveCoefficients_tooltip': 'Automatically saves tank coefficients for more accurate calculations',
        }

        super(ConfigInterface, self).init()

    def createTemplate(self):
        label = self.tb.createLabel('label')
        label['text'] += ''
        label1 = self.tb.createLabel('label1')
        label1['text'] += ''
        label2 = self.tb.createLabel('label2')
        label2['text'] += ''
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                label,
                label1,
                label2,
                self.tb.createControl('battleShow'),
                self.tb.createControl('battleBackground'),
                self.tb.createSlider('battle_x', -2000, 2000, 1, 'Horizontal position in battle'),
                self.tb.createSlider('battle_y', -2000, 2000, 1, 'Vertical position in battle')
            ],
            'column2': [
                self.tb.createControl('hangarShow'),
                self.tb.createControl('hangarBackground'),
                self.tb.createSlider('hangar_x', -2000, 2000, 1, 'Horizontal position in hangar'),
                self.tb.createSlider('hangar_y', -2000, 2000, 1, 'Vertical position in hangar'),
                self.tb.createControl('showDebugInfo'),
                self.tb.createControl('autoSaveCoefficients')
            ]
        }

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)
        if 'battleShow' in settings or 'hangarShow' in settings:
            if 'flash' in globals():
                if settings.get('battleShow') is not None and flash:
                    flash.visible(settings['battleShow'])
            if 'flashInHangar' in globals() and 'calc' in globals():
                if settings.get('hangarShow') is not None:
                    calc.hangarMessage()
        if 'showDebugInfo' in settings:
            global DEBUG, DEBUG_COEFF
            DEBUG = settings['showDebugInfo']
            DEBUG_COEFF = settings['showDebugInfo']


class FlashInHangar(object):
    def __init__(self):
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED, self.__componentRegisteringHandler, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.addListener(events.AppLifeCycleEvent.INITIALIZED, self.__onAppInitialized, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_entitiesFactories.addSettings(ViewSettings('CreditCalc', FlashMeta, 'CreditCalc.swf', WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
        # Events
        self.onHeaderUpdate = SafeEvent()
        self.onHangarLoaded = SafeEvent()
        self.setPosition = SafeEvent()
        self.setBackground = SafeEvent()
        self.setText = SafeEvent()

    @staticmethod
    def __onAppInitialized(event):
        if event.ns == APP_NAME_SPACE.SF_LOBBY:
            app = ServicesLocator.appLoader.getApp(event.ns)
            if app is None:
                return
            app.loadView(SFViewLoadParams('CreditCalc'))

    def __componentRegisteringHandler(self, event):
        if event.alias == HANGAR_ALIASES.AMMUNITION_PANEL:
            if not config.data['hangarShow']:
                return
            self.setPosition(config.data['hangar_x'], config.data['hangar_y'])
            self.setBackground(config.data['hangarBackground'], '#000000', 0.4)


class FlashMeta(View):

    def _populate(self):
        super(FlashMeta, self)._populate()
        flashInHangar.setText += self.as_setTextS
        flashInHangar.setPosition += self.as_setPositionS
        flashInHangar.setBackground += self.as_setBackgroundS

    def _dispose(self):
        super(FlashMeta, self)._dispose()

    def py_log(self, text):
        print('[%s]: %s' % (config.ID, text))

    @staticmethod
    def py_newPos(posX, posY):
        config.onApplySettings({'hangar_x': posX, 'hangar_y': posY})

    def as_setTextS(self, text):
        if self._isDAAPIInited():
            self.flashObject.as_setText(text)

    def as_setPositionS(self, x, y):
        if self._isDAAPIInited():
            self.flashObject.as_setPosition(x, y)

    def as_setBackgroundS(self, enabled, color, alpha):
        if self._isDAAPIInited():
            self.flashObject.as_setBackground(enabled, color, alpha)


class MyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        super(MyJSONEncoder, self).__init__(*args, **kwargs)
        self.current_indent = 0
        self.current_indent_str = ''
        self.indent = 4

    def encode(self, o):
        if isinstance(o, (list, tuple)):
            primitives_only = not any(isinstance(item, (list, tuple, dict)) for item in o)
            output = []
            if primitives_only:
                output = [json.dumps(item, ensure_ascii=False, encoding='utf-8-sig') for item in o]
                return '[ ' + ', '.join(output) + ' ]'
            else:
                self.current_indent += self.indent
                self.current_indent_str = " " * self.current_indent
                output = [self.current_indent_str + self.encode(item) for item in o]
                self.current_indent -= self.indent
                self.current_indent_str = " " * self.current_indent
                return '[\n' + ',\n'.join(output) + '\n' + self.current_indent_str + ']'
        elif isinstance(o, dict):
            self.current_indent += self.indent
            self.current_indent_str = " " * self.current_indent
            output = [self.current_indent_str + json.dumps(key, ensure_ascii=False, encoding='utf-8-sig') + ': ' + self.encode(value) for key, value in o.iteritems()]
            self.current_indent -= self.indent
            self.current_indent_str = " " * self.current_indent
            return '{\n' + ',\n'.join(output) + "\n" + self.current_indent_str + '}'
        else:
            return json.dumps(o, ensure_ascii=False, encoding='utf-8-sig')


class CreditsCalculator(object):
    ASSIST_COEFF = 5
    SPOT_COEFF = 100
    DAMAGE_STUN_COEFF = 7.7
    DAMAGE_SPOTTED_COEFF = 7.5
    DAMAGE_SELF_COEFF = 10

    def __init__(self):
        self._coefficients = {}
        self._initializeCoefficients()
        self._coefficients['USE_DATA'] = False
        self.AVERAGES = [
            (1.37, 1.37), (1.13, 1.28), (1.04, 1.35), (1.029, 1.42),
            (1.04, 1.5), (0.92, 1.3), (0.82, 1.4), (0.75, 1.5),
            (0.72, 0.72), (0.71, 0.72)]
        self.coeffDefaults = sorted([0.53, 0.583, 0.6, 0.605, 0.62, 0.625, 0.63, 0.632, 0.633, 0.64, 0.65, 0.659, 0.66, 0.67, 0.6745, 0.68, 0.69,
                                     0.7, 0.702, 0.708, 0.71, 0.711, 0.715, 0.72, 0.721, 0.724, 0.725, 0.73, 0.732, 0.734, 0.735, 0.745, 0.75,
                                     0.751, 0.752, 0.753, 0.756, 0.759, 0.76, 0.764, 0.77, 0.774, 0.776, 0.777, 0.779, 0.78, 0.782, 0.783, 0.787,
                                     0.788, 0.79, 0.791, 0.793, 0.795, 0.797, 0.798, 0.8, 0.802, 0.804, 0.805, 0.817, 0.82, 0.824, 0.825, 0.828, 0.83,
                                     0.835, 0.836, 0.84, 0.847, 0.85, 0.854, 0.858, 0.861, 0.865, 0.868, 0.873, 0.874, 0.88, 0.883, 0.892, 0.894, 0.899,
                                     0.9, 0.901, 0.906, 0.907, 0.909, 0.912, 0.9125, 0.915, 0.918, 0.922, 0.925, 0.928, 0.93, 0.931, 0.932, 0.935, 0.943,
                                     0.945, 0.95, 0.964, 0.968, 0.969, 0.975, 0.976, 0.98, 0.987, 0.99, 0.997, 1.0, 1.0044, 1.0074, 1.012, 1.018,
                                     1.02, 1.025, 1.026, 1.03, 1.0336, 1.044, 1.045, 1.046, 1.05, 1.053, 1.057, 1.07, 1.077, 1.08, 1.085, 1.086, 1.088,
                                     1.089, 1.09, 1.0902, 1.093, 1.094, 1.1, 1.102, 1.104, 1.108, 1.109, 1.11, 1.113, 1.115, 1.12, 1.122, 1.127, 1.128,
                                     1.129, 1.14, 1.1425, 1.15, 1.154, 1.1585, 1.168, 1.17, 1.1782, 1.18, 1.199, 1.2, 1.21, 1.219, 1.22, 1.25, 1.253,
                                     1.2558, 1.26, 1.27, 1.276, 1.3, 1.311, 1.3145, 1.33, 1.35, 1.36, 1.365, 1.38, 1.4, 1.419, 1.43, 1.437, 1.44, 1.445,
                                     1.45, 1.46, 1.4734, 1.48, 1.485, 1.49, 1.5, 1.52, 1.53, 1.55, 1.56, 1.57, 1.575, 1.59, 1.6, 1.62, 1.63, 1.637, 1.64,
                                     1.65, 1.67, 1.75, 1.81])
        self._setupFilePaths()
        self.readJson()
        self.PREMIUM_ACC = self._coefficients['USE_DATA']
        self.iconCredits = '<img src=\"img://gui/maps/icons/quests/bonuses/big/credits.png\" vspace=\"-7\" width=\"20\" height=\"20\" />'
        self.textWin = ''
        self.textDEFEAT = ''
        self.tempResults = {}
        self.item = None
        self.altMode = False
        self.ctrlMode = False
        self._initializeStateVariables()

    def _initializeStateVariables(self):
        self.hangarOutcome = 0
        self.hangarItems = {}
        self.hangarAmmo = {}
        self.killed = False
        self.repairCost = 0
        self.costRepairs = {}
        self.usedItems = {}
        self.hangarHeader = ''
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
        self.premium = 1.0
        self.compactDescr = None
        self.balanceCoeff = 0.0
        self.level = 0
        self.name = ""
        self.vehicleName = ""

    def _setupFilePaths(self):
        self.PATH = os.path.join('mods', 'configs', 'Driftkings', config.ID, 'system')
        if not os.path.exists(self.PATH):
            try:
                os.makedirs(self.PATH)
            except (IOError, OSError):
                pass
        self.PATH = os.path.join(self.PATH, '')

    def byte_ify(self, inputs):
        if inputs is None:
            return None
        if isinstance(inputs, dict):
            return {self.byte_ify(key): self.byte_ify(value) for key, value in inputs.iteritems()}
        elif isinstance(inputs, list):
            return [self.byte_ify(element) for element in inputs]
        elif isinstance(inputs, unicode):
            return inputs.encode('utf-8')
        else:
            return inputs

    def writeJson(self):
        try:
            if not os.path.exists(self.PATH):
                os.makedirs(self.PATH)
            with codecs.open(self.PATH + 'sw_templates.json', 'w', encoding='utf-8-sig') as json_file:
                sorted_coeffs = collections.OrderedDict(sorted(self._coefficients.items(), key=lambda t: t[0]))
                data = json.dumps(sorted_coeffs, sort_keys=True, indent=4, ensure_ascii=False, encoding='utf-8-sig', separators=(',', ': '), cls=MyJSONEncoder)
                json_file.write('%s' % self.byte_ify(data))
        except (IOError, OSError) as e:
            print("Error writing coefficients to file: {}".format(e))

    def readJson(self):
        try:
            if os.path.isfile(self.PATH + 'sw_templates.json'):
                with codecs.open(self.PATH + 'sw_templates.json', 'r', encoding='utf-8-sig') as json_file:
                    data = json_file.read().decode('utf-8-sig')
                    self._coefficients.update(self.byte_ify(json.loads(data)))
            else:
                self.writeJson()
        except (IOError, ValueError) as e:
            print("Error reading coefficients from file: {}".format(e))
            self.writeJson()

    def getHangarData(self, isPremium):
        if self._coefficients['USE_DATA'] != isPremium:
            self._coefficients['USE_DATA'] = isPremium
            self.writeJson()
        self.PREMIUM_ACC = isPremium
        outcome = 0
        if g_currentVehicle.item and hasattr(g_currentVehicle.item, 'battleBoosters'):
            for installedItem in g_currentVehicle.item.battleBoosters.installed.getItems():
                price = installedItem.buyPrices.getSum().price.credits
                outcome += price if not installedItem.inventoryCount else 0
        self.hangarOutcome = outcome
        self.hangarItems = {}
        if g_currentVehicle.item and hasattr(g_currentVehicle.item, 'consumables'):
            for installedItem in g_currentVehicle.item.consumables.installed.getItems():
                price = installedItem.buyPrices.getSum().price.credits
                self.hangarItems[installedItem.intCD] = [price if not installedItem.inventoryCount else 0, price if not installedItem.inventoryCount else installedItem.getSellPrice().price.credits]
        # Store ammunition costs
        self.hangarAmmo = {}
        if g_currentVehicle.item and hasattr(g_currentVehicle.item, 'gun'):
            for ammo in g_currentVehicle.item.gun.defaultAmmo:
                self.hangarAmmo[ammo.intCD] = [ammo.buyPrices.getSum().price.credits if not ammo.inventoryCount else ammo.getSellPrice().price.credits, 0, 0]
        if g_currentVehicle.item:
            if self.item == g_currentVehicle.item.descriptor.type.compactDescr:
                return
            vehicleCompDesc, balanceCoeff = self.deCode(g_currentVehicle.item.descriptor.type.compactDescr)
            notSavedCoeff = not balanceCoeff
            if notSavedCoeff:
                ids = 1 if 'premium' in g_currentVehicle.item.tags else 0
                balanceCoeff = self.AVERAGES[g_currentVehicle.item.level - 1][ids]
            text = '<b>  {0} calcCredits {1} {0}\n '.format(icons.nutStat() * 3, 'by <font color=\"#6595EE\">Driftkings</font>')
            text += icons.makeImageTag(Vehicle.getTypeSmallIconPath(g_currentVehicle.item.type, g_currentVehicle.item.isPremium), width=30, height=30, vSpace=-7 if g_currentVehicle.item.isPremium else -5) + g_currentVehicle.item.shortUserName
            text += ' : %s %s%s%% %s</b>' % (icons.creditsBig(), 'coeff: ~' if notSavedCoeff else 'coeff: ', round(balanceCoeff * 100, 2), '!!!' if notSavedCoeff else '')
            self.hangarHeader = text
            self.hangarMessage()
            self.item = g_currentVehicle.item.descriptor.type.compactDescr

    def timer(self):
        player = getPlayer()
        vehicle = player.getVehicleAttached()
        if vehicle:
            self.startBattle()
            return
        callback(0.1, self.timer)

    def code(self, compactDescr, balanceCoEff):
        test = '%s' % compactDescr
        self._coefficients[test] = balanceCoEff
        self.writeJson()
        return test, self._coefficients[test]

    def deCode(self, compactDescr):
        test = '%s' % compactDescr
        if test in self._coefficients:
            return test, round(self._coefficients[test], 6)
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
        flash.startBattle()
        flash.visible(False)
        vehicle = player.getVehicleAttached()
        self._storeRepairCosts(vehicle)
        if not self.hangarItems:
            self._initializeDefaultItems()
        self.usedItems = {}
        self.item = None
        # Store vehicle info
        self.name = vehicle.typeDescriptor.name
        self.vehicleName = player.guiSessionProvider.getCtx().getPlayerFullNameParts(vID=vehicle.id).vehicleName
        self.level = vehicle.typeDescriptor.level
        self.textWin = ''
        self.textDEFEAT = ''
        player = getPlayer()
        arenaDP = player.guiSessionProvider.getArenaDP()
        self.listAlly = vos_collections.AllyItemsCollection().ids(arenaDP)
        self.listAlly.remove(player.playerVehicleID)
        self.PREMIUM_ACC = self._coefficients['USE_DATA']
        self.readJson()
        self._resetBattleStats()
        self.premium = 1.5 if self.PREMIUM_ACC else 1.0
        # Get vehicle coefficient
        self.compactDescr, self.balanceCoeff = self.deCode(vehicle.typeDescriptor.type.compactDescr)
        if not self.balanceCoeff:
            ids = 1 if 'premium' in vehicle.typeDescriptor.type.tags else 0
            self.balanceCoeff = self.AVERAGES[self.level - 1][ids]
        self.killed = False
        self.repairCost = 0
        self.calc()

    def _storeRepairCosts(self, vehicle):
        self.costRepairs = {
            'gun': vehicle.typeDescriptor.gun.maxRepairCost,
            'engine': vehicle.typeDescriptor.engine.maxRepairCost,
            'turretRotator': vehicle.typeDescriptor.turret.turretRotatorHealth.maxRepairCost,
            'surveyingDevice': vehicle.typeDescriptor.turret.surveyingDeviceHealth.maxRepairCost,
            'ammoBay': vehicle.typeDescriptor.hull.ammoBayHealth.maxRepairCost,
            'radio': vehicle.typeDescriptor.radio.maxRepairCost,
            'fuelTank': vehicle.typeDescriptor.fuelTank.maxRepairCost,
            'chassis': vehicle.typeDescriptor.chassis.maxRepairCost
        }
        self.costRepairs.update({name: vehicle.typeDescriptor.chassis.maxRepairCost for name in CHASSIS_ALL_ITEMS})

    def _initializeDefaultItems(self):
        self.hangarItems = {
            763: (3000, 3000), 1019: (20000, 20000),
            1275: (3000, 3000), 1531: (20000, 20000),
            1787: (5000, 5000), 4859: (20000, 20000),
            4091: (20000, 20000), 2299: (20000, 20000),
            2555: (20000, 20000), 3067: (20000, 20000),
            251: (3000, 3000), 3323: (3000, 3000),
            4347: (5000, 5000), 3579: (20000, 20000),
            15867: (20000, 20000), 25851: (20000, 20000),
            16123: (20000, 20000), 2043: (5000, 5000),
            16379: (20000, 20000), 16635: (20000, 20000),
            4603: (20000, 20000), 507: (20000, 20000)
        }

    def _resetBattleStats(self):
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
        return distSq > circularVisionRadius * circularVisionRadius

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
        self.repairCost = 0
        if state == VEHICLE_VIEW_STATE.DEVICES:
            player = getPlayer()
            if not player:
                return
            ctrl = player.guiSessionProvider.shared
            if not ctrl or not hasattr(ctrl, 'equipments'):
                return
            repairs = 0
            for equipment in ctrl.equipments.iterEquipmentsByTag('repairkit'):
                if not equipment or len(equipment) < 2:
                    continue
                entities = equipment[1].getEntitiesIterator()
                for itemName, deviceState in entities:
                    if itemName not in self.costRepairs:
                        continue
                    if deviceState == 'destroyed':
                        repairs += self.costRepairs[itemName]
                    elif deviceState == 'critical':
                        repairs += self.costRepairs[itemName] / 2
            self.repairCost = int(round(repairs))
        self.calc()

    def onVehicleKilled(self, targetID, *_):
        player = getPlayer()
        vehicle = player.getVehicleAttached()
        if targetID == vehicle.id:
            self.killed = True
            getMaxRepairCost = vehicle.typeDescriptor.getMaxRepairCost() - vehicle.typeDescriptor.maxHealth
            self.repairCost = int(round(getMaxRepairCost - getMaxRepairCost * vehicle.health / round(vehicle.typeDescriptor.maxHealth)))
            ctrl = player.guiSessionProvider.shared
            repairs = 0
            for equipment in ctrl.equipments.iterEquipmentsByTag('repairkit'):
                for itemName, deviceState in equipment[1].getEntitiesIterator():
                    if deviceState == 'destroyed':
                        if itemName in self.costRepairs:
                            repairs += self.costRepairs[itemName]
                    elif deviceState == 'critical':
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

    def onShellsAdded(self, intCD, quantity, *_):
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
        if not (DEBUG or DEBUG_COEFF):
            return
        assistCoeff = self.ASSIST_COEFF
        spotCoeff = self.SPOT_COEFF
        damageStunCoeff = self.DAMAGE_STUN_COEFF
        damageSpottedCoeff = self.DAMAGE_SPOTTED_COEFF
        damageSelfCoeff = self.DAMAGE_SELF_COEFF
        defeatCredits = self.level * 700
        winCredits = self.level * 1300
        assistCredits = self.ASSIST * assistCoeff
        spotCredits = self.SPOT * spotCoeff
        stunCredits = self.DAMAGE_STUN * damageStunCoeff
        damageMinCredits = (self.DAMAGE_SELF_SPOT * damageSelfCoeff + (self.DAMAGE_UNKNOWN_SPOT + self.DAMAGE_OTHER_SPOT) * damageSpottedCoeff)
        damageMaxCredits = ((self.DAMAGE_SELF_SPOT + self.DAMAGE_UNKNOWN_SPOT) * damageSelfCoeff + self.DAMAGE_OTHER_SPOT * damageSpottedCoeff)
        outcomeCredits = self.battleOutcome()
        self.DefeatResult = int(int(self.balanceCoeff * int(defeatCredits + assistCredits + spotCredits + damageMaxCredits + stunCredits) - 0.5) * self.premium + 0.5)
        self.DefeatResultMin = int(int(self.balanceCoeff * int(defeatCredits + assistCredits + spotCredits + damageMinCredits + stunCredits) - 0.5) * self.premium + 0.5)
        self.WinResult = int(int(self.balanceCoeff * int(winCredits + assistCredits + spotCredits + damageMaxCredits + stunCredits) - 0.5) * self.premium + 0.5)
        self.WinResultMin = int(int(self.balanceCoeff * int(winCredits + assistCredits + spotCredits + damageMinCredits + stunCredits) - 0.5) * self.premium + 0.5)
        if not hangar and flash:
            self._updateBattleUI(outcomeCredits)

    def _updateBattleUI(self, outcomeCredits):
        textWinner = self.correctedText(self.WinResultMin, self.WinResult, outcomeCredits)
        textDefeat = self.correctedText(self.DefeatResult, self.DefeatResult, outcomeCredits)
        colorWin = '#80D639'
        colorDefeat = '#FF6347'
        self.textWin = '<font size=\"20\" color=\"%s\">~%s%s</font>' % (colorWin, self.iconCredits, textWinner)
        self.textDEFEAT = '<font size=\"20\" color=\"%s\">~%s%s</font>' % (colorDefeat, self.iconCredits, textDefeat)
        self._storeBattleResults()
        flash.visible(True)
        flash.setCreditsText(self.textWin if not self.altMode else self.textDEFEAT)

    def _storeBattleResults(self):
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
        self.tempResults[self.compactDescr]['damage'] = (self.DAMAGE_SELF_SPOT + self.DAMAGE_UNKNOWN_SPOT + self.DAMAGE_OTHER_SPOT + self.DAMAGE_STUN)
        self.tempResults[self.compactDescr]['assist'] = self.ASSIST
        self.tempResults[self.compactDescr]['spot'] = self.SPOT
        if self.tempResults[self.compactDescr]['repairCost'] == self.repairCost:
            self.tempResults[self.compactDescr]['clearRepair'] = True
        else:
            self.tempResults[self.compactDescr]['clearRepair'] = False

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

    def correctedText(self, v_min, v_max, outcome):
        out = '<font color=\"#FF0000\"> -%s</font>' % outcome if outcome else ''
        if v_min != v_max:
            if self.ctrlMode:
                return '%s[%s]%s' % (v_min, int(v_max * 1.05), out)
            return '%s%s' % (v_min, out)
        return '%s%s' % (v_max, out)

    def getDebugText(self):
        debugText = 'Coeff: %s: %s\n' % ('MISS' if self.compactDescr not in self._coefficients else 'FOUND', self.balanceCoeff)
        if self.compactDescr not in self._coefficients:
            debugText += '\nCredit Calc need learn\non that vehicle\n'
            if not self.tempResults[self.compactDescr]['damage']:
                debugText += 'JUST SUICIDE FAST plz!\n'
                debugText += 'And wait until battle down\n'
            else:
                debugText += 'wrong battle! play again\n'
        return debugText

    def stopBattle(self):
        """Clean up after battle ends."""
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
        flash.stopBattle()
        self._logDebugInfo()
        self._resetAfterBattle()

    def _logDebugInfo(self):
        if DEBUG:
            if self.compactDescr not in self.tempResults:
                return
            self.compactDescr, self.balanceCoeff = self.deCode(self.tempResults[self.compactDescr]['descr'])
            print('tempResults', self.tempResults[self.compactDescr])
            outcomeCredits = self.battleOutcome()
            textWinner = '~%s' % self.correctedText(self.WinResultMin, self.WinResult, outcomeCredits)
            textDefeat = '~%s' % self.correctedText(self.DefeatResultMin, self.DefeatResult, outcomeCredits)
            textWinnerPremium = ''
            textDefeatPremium = ''
            if BattleReplay.g_replayCtrl.isPlaying:
                textWinnerPremium = ', With Premium account: ~%s Credits' % self.correctedText(int(1.5 * self.WinResultMin), int(1.5 * self.WinResult), outcomeCredits)
                textDefeatPremium = ', With Premium account: ~%s Credits' % self.correctedText(int(1.5 * self.DefeatResultMin), int(1.5 * self.DefeatResult), outcomeCredits)
            price = self.hangarOutcome
            for equipment in self.usedItems:
                if self.usedItems[equipment][0]:
                    price += self.usedItems[equipment][1]
            for ammo in self.hangarAmmo:
                if self.hangarAmmo[ammo][1]:
                    price += self.hangarAmmo[ammo][0] * self.hangarAmmo[ammo][1]
            consumables = int(round(price))
            print('#' * 40)
            print('Credits Calculate mode')
            print('VEHICLE: %s level:%s (id:%s)' % (self.tempResults[self.compactDescr]['name'], self.tempResults[self.compactDescr]['level'], self.compactDescr))
            print('damage:%s, assist:%s, spot:%s, %s' % (self.tempResults[self.compactDescr]['damage'], self.tempResults[self.compactDescr]['assist'], self.tempResults[self.compactDescr]['spot'], 'clear repaired' if self.tempResults[self.compactDescr]['clearRepair'] else 'not cleared repair'))
            print('damage detail: selfSpot:%s, unkwnSpot:%s, othrSpot:%s, forStunned:%s, ' % (self.DAMAGE_SELF_SPOT, self.DAMAGE_UNKNOWN_SPOT, self.DAMAGE_OTHER_SPOT, self.DAMAGE_STUN))
            print('coeff:%s, premCoeff:%s' % (self.balanceCoeff, self.tempResults[self.compactDescr]['premium']))
            print('repairCost:%s[%s], consumables:%s' % (-int(round(self.repairCost * self.balanceCoeff)), -self.repairCost, -consumables))
            # Print ammo costs
            amm0 = ''
            for ammo in self.hangarAmmo:
                amm0 += '%s Credits (%s * %s) ' % (self.hangarAmmo[ammo][0] * self.hangarAmmo[ammo][1], self.hangarAmmo[ammo][0], self.hangarAmmo[ammo][1])
            if amm0:
                print ('Ammo: %s' % amm0)
            # Print final results
            print('WINNER:%s Credits' % textWinner + textWinnerPremium)
            print('DEFEAT:%s Credits' % textDefeat + textDefeatPremium)
            print('#' * 40)
            print(self.getDebugText())

    def _resetAfterBattle(self):
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
            self.recalculatedMessage = '<font size=\"20\" color=\"#FFE041\">%s</font>\n' % self.hangarHeader
            if self.textWin or self.textDEFEAT:
                textWinner = self.correctedText(self.WinResultMin, self.WinResult, 0)
                textDefeat = self.correctedText(self.DefeatResult, self.DefeatResult, 0)
                colorWin = '#80D639'
                colorDefeat = '#FF6347'
                self.textWin = '<font size=\"20\" color=\"%s\">~%s%s</font>' % (colorWin, self.iconCredits, textWinner)
                self.textDEFEAT = '<font size=\"20\" color=\"%s\">~%s%s</font>' % (
                colorDefeat, self.iconCredits, textDefeat)
                self.recalculatedMessage += '  ' + self.textWin + '<font size=\"20\" color=\"#FFE041\"> %s </font>' % self.vehicleName + self.textDEFEAT
            self.timerMessage()

    def timerMessage(self):
        if not config.data['hangarShow']:
            return
        if g_currentVehicle.item:
            flashInHangar.setPosition(config.data['hangar_x'], config.data['hangar_y'])
            flashInHangar.setBackground(config.data['battleBackground'], '#000000', 0.4)
            flashInHangar.setText(self.recalculatedMessage)
            return
        callback(1.0, self.timerMessage)

    @staticmethod
    def tester(credits, premiumCoEff, winCoEff, level, assist, spot):
        result = []
        winCoEff = 1300 if winCoEff else 700
        base_value = int(level * winCoEff + assist * 5 + spot * 100)
        pool = {1: (99, 0.1), 2: (999, 0.01), 3: (9999, 0.001), 4: (99999, 0.0001), 5: (999999, 0.00001),}
        for precision, (iterations, increment) in pool.iteritems():
            boosterCoEff = 0.0
            for _ in xrange(iterations):
                boosterCoEff = round(boosterCoEff + increment, precision)
                calculated_value = int(int(boosterCoEff * base_value - 0.5) * premiumCoEff + 0.5)
                if credits == calculated_value:
                    result.append(boosterCoEff)
            if result:
                if 'DEBUG' in globals() and DEBUG:
                    print('search pool: %s' % precision, (iterations, increment), boosterCoEff)
                return result
        return result

    def sortValues(self, value, debug=False):
        try:
            index = self.coeffDefaults.index(filter(lambda x: value <= x + 0.0005, self.coeffDefaults)[0])
            if DEBUG or debug:
                print('sortValues value: %s=>[%s]<%s' % (self.coeffDefaults[index], value, self.coeffDefaults[index + 1] if len(self.coeffDefaults) > index + 1 else self.coeffDefaults[index]))
            return self.coeffDefaults[index]
        except Exception as e:
            if DEBUG or debug:
                print('sortValues error not in range: %s %s' % value, e)
            return value

    def sortResult(self, data1, data2, testCoEff):
        if data1 and data2:
            check1 = self.sortValues(round(sum(data1) / len(data1), 5), DEBUG_COEFF)
            check2 = self.sortValues(round(sum(data2) / len(data2), 5), DEBUG_COEFF)
            if check1 == testCoEff or check2 == testCoEff:
                return testCoEff
            if check1 == check2:
                return check1
            if check1 in data2:
                return check1
            if check2 in data1:
                return check2
        return 0.0

    def resultReCalc(self, typeCompDescr, isWin, credits, originalCredits, spot, assist, damage, *_, **__):
        if DEBUG or DEBUG_COEFF:
            print('$$$$$ resultReCalc started')
        self.readJson()
        vehicleCompDesc, testCoEff = self.deCode(typeCompDescr)
        if vehicleCompDesc not in self.tempResults:
            return
        if not damage:
            self._calcModeNoDamage(typeCompDescr, vehicleCompDesc, testCoEff, isWin, credits, originalCredits, spot, assist)

    def _calcModeNoDamage(self, typeCompDescr, vehicleCompDesc, testCoEff, isWin, credits, originalCredits, spot, assist):
        if DEBUG or DEBUG_COEFF:
            print('$$$$$$$$$$$$$$ NO DAMAGE MODE $$$$$$$$$$$$$$')
        if originalCredits == 0:
            if DEBUG:
                print('$$$$ originalCredits is zero! Impossible calc $$$$')
            return
        checkCorrectedBattleData = credits / float(originalCredits)
        if DEBUG and checkCorrectedBattleData != 1.5:
            print('$$$$ BATTLE DATA INCORRECT! PLAY AGAIN $$$$')
        premiumCoEff = 1.0 if checkCorrectedBattleData < 1.01 else 1.5
        winCoEff = 1300 if isWin else 700
        level = self.tempResults[vehicleCompDesc]['level']
        result1 = self.tester(originalCredits, 1.0, isWin, level, assist, spot)
        result2 = self.tester(credits, 1.5, isWin, level, assist, spot)
        checkData = int(int(1.0 * int(level * winCoEff + assist * 5 + spot * 100) - 0.5) * premiumCoEff + 0.5)
        if checkData == 0 or originalCredits == 0:
            if DEBUG:
                print('$$$$ checkData or originalCredits is zero! $$$$')
            coEff1 = 1.0
        else:
            if premiumCoEff > 1.1:
                coEff1 = round(float(checkData) / originalCredits, 4)
            else:
                coEff1 = round(float(originalCredits) / checkData, 4)
        check = self.sortResult(result1, result2, coEff1)
        checkOne = check
        self._printDebugInfo(vehicleCompDesc, level, assist, spot, winCoEff, testCoEff, credits, originalCredits, checkData, checkCorrectedBattleData, check, coEff1, result1, result2, checkOne)
        checkData *= premiumCoEff
        if checkData == 0:
            if DEBUG:
                print('$$$$ checkData * premiumCoEff is zero! $$$$')
            coEff2 = coEff1
        else:
            coEff2 = round(float(credits) / checkData, 4)
        checkAgain = self.sortResult(result1, result2, coEff2)
        if checkAgain and check != checkAgain:
            check = checkAgain
        if DEBUG:
            print('#### resultReCalc coEff2[%s] and coEff1[%s] and check[%s]' % (coEff2, coEff1, check))
        self._saveCalculatedResults(typeCompDescr, vehicleCompDesc, coEff1, coEff2, check, testCoEff)

    def _printDebugInfo(self, vehicleCompDesc, level, assist, spot, winCoEff, testCoEff, credits, originalCredits, checkData, checkCorrectedBattleData, check, coEff1, result1, result2, checkOne):
        if DEBUG:
            print('VEHICLE: %s level:%s (id:%s)' % (self.tempResults[vehicleCompDesc]['name'], self.tempResults[vehicleCompDesc]['level'], vehicleCompDesc))
            print('level:%s, assist:%s, spot:%s, winCoEff:%s, balanceCoEff:%s' % (
            level, assist, spot, winCoEff, testCoEff))
            print('credits:%s originalCredits:%s, checkData:%s' % (credits, originalCredits, checkData))
            print('credits / originalCredits = %s' % checkCorrectedBattleData)
            print('possible coEffs:', check)
            print('#### resultReCalc coEff1[%s] and testCoEff[%s]' % (coEff1, testCoEff))
            print('result1 = ', result1)
            if result1 and len(result1) > 0:
                print('result1 coEff = %s' % round(sum(result1) / len(result1), 4))
            print('result2 = ', result2)
            if result2 and len(result2) > 0:
                print('result2 coEff = %s' % round(sum(result2) / len(result2), 4))
        if DEBUG_COEFF:
            if result1 and len(result1) > 0:
                print('$$$$ 1 round coEff:%s' % round(sum(result1) / len(result1), 4), result1)
            if result2 and len(result2) > 0:
                print('$$$$ 2 round coEff:%s' % round(sum(result2) / len(result2), 4), result2)
            print('$$$$ VEHICLE: %s level:%s (id:%s)' % (self.tempResults[vehicleCompDesc]['name'], self.tempResults[vehicleCompDesc]['level'], vehicleCompDesc))
            print('$$$$ originalCoEff: %s, possibleCoEff1: %s, possibleCoEff2: %s' % (testCoEff, checkOne, check))

    def _saveCalculatedResults(self, typeCompDescr, vehicleCompDesc, coEff1, coEff2, check, testCoEff):
        if coEff1 == coEff2 and coEff1 != 1.0:
            if DEBUG or DEBUG_COEFF:
                print('####1 resultReCalc SAVED coEff[%s] ' % coEff2)
            self.compactDescr, self.balanceCoeff = self.code(typeCompDescr, coEff2)
            self.readJson()
            if DEBUG or DEBUG_COEFF:
                print("####1 '%s': %s," % (self.compactDescr, self.balanceCoeff))
        elif check:
            if DEBUG or DEBUG_COEFF:
                print('####2 resultReCalc SAVED coEff[%s]' % check)
            self.compactDescr, self.balanceCoeff = self.code(typeCompDescr, check)
            self.readJson()
            if DEBUG or DEBUG_COEFF:
                print("####2 '%s': %s," % (self.compactDescr, self.balanceCoeff))
        if DEBUG or DEBUG_COEFF:
            self._showResultMessage(vehicleCompDesc, check, testCoEff)

    def _showResultMessage(self, vehicleCompDesc, check, testCoEff):
        self.recalculatedMessage = '<font size=\"20\" color=\"#FFE041\">Credits Calc to %s (id:%s)\nNew coEff:%s assigned, %s to %s</font>\n' % (self.tempResults[vehicleCompDesc]['name'], self.compactDescr, check, testCoEff, check)
        try:
            import BigWorld
            BigWorld.callback(1.0, self.timerMessage)
        except ImportError:
            print("Error: BigWorld not available for callback")

    def receiveBattleResult(self, _, battleResults):
        playerVehicles = battleResults['personal'].itervalues().next()
        if not playerVehicles:
            return
        assist = max(playerVehicles['damageAssistedRadio'], playerVehicles['damageAssistedTrack'], playerVehicles['damageAssistedStun'])
        spot = playerVehicles['spotted']
        damage = playerVehicles['damageDealt']
        repair = playerVehicles['repair']
        self.resultReCalc(playerVehicles['typeCompDescr'], battleResults['common']['winnerTeam'] == playerVehicles['team'], playerVehicles['factualCredits'], playerVehicles['originalCredits'], spot, assist, damage, repair)

    def _initializeCoefficients(self):
        tanks_data = [
            {'id': '161', 'coefficient': 1.4},
            {'id': '417', 'coefficient': 1.1},
            {'id': '673', 'coefficient': 1.15},
            {'id': '929', 'coefficient': 1.1},
            {'id': '1185', 'coefficient': 1.0},
            {'id': '1441', 'coefficient': 1.0},
            {'id': '1697', 'coefficient': 0.9},
            {'id': '1953', 'coefficient': 0.8},
            {'id': '2209', 'coefficient': 0.7},
            {'id': '51361', 'coefficient': 1.5},
            {'id': '2465', 'coefficient': 0.72},
            {'id': '2721', 'coefficient': 0.73},
            {'id': '3745', 'coefficient': 0.708},
            {'id': '2977', 'coefficient': 1.05},
            {'id': '129', 'coefficient': 1.4},
            {'id': '51841', 'coefficient': 1.2},
            {'id': '385', 'coefficient': 1.102},
            {'id': '641', 'coefficient': 1.05},
            {'id': '897', 'coefficient': 1.05},
            {'id': '1153', 'coefficient': 1.1},
            {'id': '51585', 'coefficient': 1.2},
            {'id': '1409', 'coefficient': 0.9},
            {'id': '1665', 'coefficient': 0.8},
            {'id': '4993', 'coefficient': 0.7},
            {'id': '52609', 'coefficient': 1.6},
            {'id': '52353', 'coefficient': 1.6},
            {'id': '53121', 'coefficient': 1.5},
            {'id': '5249', 'coefficient': 0.72},
            {'id': '5505', 'coefficient': 0.73},
            {'id': '1169', 'coefficient': 1.419},
            {'id': '1425', 'coefficient': 1.1},
            {'id': '401', 'coefficient': 1.3},
            {'id': '1681', 'coefficient': 1.1},
            {'id': '1937', 'coefficient': 1.018},
            {'id': '2193', 'coefficient': 1.0044},
            {'id': '2449', 'coefficient': 0.9},
            {'id': '145', 'coefficient': 1.25},
            {'id': '51345', 'coefficient': 1.25},
            {'id': '2705', 'coefficient': 0.858},
            {'id': '913', 'coefficient': 1.5},
            {'id': '2961', 'coefficient': 0.791},
            {'id': '3217', 'coefficient': 0.73},
            {'id': '3473', 'coefficient': 0.71},
            {'id': '609', 'coefficient': 1.3},
            {'id': '3169', 'coefficient': 1.2996},
            {'id': '865', 'coefficient': 1.1},
            {'id': '2401', 'coefficient': 1.1},
            {'id': '2145', 'coefficient': 1.1},
            {'id': '2913', 'coefficient': 1.2},
            {'id': '353', 'coefficient': 1.2},
            {'id': '5985', 'coefficient': 1.1},
            {'id': '1633', 'coefficient': 1.1},
            {'id': '1377', 'coefficient': 1.0},
            {'id': '51553', 'coefficient': 1.5},
            {'id': '1889', 'coefficient': 0.85},
            {'id': '1121', 'coefficient': 0.77},
            {'id': '52065', 'coefficient': 1.5},
            {'id': '52833', 'coefficient': 1.5},
            {'id': '2657', 'coefficient': 0.69},
            {'id': '3425', 'coefficient': 0.75},
            {'id': '3681', 'coefficient': 0.73},
            {'id': '4705', 'coefficient': 1.05},
            {'id': '4449', 'coefficient': 1.05},
            {'id': '5729', 'coefficient': 1.05},
            {'id': '52321', 'coefficient': 1.2},
            {'id': '5473', 'coefficient': 0.9},
            {'id': '5217', 'coefficient': 0.83},
            {'id': '4961', 'coefficient': 0.8},
            {'id': '52577', 'coefficient': 1.5},
            {'id': '4193', 'coefficient': 0.71},
            {'id': '3937', 'coefficient': 0.73},
            {'id': '1329', 'coefficient': 1.419},
            {'id': '2353', 'coefficient': 1.128},
            {'id': '4401', 'coefficient': 1.0074},
            {'id': '3121', 'coefficient': 1.0336},
            {'id': '4913', 'coefficient': 0.925},
            {'id': '64817', 'coefficient': 1.35},
            {'id': '3377', 'coefficient': 0.78},
            {'id': '305', 'coefficient': 1.4},
            {'id': '3889', 'coefficient': 0.6745},
            {'id': '62001', 'coefficient': 1.5},
            {'id': '5681', 'coefficient': 0.67},
            {'id': '5937', 'coefficient': 0.66},
            {'id': '4657', 'coefficient': 1.11},
            {'id': '5169', 'coefficient': 0.909},
            {'id': '1073', 'coefficient': 0.78},
            {'id': '64049', 'coefficient': 1.575},
            {'id': '49', 'coefficient': 1.575},
            {'id': '561', 'coefficient': 1.575},
            {'id': '63793', 'coefficient': 1.5},
            {'id': '1585', 'coefficient': 0.708},
            {'id': '1841', 'coefficient': 0.71},
            {'id': '63537', 'coefficient': 0.73},
            {'id': '4145', 'coefficient': 0.73},
            {'id': '3633', 'coefficient': 0.874},
            {'id': '65073', 'coefficient': 1.575},
            {'id': '2865', 'coefficient': 0.782},
            {'id': '817', 'coefficient': 1.575},
            {'id': '64561', 'coefficient': 1.55},
            {'id': '2097', 'coefficient': 0.7},
            {'id': '5425', 'coefficient': 0.774},
            {'id': '6193', 'coefficient': 0.77},
            {'id': '113', 'coefficient': 1.4},
            {'id': '369', 'coefficient': 1.1},
            {'id': '625', 'coefficient': 1.05},
            {'id': '881', 'coefficient': 1.0},
            {'id': '1137', 'coefficient': 1.0},
            {'id': '51569', 'coefficient': 1.3},
            {'id': '1393', 'coefficient': 0.9},
            {'id': '1649', 'coefficient': 0.77},
            {'id': '1905', 'coefficient': 0.72},
            {'id': '51825', 'coefficient': 1.5},
            {'id': '2161', 'coefficient': 0.71},
            {'id': '2417', 'coefficient': 0.73},
            {'id': '5201', 'coefficient': 1.199},
            {'id': '593', 'coefficient': 1.1},
            {'id': '54865', 'coefficient': 1.2996},
            {'id': '6993', 'coefficient': 1.089},
            {'id': '4945', 'coefficient': 1.026},
            {'id': '1361', 'coefficient': 1.0},
            {'id': '7761', 'coefficient': 1.09},
            {'id': '7505', 'coefficient': 1.089},
            {'id': '6481', 'coefficient': 1.077},
            {'id': '2129', 'coefficient': 1.057},
            {'id': '59729', 'coefficient': 0.7799},
            {'id': '59473', 'coefficient': 0.68},
            {'id': '58449', 'coefficient': 1.5},
            {'id': '58705', 'coefficient': 0.6701},
            {'id': '58961', 'coefficient': 0.66},
            {'id': '81', 'coefficient': 1.637},
            {'id': '337', 'coefficient': 1.253},
            {'id': '2385', 'coefficient': 1.089},
            {'id': '849', 'coefficient': 1.026},
            {'id': '52817', 'coefficient': 1.26},
            {'id': '1617', 'coefficient': 1.0},
            {'id': '12881', 'coefficient': 1.0},
            {'id': '53585', 'coefficient': 1.53},
            {'id': '57169', 'coefficient': 1.3},
            {'id': '56145', 'coefficient': 1.22},
            {'id': '1105', 'coefficient': 0.932},
            {'id': '55889', 'coefficient': 1.25},
            {'id': '3665', 'coefficient': 0.85},
            {'id': '5457', 'coefficient': 0.77},
            {'id': '56913', 'coefficient': 1.5},
            {'id': '15441', 'coefficient': 1.55},
            {'id': '5969', 'coefficient': 0.825},
            {'id': '55633', 'coefficient': 1.6},
            {'id': '5713', 'coefficient': 0.73},
            {'id': '7249', 'coefficient': 0.73},
            {'id': '14929', 'coefficient': 0.73},
            {'id': '54353', 'coefficient': 1.4},
            {'id': '2897', 'coefficient': 1.115},
            {'id': '53841', 'coefficient': 1.38},
            {'id': '4689', 'coefficient': 0.98},
            {'id': '3153', 'coefficient': 0.836},
            {'id': '55121', 'coefficient': 1.3},
            {'id': '56657', 'coefficient': 1.5},
            {'id': '3921', 'coefficient': 0.825},
            {'id': '4433', 'coefficient': 0.752},
            {'id': '15697', 'coefficient': 0.745},
            {'id': '6225', 'coefficient': 0.745},
            {'id': '57937', 'coefficient': 0.73},
            {'id': '15185', 'coefficient': 0.73},
            {'id': '8273', 'coefficient': 1.1},
            {'id': '8017', 'coefficient': 0.9},
            {'id': '9041', 'coefficient': 0.945},
            {'id': '13393', 'coefficient': 0.95},
            {'id': '8785', 'coefficient': 0.997},
            {'id': '9553', 'coefficient': 0.9},
            {'id': '57681', 'coefficient': 1.43},
            {'id': '14417', 'coefficient': 0.9},
            {'id': '9809', 'coefficient': 1.012},
            {'id': '54097', 'coefficient': 1.38},
            {'id': '10065', 'coefficient': 0.795},
            {'id': '14161', 'coefficient': 0.75},
            {'id': '59985', 'coefficient': 1.5},
            {'id': '8529', 'coefficient': 0.724},
            {'id': '14673', 'coefficient': 0.71},
            {'id': '13137', 'coefficient': 0.65},
            {'id': '52561', 'coefficient': 0.715},
            {'id': '9297', 'coefficient': 0.583},
            {'id': '13905', 'coefficient': 0.6},
            {'id': '15953', 'coefficient': 0.583},
            {'id': '833', 'coefficient': 1.15},
            {'id': '3393', 'coefficient': 1.08},
            {'id': '14657', 'coefficient': 1.086},
            {'id': '4161', 'coefficient': 1.104},
            {'id': '2113', 'coefficient': 1.35},
            {'id': '4673', 'coefficient': 1.122},
            {'id': '28225', 'coefficient': 1.5},
            {'id': '7233', 'coefficient': 0.9},
            {'id': '7489', 'coefficient': 0.71},
            {'id': '14401', 'coefficient': 0.64},
            {'id': '11841', 'coefficient': 0.78},
            {'id': '577', 'coefficient': 1.63},
            {'id': '43329', 'coefficient': 1.2},
            {'id': '15169', 'coefficient': 1.1},
            {'id': '1601', 'coefficient': 1.276},
            {'id': '15937', 'coefficient': 1.1},
            {'id': '1345', 'coefficient': 1.219},
            {'id': '43841', 'coefficient': 1.09},
            {'id': '5953', 'coefficient': 1.113},
            {'id': '2881', 'coefficient': 1.046},
            {'id': '14145', 'coefficient': 1.0},
            {'id': '17985', 'coefficient': 0.87},
            {'id': '6465', 'coefficient': 0.873},
            {'id': '5185', 'coefficient': 0.824},
            {'id': '63297', 'coefficient': 1.3998},
            {'id': '18241', 'coefficient': 0.7799},
            {'id': '63809', 'coefficient': 1.4},
            {'id': '43585', 'coefficient': 1.5},
            {'id': '17473', 'coefficient': 0.68},
            {'id': '18497', 'coefficient': 0.68},
            {'id': '61505', 'coefficient': 1.5},
            {'id': '4929', 'coefficient': 0.67},
            {'id': '18753', 'coefficient': 0.6701},
            {'id': '17217', 'coefficient': 0.66},
            {'id': '19009', 'coefficient': 0.66},
            {'id': '13121', 'coefficient': 1.0},
            {'id': '321', 'coefficient': 1.025},
            {'id': '14913', 'coefficient': 1.0},
            {'id': '4417', 'coefficient': 1.05},
            {'id': '60737', 'coefficient': 1.25},
            {'id': '63553', 'coefficient': 1.5},
            {'id': '63041', 'coefficient': 1.5},
            {'id': '62529', 'coefficient': 1.6},
            {'id': '5697', 'coefficient': 0.817},
            {'id': '15681', 'coefficient': 0.75},
            {'id': '15425', 'coefficient': 0.73},
            {'id': '3649', 'coefficient': 0.75},
            {'id': '1089', 'coefficient': 1.08},
            {'id': '6721', 'coefficient': 1.08},
            {'id': '2625', 'coefficient': 0.906},
            {'id': '6977', 'coefficient': 0.795},
            {'id': '62273', 'coefficient': 1.5},
            {'id': '16449', 'coefficient': 0.8},
            {'id': '62017', 'coefficient': 1.6},
            {'id': '64065', 'coefficient': 1.445},
            {'id': '3137', 'coefficient': 0.793},
            {'id': '62785', 'coefficient': 1.6},
            {'id': '3905', 'coefficient': 0.702},
            {'id': '16705', 'coefficient': 0.72},
            {'id': '6209', 'coefficient': 0.75},
            {'id': '16961', 'coefficient': 0.71},
            {'id': '3601', 'coefficient': 0.987},
            {'id': '6673', 'coefficient': 0.915},
            {'id': '17937', 'coefficient': 0.85},
            {'id': '1809', 'coefficient': 0.9125},
            {'id': '11281', 'coefficient': 0.85},
            {'id': '1041', 'coefficient': 1.0044},
            {'id': '60689', 'coefficient': 1.5},
            {'id': '16145', 'coefficient': 0.95},
            {'id': '57105', 'coefficient': 1.35},
            {'id': '1553', 'coefficient': 0.98},
            {'id': '11793', 'coefficient': 0.95},
            {'id': '15121', 'coefficient': 1.33},
            {'id': '2833', 'coefficient': 1.18},
            {'id': '5905', 'coefficient': 1.08},
            {'id': '4625', 'coefficient': 1.18},
            {'id': '15633', 'coefficient': 1.03},
            {'id': '5649', 'coefficient': 1.12},
            {'id': '273', 'coefficient': 1.17},
            {'id': '8977', 'coefficient': 0.85},
            {'id': '15377', 'coefficient': 0.78},
            {'id': '8721', 'coefficient': 0.7},
            {'id': '9233', 'coefficient': 0.82},
            {'id': '3329', 'coefficient': 0.918},
            {'id': '1025', 'coefficient': 0.95},
            {'id': '41473', 'coefficient': 1.75},
            {'id': '15361', 'coefficient': 0.82},
            {'id': '4609', 'coefficient': 0.892},
            {'id': '54529', 'coefficient': 1.09},
            {'id': '52737', 'coefficient': 1.6},
            {'id': '60929', 'coefficient': 1.3},
            {'id': '15105', 'coefficient': 0.85},
            {'id': '3073', 'coefficient': 0.836},
            {'id': '53505', 'coefficient': 1.3145},
            {'id': '52225', 'coefficient': 1.3},
            {'id': '769', 'coefficient': 0.975},
            {'id': '52481', 'coefficient': 1.575},
            {'id': '15873', 'coefficient': 1.02},
            {'id': '9729', 'coefficient': 1.4},
            {'id': '9473', 'coefficient': 0.964},
            {'id': '16641', 'coefficient': 0.83},
            {'id': '19457', 'coefficient': 0.78},
            {'id': '45569', 'coefficient': 1.5},
            {'id': '18433', 'coefficient': 0.68},
            {'id': '18177', 'coefficient': 0.67},
            {'id': '19201', 'coefficient': 0.66},
            {'id': '47873', 'coefficient': 1.3},
            {'id': '33281', 'coefficient': 1.5},
            {'id': '52993', 'coefficient': 1.437},
            {'id': '1537', 'coefficient': 0.997},
            {'id': '61441', 'coefficient': 1.52},
            {'id': '1', 'coefficient': 1.094},
            {'id': '34305', 'coefficient': 1.48},
            {'id': '51457', 'coefficient': 1.5},
            {'id': '47105', 'coefficient': 1.45},
            {'id': '58113', 'coefficient': 1.22},
            {'id': '12289', 'coefficient': 0.83},
            {'id': '2561', 'coefficient': 0.906},
            {'id': '59393', 'coefficient': 1.25},
            {'id': '57089', 'coefficient': 1.25},
            {'id': '35073', 'coefficient': 1.5},
            {'id': '8961', 'coefficient': 0.928},
            {'id': '6657', 'coefficient': 0.858},
            {'id': '12545', 'coefficient': 0.77},
            {'id': '32257', 'coefficient': 1.5},
            {'id': '48897', 'coefficient': 1.5},
            {'id': '13313', 'coefficient': 0.67},
            {'id': '47617', 'coefficient': 1.5},
            {'id': '59905', 'coefficient': 1.5},
            {'id': '61953', 'coefficient': 1.5},
            {'id': '46337', 'coefficient': 1.5},
            {'id': '62977', 'coefficient': 1.5},
            {'id': '47361', 'coefficient': 1.5},
            {'id': '46081', 'coefficient': 1.5},
            {'id': '4353', 'coefficient': 0.802},
            {'id': '17665', 'coefficient': 0.75},
            {'id': '7937', 'coefficient': 0.82},
            {'id': '33793', 'coefficient': 1.52},
            {'id': '15617', 'coefficient': 0.73},
            {'id': '21761', 'coefficient': 0.73},
            {'id': '34049', 'coefficient': 1.5},
            {'id': '17153', 'coefficient': 0.73},
            {'id': '13825', 'coefficient': 0.78},
            {'id': '16897', 'coefficient': 0.82},
            {'id': '19969', 'coefficient': 0.73},
            {'id': '54017', 'coefficient': 1.4734},
            {'id': '33025', 'coefficient': 1.3},
            {'id': '51713', 'coefficient': 1.575},
            {'id': '11777', 'coefficient': 1.0},
            {'id': '18689', 'coefficient': 0.912},
            {'id': '11265', 'coefficient': 0.922},
            {'id': '2817', 'coefficient': 0.583},
            {'id': '10497', 'coefficient': 0.868},
            {'id': '49921', 'coefficient': 1.5},
            {'id': '59137', 'coefficient': 1.35},
            {'id': '46593', 'coefficient': 1.35},
            {'id': '5889', 'coefficient': 0.894},
            {'id': '513', 'coefficient': 0.935},
            {'id': '9217', 'coefficient': 1.5},
            {'id': '63233', 'coefficient': 1.5},
            {'id': '48641', 'coefficient': 1.5},
            {'id': '49665', 'coefficient': 1.5},
            {'id': '20481', 'coefficient': 0.8},
            {'id': '58881', 'coefficient': 1.5},
            {'id': '11009', 'coefficient': 0.922},
            {'id': '44289', 'coefficient': 1.5},
            {'id': '62721', 'coefficient': 1.5},
            {'id': '53249', 'coefficient': 1.5},
            {'id': '5377', 'coefficient': 0.797},
            {'id': '60417', 'coefficient': 1.5},
            {'id': '19713', 'coefficient': 0.77},
            {'id': '20737', 'coefficient': 0.77},
            {'id': '10753', 'coefficient': 0.756},
            {'id': '11521', 'coefficient': 0.777},
            {'id': '6145', 'coefficient': 0.783},
            {'id': '7169', 'coefficient': 0.788},
            {'id': '32001', 'coefficient': 1.5},
            {'id': '20225', 'coefficient': 0.63},
            {'id': '13569', 'coefficient': 0.605},
            {'id': '3841', 'coefficient': 0.98},
            {'id': '7681', 'coefficient': 0.964},
            {'id': '4865', 'coefficient': 1.044},
            {'id': '16385', 'coefficient': 1.12},
            {'id': '5633', 'coefficient': 1.0},
            {'id': '16129', 'coefficient': 0.945},
            {'id': '1793', 'coefficient': 0.935},
            {'id': '4097', 'coefficient': 0.78},
            {'id': '8449', 'coefficient': 0.68},
            {'id': '8705', 'coefficient': 0.76},
        ]
        for tank in tanks_data:
            self.add_coefficient(tank['id'], tank['coefficient'])

    def add_coefficient(self, tankID, coefficient):
        self._coefficients[tankID] = coefficient


class Flash(object):
    def startBattle(self):
        if not config.data['battleShow']:
            return
        if not g_guiFlash:
            return
        g_guiFlash.createComponent('credits', COMPONENT_TYPE.PANEL, {
            'x'     : config.data['battle_x'],
            'y'     : config.data['battle_y'],
            'width' : 1,
            'height': 1,
            'drag'  : True,
            'border': True,
            'alignX': COMPONENT_ALIGN.LEFT,
            'alignY': COMPONENT_ALIGN.BOTTOM})

        g_guiFlash.createComponent('credits.text', COMPONENT_TYPE.LABEL, {
            'shadow': {"distance": 0, "angle": 0, "color": 0x000000, "alpha": 1, "blurX": 1, "blurY": 1, "strength": 1, "quality": 1},
            'text'  : '',
            'width': 168,
            'height': 25,
            'index': 1,
            'multiline': True,
            'tooltip': '+1000 or -1000 it\'s normal calc\nIf calc incorrect, play battle without damage to fix it.\nFull time replays, no escape!!!'})
        if config.data['battleBackground']:
            g_guiFlash.createComponent('credits.image', COMPONENT_TYPE.IMAGE, {'width': 168, 'height': 25, 'index': 0, 'image': '../maps/icons/quests/inBattleHint.png'})
        COMPONENT_EVENT.UPDATED += self.update

    def stopBattle(self):
        if not config.data['battleShow']:
            return
        if not g_guiFlash:
            return
        COMPONENT_EVENT.UPDATED -= self.update
        g_guiFlash.deleteComponent('credits.text')
        if config.data['battleBackground']:
            g_guiFlash.deleteComponent('credits.image')
        g_guiFlash.deleteComponent('credits')

    @staticmethod
    def update(alias, props):
        if not config.data['battleShow']:
            return
        if str(alias) == str('credits'):
            x = int(props.get('x', config.data['battle_x']))
            if x and x != int(config.data['battle_x']):
                config.data['battle_x'] = x
            y = int(props.get('y', config.data['battle_y']))
            if y and y != int(config.data['battle_y']):
                config.data['battle_y'] = y
            config.onApplySettings({'battle_x': x, 'battle_y': y})

    @staticmethod
    def setCreditsText(text, width=0, height=0):
        if not config.data['battleShow']:
            return
        if not g_guiFlash:
            return
        data = {'visible': True, 'text': text}
        if width:
            data['width'] = width
        if height:
            data['width'] = height
        g_guiFlash.updateComponent('credits.text', data)

    @staticmethod
    def visible(status):
        if not config.data['battleShow']:
            return
        g_guiFlash.updateComponent('credits', {'visible': status})


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
            if ArenaUniqueID in self.ResultsCache: return
            calc.receiveBattleResult(True, battleResults)

    def WaitResult(self):
        while self.Threads:
            ArenaUniqueID = self.ArenaIDQueue.get()
            self.ResultsAvailable.wait()
            try:
                getPlayer().battleResultsCache.get(ArenaUniqueID, partial(self.CheckCallback, ArenaUniqueID))
            except StandardError:
                pass


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)
flashInHangar = FlashInHangar()
flash = Flash()
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
def new_updateWidgetModel(func, self):
    result = func(self)
    if g_currentVehicle.item:
        try:
            status = g_currentVehicle.itemsCache.items.stats.activePremiumExpiryTime > 0
        except StandardError:
            status = False
        try:
            calc.getHangarData(status)
        except Exception as e:
            print('ERROR: creditCalc crew:', e)
    return result


@override(PlayerAvatar, 'onBattleEvents')
def new__onBattleEvents(func, self, events):
    func(self, events)
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        calc.onBattleEvents(events)


@override(LobbyView, '_populate')
def new__populate(func, self):
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


g_playerEvents.onBattleResultsReceived += calc.receiveBattleResult
g_playerEvents.onAvatarReady += IntoBattle
g_playerEvents.onAccountBecomePlayer += onAccountBecomePlayer


def fini():
    results.Threads = False


def jsonGenerator(nations=None, onlyNew=False):
    COEFFICIENTS = {}
    version_paths = ['../version.xml', 'version.xml', './version.xml']
    resMgr = None
    for path in version_paths:
        resMgr = ResMgr.openSection(path)
        if resMgr is not None:
            break
    ver = 'temp' if resMgr is None else resMgr.readString('version')
    i1 = ver.find('.')
    i2 = ver.find('#')
    if i1 >= 0 and i2 >= 0:
        version_segment = ver[i1 + 1:i2 - 1]
        PATH = './res_mods/{}/system/'.format(version_segment)
    else:
        PATH = './res_mods/system/'
    json_path = PATH + 'sw_templates.json'
    if os.path.isfile(json_path):
        try:
            with codecs.open(json_path, 'r', encoding='utf-8-sig') as json_file:
                data = json_file.read().decode('utf-8-sig')
                COEFFICIENTS.update(calc.byte_ify(json.loads(data)))
        except Exception as e:
            print("# Error load coefficients: {}".format(e))

    def deCode(compactDescr):
        test = str(compactDescr)
        if test in COEFFICIENTS:
            return test, round(COEFFICIENTS[test], 6)
        return test, 0.0
    items = g_currentVehicle.itemsCache.items.getVehicles()

    def getData(_nation, _role):
        text = []
        has_vehicles = False
        for level in xrange(1, 11):
            for compactDescr in items:
                vehicle = items[compactDescr]
                if (vehicle.nationName == _nation and
                        vehicle.descriptor.level == level and
                        vehicle.type == _role):
                    vehicleCompDesc, balanceCoeff = deCode(compactDescr)
                    premium_flag = ' !!!!PREMIUM' if (vehicle.isPremium or vehicle.isPremiumIGR) else ''
                    details = '#lvl:{} {} {}'.format( vehicle.descriptor.level, vehicle.name.replace(':', '_'), premium_flag)
                    if not balanceCoeff:
                        text.append("#'{}': {}, {} https://premomer.org/tank.php?id={}".format(compactDescr, None, details, compactDescr))
                        has_vehicles = True
                    elif not onlyNew:
                        text.append("'{}': {}, {}".format(compactDescr, balanceCoeff, details))
                        has_vehicles = True
        if has_vehicles:
            print('# {}'.format(_role))
        if text:
            print('\n'.join(text))
    if not nations:
        nations = ['ussr', 'germany', 'uk', 'japan', 'usa', 'china', 'france', 'czech', 'sweden', 'poland', 'italy']
    roles = ['lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG']
    print('########################### DATA ###########################')
    for nation in nations:
        print('# {}'.format(nation))
        for role in roles:
            getData(nation, role)
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!! DONE !!!!!!!!!!!!!!!!!!!!!!!!!!!')
