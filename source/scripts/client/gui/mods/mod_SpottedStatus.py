# -*- coding: utf-8 -*-
import traceback

from Avatar import PlayerAvatar
from gui.Scaleform.daapi.view.battle.shared.minimap.plugins import ArenaVehiclesPlugin
from helpers import dependency
from helpers.CallbackDelayer import CallbackDelayer
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import SimpleConfigInterface, override, Analytics, logWarning, getPlayer


class ConfigInterface(SimpleConfigInterface, CallbackDelayer):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self._spotted_cache = {}
        self.as_create = False
        CallbackDelayer.__init__(self)
        override(PlayerAvatar, '_PlayerAvatar__startGUI', self.new_startGui)
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.new_destroyGUI)
        self.place = '/'.format(['..', 'mods', 'configs', 'Driftkings', '%(mod_ID)s', 'icons', ''])
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.4.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
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
            'UI_version': self.version,
            'UI_setting_neverSeen_text': 'Never Seen',
            'UI_setting_neverSeen_tooltip': '',
            'UI_setting_spotted_text': 'Spotted',
            'UI_setting_spotted_tooltip': '',
            'UI_setting_lost_text': 'Lost',
            'UI_setting_lost_tooltip': '',
            'UI_setting_dead_text': 'Dead',
            'UI_setting_dead_tooltip': '',
            'UI_setting_help_text': 'Help:',
            'UI_setting_help_tooltip': ' * You can change images to text or icons.\n'
                                       ' * For icons go to ../Games/WorldOfTanks_xx/mods/configs/Driftkings/SpottedStatus/icons/*.png and replace names\n'
                                       '<img src=\'img://gui/maps/uiKit/dialogs/icons/alert.png\' width=\'22\' height=\'22\'><font color=\'#\'>\t'
                                       'Please don\'t chang the text in text box if you don\'t know you doing</font><img src=\'img://gui/maps/uiKit/dialogs/icons/alert.png\' width=\'22\' height=\'22\'>'
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

    def new_startGui(self, func, *args):
        func(*args)
        self.vehiclesInfo()
        self.start()
        self.delayCallback(0.3, self.start)

    def new_destroyGUI(self, func, *args):
        func(*args)
        self.clear()

    def getSpottedStatus(self):
        for vID in self._spotted_cache:
            if self._spotted_cache[vID] == 'neverSeen':
                if self.as_create:
                    g_driftkingsPlayersPanels.update(self.ID, {'vehicleID': vID, 'text': self.data['neverSeen']})

            elif self._spotted_cache[vID] == 'dead':
                if self.as_create:
                    g_driftkingsPlayersPanels.update(self.ID, {'vehicleID': vID, 'text': self.data['dead']})

            elif self._spotted_cache[vID] == 'lost':
                if self.as_create:
                    g_driftkingsPlayersPanels.update(self.ID, {'vehicleID': vID, 'text': self.data['lost']})
            elif self._spotted_cache[vID] == 'spotted':
                if self.as_create:
                    g_driftkingsPlayersPanels.update(self.ID, {'vehicleID': vID, 'text': self.data['spotted']})

    def updateSpottedStatus(self, vID, spotted):
        player = getPlayer()
        arena = player.arena if hasattr(player, 'arena') else None
        if arena is None:
            return
        else:
            arenaVehicle = arena.vehicles[vID] if vID in arena.vehicles else None
            if arenaVehicle is None:
                return
            if vID in self._spotted_cache:
                if not arenaVehicle['isAlive']:
                    self._spotted_cache[vID] = 'dead'
                    return
                if spotted:
                    self._spotted_cache[vID] = 'spotted'
                    return
                self._spotted_cache[vID] = 'lost'
            return

    def vehiclesInfo(self):
        for vInfo in self.sessionProvider.getArenaDP().getVehiclesInfoIterator():
            if not vInfo.team == getPlayer().team:
                self._spotted_cache[vInfo.vehicleID] = 'neverSeen'

    def start(self):
        if g_driftkingsPlayersPanels.events.onUIReady and not self.as_create:
            self.as_create = True
            g_driftkingsPlayersPanels.create(self.ID, {
                'right': {
                    'x': self.data['text']['x'],
                    'y': self.data['text']['y']
                }
            })

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


g_config = None
try:
    from DriftkingsPlayersPanelAPI import g_driftkingsPlayersPanels

    g_config = ConfigInterface()
    statistic_mod = Analytics(g_config.ID, g_config.version, 'UA-76792179-11')
except ImportError:
    logWarning(g_config.ID, 'Battle Flash API not found.')
except StandardError:
    traceback.print_exc()
else:
    @override(ArenaVehiclesPlugin, '_setInAoI')
    def new_setInAoI(func, self, entry, isInAoI):
        result = func(self, entry, isInAoI)
        try:
            for vehicleID, entry2 in self._entries.iteritems():
                if entry == entry2 and g_config.data['enabled']:
                    g_config.arenaVehiclesPlugin(vehicleID, isInAoI)
                    break
        except StandardError:
            traceback.print_exc()
        finally:
            return result
