# -*- coding: utf-8 -*-
import os
import traceback

from Avatar import PlayerAvatar
from gui.Scaleform.daapi.view.battle.shared.minimap.plugins import ArenaVehiclesPlugin
from helpers import dependency
from helpers.CallbackDelayer import CallbackDelayer
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import DriftkingsConfigInterface, override, Analytics, logWarning, getPlayer, calculate_version, logError


class ConfigInterface(DriftkingsConfigInterface, CallbackDelayer):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self._spotted_cache = {}
        self.as_create = False
        CallbackDelayer.__init__(self)
        self.place = os.path.join('..', 'mods', 'configs', 'Driftkings', '%(mod_ID)s', 'icons')
        super(ConfigInterface, self).__init__()
        override(PlayerAvatar, '_PlayerAvatar__startGUI', self.__startGui)
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.__destroyGUI)

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.4.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'text': {'x': -60, 'y': 0},
            'neverSeen': '<img src=\'img://' + self.place + 'neverSeen.png\' width=\'22\' height=\'22\'>',
            'spotted': '<img src=\'img://' + self.place + 'spotted.png\' width=\'22\' height=\'22\'>',
            'lost': '<img src=\'img://' + self.place + 'lost.png\' width=\'22\' height=\'22\'>',
            'dead': '<img src=\'img://' + self.place + 'dead.png\' width=\'22\' height=\'22\'>'
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_neverSeen_text': 'Never Seen',
            'UI_setting_neverSeen_tooltip': '',
            'UI_setting_spotted_text': 'Spotted',
            'UI_setting_spotted_tooltip': '',
            'UI_setting_lost_text': 'Lost',
            'UI_setting_lost_tooltip': '',
            'UI_setting_dead_text': 'Dead',
            'UI_setting_dead_tooltip': '',
            'UI_setting_help_text': 'Help:',
            'UI_setting_help_tooltip': (
                ' * You can change images to text or icons.\n'
                ' * For icons go to game folder "mods/configs/Driftkings/SpottedStatus/icons/*.png" and replace names\n'
                '{}\n{}'.format(
                    '<img src=\'img://gui/maps/uiKit/dialogs/icons/alert.png\' width=\'18\' height=\'18\'>',
                    '<font color=\'#\'>Please don\'t change the text in text box if you don\'t know what you\'re doing.</font>'
                )
            )
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        help = self.tb.createLabel('help')
        help['tooltip'] += 'help'

        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('neverSeen', self.tb.types.TextInput, 350),
                self.tb.createControl('spotted', self.tb.types.TextInput, 350),
                self.tb.createControl('lost', self.tb.types.TextInput, 350),
                self.tb.createControl('dead', self.tb.types.TextInput, 350)
            ],
            'column2': [
                help
            ]
        }

    def clear(self):
        self._spotted_cache = {}
        self.clearCallbacks()

    def __startGui(self, func, *args):
        func(*args)
        self.vehiclesInfo()
        self.start()
        self.delayCallback(0.3, self.start)

    def __destroyGUI(self, func, *args):
        func(*args)
        self.clear()

    def getSpottedStatus(self):
        for vehicleID in self._spotted_cache:
            # neverSeen, spotted, lost, dead
            if self._spotted_cache[vehicleID] == 'neverSeen':
                if self.as_create:
                    g_driftkingsPlayersPanels.update(self.ID, {'vehicleID': vehicleID, 'text': self.data['neverSeen']})
            # dead
            elif self._spotted_cache[vehicleID] == 'dead':
                if self.as_create:
                    g_driftkingsPlayersPanels.update(self.ID, {'vehicleID': vehicleID, 'text': self.data['dead']})
            # lost
            elif self._spotted_cache[vehicleID] == 'lost':
                if self.as_create:
                    g_driftkingsPlayersPanels.update(self.ID, {'vehicleID': vehicleID, 'text': self.data['lost']})
            # spotted
            elif self._spotted_cache[vehicleID] == 'spotted':
                if self.as_create:
                    g_driftkingsPlayersPanels.update(self.ID, {'vehicleID': vehicleID, 'text': self.data['spotted']})

    def updateSpottedStatus(self, vehicleID, spotted):
        arena = getPlayer().arena if hasattr(getPlayer(), 'arena') else None
        if arena is None:
            return
        else:
            arenaVehicle = arena.vehicles[vehicleID] if vehicleID in arena.vehicles else None
            if arenaVehicle is None:
                return
            if vehicleID in self._spotted_cache:
                if not arenaVehicle['isAlive']:
                    self._spotted_cache[vehicleID] = 'dead'
                    return
                if spotted:
                    self._spotted_cache[vehicleID] = 'spotted'
                    return
                self._spotted_cache[vehicleID] = 'lost'
            return

    def vehiclesInfo(self):
        for vInfo in self.sessionProvider.getArenaDP().getVehiclesInfoIterator():
            if not vInfo.team == getPlayer().team:
                self._spotted_cache[vInfo.vehicleID] = 'neverSeen'

    def start(self):
        if g_driftkingsPlayersPanels.events.onUIReady and not self.as_create:
            self.as_create = True
            g_driftkingsPlayersPanels.create(self.ID, {'right': {'x': self.data['text']['x'], 'y': self.data['text']['y']}})
        if hasattr(getPlayer(), 'arena'):
            arena = getPlayer().arena
            for vID in self._spotted_cache:
                if self._spotted_cache[vID] != 'dead':
                    arenaVehicle = arena.vehicles[vID] if vID in arena.vehicles else None
                    if arenaVehicle:
                        if not arenaVehicle['isAlive']:
                            self._spotted_cache[vID] = 'dead'
                    elif not self.sessionProvider.getArenaDP().getVehicleInfo(vID).isAlive():
                        self._spotted_cache[vID] = 'dead'
        self.getSpottedStatus()
        return 0.3

    def arenaVehiclesPlugin(self, vehicleID, spotted):
        self.updateSpottedStatus(vehicleID, spotted)
        self.getSpottedStatus()


config = None
try:
    from DriftkingsPlayersPanelAPI import g_driftkingsPlayersPanels
    config = ConfigInterface()
    statistic_mod = Analytics(config.ID, config.version)
except ImportError:
    logWarning(config.ID, 'Battle Flash API not found.')
except Exception as err:
    logError(config.ID, 'Error initializing mod: {}', err)
    traceback.print_exc()
else:
    @override(ArenaVehiclesPlugin, '_setInAoI')
    def new_setInAoI(func, self, entry, isInAoI, *args, **kwargs):
        result = func(self, entry, isInAoI, *args, **kwargs)
        try:
            for vehicleID, entry2 in self._entries.iteritems():
                if entry == entry2 and config.data['enabled']:
                    config.arenaVehiclesPlugin(vehicleID, isInAoI)
                    break
        except StandardError:
            traceback.print_exc()
        finally:
            return result
