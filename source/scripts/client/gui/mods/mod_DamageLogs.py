# -*- coding: utf-8 -*-
import math
from collections import defaultdict, namedtuple
from colorsys import hsv_to_rgb

import Keys
from CurrentVehicle import g_currentVehicle
from Event import SafeEvent
from PlayerEvents import g_playerEvents
from constants import ATTACK_REASONS
from constants import BATTLE_LOG_SHELL_TYPES
from debug_utils import LOG_CURRENT_EXCEPTION
from dossiers2.ui.achievements import MARK_ON_GUN_RECORD
from frameworks.wulf import WindowLayer
from gui import InputHandler
from gui.Scaleform.daapi.view.battle.shared.formatters import normalizeHealth
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.DisposableEntity import EntityState
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.locale.INGAME_GUI import INGAME_GUI
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import _LogViewComponent, DamageLogPanel
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE as _ETYPE
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.avatar_getter import getVehicleTypeDescriptor
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID
from gui.shared.personality import ServicesLocator
from helpers import dependency
from helpers import i18n
from skeletons.gui.app_loader import GuiGlobalSpaceID
from skeletons.gui.battle_session import IBattleSessionProvider
from skeletons.gui.shared import IItemsCache

from DriftkingsCore import SimpleConfigInterface, Analytics, override, logDebug, logInfo, g_events

AS_INJECTOR = 'DamageLogsInjector'
AS_BATTLE = 'DamageLogsView'
AS_SWF = 'DamageLogs.swf'

BASE_WG_LOGS = (DamageLogPanel._addToTopLog, DamageLogPanel._updateTopLog, DamageLogPanel._updateBottomLog, DamageLogPanel._addToBottomLog)
validated = {}

_EVENT_TO_TOP_LOG_MACROS = {
    FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY: ('tankAvgDamage', 'tankDamageAvgColor', 'playerDamage'),
    FEEDBACK_EVENT_ID.PLAYER_USED_ARMOR: ('tankAvgBlocked', 'tankBlockedAvgColor', 'blockedDamage'),
    FEEDBACK_EVENT_ID.PLAYER_ASSIST_TO_KILL_ENEMY: ('tankAvgAssist', 'tankAssistAvgColor', 'assistDamage'),
    FEEDBACK_EVENT_ID.PLAYER_ASSIST_TO_STUN_ENEMY: ('tankAvgStun', 'tankStunAvgColor', 'stun'),
    FEEDBACK_EVENT_ID.PLAYER_SPOTTED_ENEMY: (None, None, 'spottedTanks')
}


_SHELL_TYPES_TO_STR = {
    BATTLE_LOG_SHELL_TYPES.ARMOR_PIERCING: INGAME_GUI.DAMAGELOG_SHELLTYPE_ARMOR_PIERCING,
    BATTLE_LOG_SHELL_TYPES.ARMOR_PIERCING_HE: INGAME_GUI.DAMAGELOG_SHELLTYPE_ARMOR_PIERCING_HE,
    BATTLE_LOG_SHELL_TYPES.ARMOR_PIERCING_CR: INGAME_GUI.DAMAGELOG_SHELLTYPE_ARMOR_PIERCING_CR,
    BATTLE_LOG_SHELL_TYPES.HOLLOW_CHARGE: INGAME_GUI.DAMAGELOG_SHELLTYPE_HOLLOW_CHARGE,
    BATTLE_LOG_SHELL_TYPES.HE_MODERN: INGAME_GUI.DAMAGELOG_SHELLTYPE_HIGH_EXPLOSIVE,
    BATTLE_LOG_SHELL_TYPES.HE_LEGACY_STUN: INGAME_GUI.DAMAGELOG_SHELLTYPE_HIGH_EXPLOSIVE,
    BATTLE_LOG_SHELL_TYPES.HE_LEGACY_NO_STUN: INGAME_GUI.DAMAGELOG_SHELLTYPE_HIGH_EXPLOSIVE
}


EXTENDED_FEEDBACK = (FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY, FEEDBACK_EVENT_ID.ENEMY_DAMAGED_HP_PLAYER)
PREMIUM_SHELL_END = 'PREMIUM'
LogData = namedtuple('LogData', ('kills', 'id_list', 'vehicles', 'log_id'))
EfficiencyAVGData = namedtuple('EfficiencyAVGData', ('damage', 'assist', 'stun', 'blocked', 'marksOnGunValue', 'marksOnGunIcon', 'name', 'marksAvailable', 'winRate'))
KeysData = namedtuple('KeysData', ('keys', 'keyFunction'))
KEY_ALIAS_CONTROL = (Keys.KEY_LCONTROL, Keys.KEY_RCONTROL)
KEY_ALIAS_ALT = (Keys.KEY_LALT, Keys.KEY_RALT)
KEY_ALIAS_SHIFT = (Keys.KEY_LSHIFT, Keys.KEY_RSHIFT)


class KeysListener(object):

    def __init__(self):
        self.keysPar = {'useKeyPairs': True}
        self.keysMap = set()
        self.pressedKeys = set()
        self.usableKeys = set()
        g_playerEvents.onAvatarReady += self.onEnterBattlePage
        g_playerEvents.onAvatarBecomeNonPlayer += self.onExitBattlePage

    def registerComponent(self, keyFunction, keyList=None):
        self.keysMap.add(KeysData(self.normalizeKey(keyList) if keyList else KEY_ALIAS_ALT, keyFunction))

    def clear(self):
        self.keysMap.clear()
        self.usableKeys.clear()
        self.pressedKeys.clear()

    def onEnterBattlePage(self):
        InputHandler.g_instance.onKeyDown += self.onKeyDown
        InputHandler.g_instance.onKeyUp += self.onKeyUp

    def onExitBattlePage(self):
        InputHandler.g_instance.onKeyDown -= self.onKeyDown
        InputHandler.g_instance.onKeyUp -= self.onKeyUp
        self.clear()

    def onKeyUp(self, event):
        if event.key not in self.pressedKeys:
            return
        for keysData in self.keysMap:
            if event.key in keysData.keys:
                try:
                    keysData.keyFunction(False)
                except StandardError:
                    LOG_CURRENT_EXCEPTION()
        self.pressedKeys.discard(event.key)

    def onKeyDown(self, event):
        if event.key not in self.usableKeys or event.key in self.pressedKeys:
            return
        for keysData in self.keysMap:
            if event.key in keysData.keys:
                try:
                    keysData.keyFunction(True)
                except StandardError:
                    LOG_CURRENT_EXCEPTION()
        self.pressedKeys.add(event.key)

    def normalizeKey(self, keyList):
        keys = set()
        for key in keyList:
            if isinstance(key, (list, set, tuple)):
                keys.update(key)
            else:
                keys.add(key)
        if self.keysPar['useKeyPairs']:
            for key in tuple(keys):
                if key in KEY_ALIAS_CONTROL:
                    keys.update(KEY_ALIAS_CONTROL)
                elif key in KEY_ALIAS_ALT:
                    keys.update(KEY_ALIAS_ALT)
                elif key in KEY_ALIAS_SHIFT:
                    keys.update(KEY_ALIAS_SHIFT)
        self.usableKeys.update(keys)
        return tuple(keys)


g_keysListener = KeysListener()


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,

            'reversLog': True,
            'enableLogExtended': True,
            'enabledLogTotal': True,
            'topEnabled': True,

            'wgLogHideCritics': True,
            'wgLogHideBlock': True,
            'wgLogHideAssist': True,
            'logExtended': {
                'attackReason': {
                    "AdaptationHealthRestore": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "artillery_eq": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "artillery_protection": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "artillery_sector": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "berserker_eq": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "bomber_eq": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "bombers": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "clingBrander": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "corrodingShot": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "death_zone": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "drowning": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "fire": "<img src='img://gui/maps/icons/DamageLogs/efficiency/fire.png' width='15' height='15' vspace='-4'>",
                    "fireCircle": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "fort_artillery_eq": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "gas_attack": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "manual": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "minefield_eq": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "none": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "overturn": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "ram_brander": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "ram_cling_brander": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "ramming": "<img src='img://gui/maps/icons/DamageLogs/efficiency/ram.png' width='15' height='15' vspace='-4'>",
                    "recovery": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "shot": "<img src='img://gui/maps/icons/DamageLogs/efficiency/damage.png' width='15' height='15' vspace='-4'>",
                    "smoke": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "spawned_bot_explosion": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "thunderStrike": "<img src='img://gui/maps/icons/DamageLogs/efficiency/module.png' width='15' height='15' vspace='-4'>",
                    "world_collision": "<img src='img://gui/maps/icons/DamageLogs/efficiency/ram.png' width='15' height='15' vspace='-4'>"
                },
                'avgColor': {
                    'brightness': 1.0,
                    'saturation': 0.5
                },
                'bottomEnabled': True,
                'enabled': True,
                'killedIcon': '<img src=\'img://gui/maps/icons/DamageLogs/efficiency/destruction.png\' width=\'14\' height=\'14\' vspace=\'-4\'>',
                'logsAltModeHotkey': [[56]],
                'reverse': True,
                'settings': {
                    'align': 'left',
                    'x': 6,
                    'y': 756
                },
                'shellColor': {
                    'gold': '#FFD700',
                    'normal': '#FAFAFA'
                },
                'templates': [
                    [
                        "<textformat leading='-2' tabstops='[20, 55, 80, 100]'><font face='$TitleFont' size='15'>",
                        "<font size='12'>%(index)02d:</font><tab>",
                        "<font color='%(percentDamageAvgColor)s'>%(totalDamage)s</font><tab>",
                        "<font color='%(shellColor)s'>%(shellType)s</font><tab>",
                        "%(attackReason)s<tab>",
                        "%(classIcon)s%(tankName)s %(killedIcon)s",
                        "</font></textformat>"
                    ],
                    [
                        "<textformat leading='-2' tabstops='[20, 55, 80, 100]'><font face='$TitleFont' size='15'>",
                        "<font size='12'>%(shots)d:</font><tab>",
                        "<font color='%(percentDamageAvgColor)s'>%(lastDamage)s</font><tab>",
                        "<font color='%(shellColor)s'>%(shellType)s</font><tab>",
                        "%(attackReason)s<tab>",
                        "%(classIcon)s%(userName).12s %(killedIcon)s",
                        "</font></textformat>"
                    ]
                ],
                'topEnabled': True
            },
            'logTotal': {
                'avgColor': {
                    'brightness': 1.0,
                    'saturation': 0.5
                },
                'enabled': True,
                'icons': {
                    "assistIcon": "<img src='img://gui/maps/icons/DamageLogs/efficiency/help.png' width='16' height='16' vspace='-4'>",
                    "blockedIcon": "<img src='img://gui/maps/icons/DamageLogs/efficiency/armor.png' width='16' height='16' vspace='-4'>",
                    "damageIcon": "<img src='img://gui/maps/icons/DamageLogs/efficiency/damage.png' width='16' height='16' vspace='-4'>",
                    "spottedIcon": "<img src='img://gui/maps/icons/DamageLogs/efficiency/detection.png' width='16' height='16' vspace='-4'>",
                    "stunIcon": "<img src='img://gui/maps/icons/DamageLogs/efficiency/stun.png' width='16' height='16' vspace='-4'>"
                },
                'separate': '  ',
                'settings': {
                    'align': 'right',
                    'inCenter': True,
                    'x': -260,
                    'y': 0
                },
                'templateMainDMG': [
                    "%(damageIcon)s<font color='%(tankDamageAvgColor)s'>%(playerDamage)s</font>",
                    "%(blockedIcon)s<font color='%(tankBlockedAvgColor)s'>%(blockedDamage)s</font>",
                    "%(assistIcon)s<font color='%(tankAssistAvgColor)s'>%(assistDamage)s</font>",
                    "%(spottedIcon)s%(spottedTanks)s",
                    "%(stunIcon)s<font color='%(tankStunAvgColor)s'>%(stun)s</font>"
                ]
            }

        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_colour_text': '',
            'UI_setting_colour_tooltip': '',
            'UI_setting_isModel_text': '',
            'UI_setting_isModel_tooltip': '',
            #
            'UI_setting_reversLog_text': 'Enable Reverse Log.',
            'UI_setting_reversLog_tooltip': 'Reverses the position of the damage log.',
            'UI_setting_wgLogHideCritics_text': 'WG Log Hide Critics',
            'UI_setting_wgLogHideCritics_tooltip': '',
            'UI_setting_wgLogHideBlock_text': 'WG Log Hide Block',
            'UI_setting_wgLogHideBlock_tooltip': '',
            'UI_setting_wgLogHideAssist_text': 'WG Log Hide Assist',
            'UI_setting_wgLogHideAssist_tooltip': ''
            # 'UI_colors': {}
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('reversLog'),
                self.tb.createControl('wgLogHideCritics'),
                self.tb.createControl('wgLogHideBlock'),
                self.tb.createControl('wgLogHideAssist')
            ],
            'column2': []
        }


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class CurrentVehicleCachedData(object):
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        default = 2500
        self.__default = EfficiencyAVGData(default, default, default, 0, 0.0, '', 'Undefined', False, 0.0)
        self.__EfficiencyAVGData = None

    def onVehicleChanged(self):
        if g_currentVehicle.isPresent():
            self.setAvgData(g_currentVehicle.intCD, g_currentVehicle.item.userName, g_currentVehicle.item.level)
        else:
            self.__EfficiencyAVGData = None

    @staticmethod
    def getWinsEfficiency(random):
        win_rate = random.getWinsEfficiency()
        return round(win_rate * 100, 2) if win_rate is not None else 0.0

    def setAvgData(self, intCD, name, level):
        dossier = self.itemsCache.items.getVehicleDossier(intCD)
        random = dossier.getRandomStats()
        marksOnGun = random.getAchievement(MARK_ON_GUN_RECORD)
        icon = marksOnGun.getIcons()['95x85'][3:]
        marksOnGunIcon = '<img src=\'img://gui/{}\' width=\'20\' height=\'18\' vspace=\'-8\'>'.format(icon)
        self.__EfficiencyAVGData = EfficiencyAVGData(
            int(random.getAvgDamage() or 0),
            int(random.getDamageAssistedEfficiency() or 0),
            int(random.getAvgDamageAssistedStun() or 0),
            int(random.getAvgDamageBlocked() or 0),
            round(marksOnGun.getDamageRating(), 2),
            marksOnGunIcon,
            name,
            level > 4,
            self.getWinsEfficiency(random)
        )
        logDebug(False, self.__EfficiencyAVGData)

    @property
    def efficiencyAvgData(self):
        return self.__EfficiencyAVGData or self.__default


cachedVehicleData = CurrentVehicleCachedData()


def percentToRGB(percent, saturation=0.5, brightness=1.0, **__):
    """Percent is float number in range 0 - 2.4 purple, or 1.0 green."""
    position = min(0.8333, percent * 0.3333)
    r, g, b = (int(math.ceil(i * 255)) for i in hsv_to_rgb(position, saturation, brightness))
    return '#{:02X}{:02X}{:02X}'.format(r, g, b)


def getPercent(param_a, param_b):
    if param_b <= 0:
        return 0.0
    return float(normalizeHealth(param_a)) / param_b


def getI18nShellName(shellType):
    return i18n.makeString(_SHELL_TYPES_TO_STR[shellType])


def getVehicleClassIcon(classTag):
    if not classTag:
        return ''
    return '<img src=\'{}/vehicle_types/{}.png\' width=\'20\' height=\'20\' vspace=\'-6\'>'.format('img://gui/maps/icons/DamageLogs/', classTag)


class DamageLogsInjector(View):

    def _populate(self):
        # noinspection PyProtectedMember
        super(DamageLogsInjector, self)._populate()
        g_events.onBattleClosed += self.destroy

    def _dispose(self):
        g_events.onBattleClosed -= self.destroy
        # noinspection PyProtectedMember
        super(DamageLogsInjector, self)._dispose()

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            return
        super(DamageLogsInjector, self).destroy()


class DamageLogsMeta(BaseDAAPIComponent):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.color = {
            'vehicleTypesColors': {
                'AT-SPG': '#0094EC',
                'SPG': '#A90400',
                'heavyTank': '#F9B200',
                'lightTank': '#37BC00',
                'mediumTank': '#FDEF6C',
                'unknown': '#FAFAFA'
            }
        }
        self._arenaDP = self.sessionProvider.getArenaDP()
        self._arenaVisitor = self.sessionProvider.arenaVisitor
        super(DamageLogsMeta, self).__init__()

    def isSPG(self):
        return self.getVehicleInfo().isSPG()

    def getVehicleInfo(self, vID=None):
        return self._arenaDP.getVehicleInfo(vID)

    def _populate(self):
        # noinspection PyProtectedMember
        super(DamageLogsMeta, self)._populate()
        g_events.onBattleClosed += self.destroy
        logInfo('\'%s\' loaded' % config.ID)

    def _dispose(self):
        g_events.onBattleClosed -= self.destroy
        # noinspection PyProtectedMember
        super(DamageLogsMeta, self)._dispose()
        logInfo('\'%s\' destroyed' % config.ID)

    @property
    def isPlayerVehicle(self):
        vehicle = self.sessionProvider.shared.vehicleState.getControllingVehicle()
        if vehicle is not None:
            return vehicle.id == self.playerVehicleID
        observed_veh_id = self.sessionProvider.shared.vehicleState.getControllingVehicleID()
        return self.playerVehicleID == observed_veh_id or observed_veh_id == 0

    @property
    def playerVehicleID(self):
        return self._arenaDP.getPlayerVehicleID()

    def getVehicleClassColor(self, classTag):
        return self.color['vehicleTypesColors'][classTag or 'unknown']

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            return
        super(DamageLogsMeta, self).destroy()

    def as_createExtendedLogsS(self, position, topEnabled, bottomEnabled):
        return self.flashObject.as_createExtendedLogs(position, topEnabled, bottomEnabled) if self._isDAAPIInited() else None

    def as_createTopLogS(self, settings):
        return self.flashObject.as_createTopLog(settings) if self._isDAAPIInited() else None

    def as_updateExtendedLogS(self, logID, text):
        return self.flashObject.as_updateExtendedLog(logID, text) if self._isDAAPIInited() else None

    def as_updateTopLogS(self, text):
        return self.flashObject.as_updateTopLog(text) if self._isDAAPIInited() else None


class DamageLogs(DamageLogsMeta):

    def __init__(self):
        super(DamageLogs, self).__init__()
        self._damage_done = None
        self._damage_received = None
        self._is_extended_log_enabled = False
        self._is_key_down = 0
        self._is_top_log_enabled = False
        self._playerShell = ('--', False)
        self.top_log = defaultdict(int)
        self.last_shell = defaultdict(lambda: ('--', False))
        self.top_log_template = ''
        self.log_extended = {}
        self.log_total = None

    def _populate(self):
        # noinspection PyProtectedMember
        super(DamageLogs, self)._populate()
        feedback = self.sessionProvider.shared.feedback
        if feedback is None:
            return
        feedback.onPlayerFeedbackReceived += self.__onPlayerFeedbackReceived
        self._is_top_log_enabled = config.data['enabled'] and config.data['topEnabled']
        if self._is_top_log_enabled:
            self.as_createTopLogS(config.data['logExtended']['settings'])
            self.update_top_log_start_params()
            self.as_updateTopLogS(self.top_log_template % self.top_log)
        self._is_extended_log_enabled = config.data['logExtended']['enabled'] and config.data['enableLogExtended'] and not self._arenaVisitor.gui.isEpicBattle()
        if self._is_extended_log_enabled:
            position = config.data['logExtended']['settings']
            top_enabled = config.data['logExtended']['topEnabled']
            bottom_enabled = config.data['logExtended']['bottomEnabled']
            self.as_createExtendedLogsS(position, top_enabled, bottom_enabled)
            g_keysListener.registerComponent(self.onLogsAltMode, keyList=config.data['logExtended']['logsAltModeHotkey'])
            self._damage_done = LogData(set(), list(), dict(), 0)
            self._damage_received = LogData(set(), list(), dict(), 1)
            arena = self._arenaVisitor.getArenaSubscription()
            if arena is not None:
                arena.onVehicleUpdated += self.onVehicleUpdated
                arena.onVehicleKilled += self.onVehicleKilled
            ammo_ctrl = self.sessionProvider.shared.ammo
            if ammo_ctrl is not None:
                ammo_ctrl.onGunReloadTimeSet += self._onGunReloadTimeSet

    def update_top_log_start_params(self):
        template = config.data['logTotal']['templateMainDMG']
        self.top_log.update(config.data['logTotal']['icons'], tankDamageAvgColor='#FFFFFF', tankAssistAvgColor='#FFFFFF', tankBlockedAvgColor='#FFFFFF', tankStunAvgColor='#FFFFFF', tankAvgDamage=cachedVehicleData.efficiencyAvgData.damage, tankAvgAssist=cachedVehicleData.efficiencyAvgData.assist, tankAvgStun=cachedVehicleData.efficiencyAvgData.stun, tankAvgBlocked=cachedVehicleData.efficiencyAvgData.blocked)
        if not self.isSPG():
            self.top_log.update(stun='', stunIcon='')
            template = [line for line in template if 'stunIcon' not in line]
        self.top_log_template = config.data['logTotal']['separate'].join(template)

    def isExtendedLogEventEnabled(self, eventType):
        return self._is_extended_log_enabled and eventType in EXTENDED_FEEDBACK

    def isTopLogEventEnabled(self, eventType):
        return self._is_top_log_enabled and eventType in _EVENT_TO_TOP_LOG_MACROS

    def getLogData(self, eventType):
        if eventType == FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY:
            return self._damage_done
        elif eventType == FEEDBACK_EVENT_ID.ENEMY_DAMAGED_HP_PLAYER:
            return self._damage_received
        raise ValueError('logExtended: incorrect event parameter in getLogData module {}'.format(eventType))

    def _dispose(self):
        feedback = self.sessionProvider.shared.feedback
        if feedback is not None:
            feedback.onPlayerFeedbackReceived -= self.__onPlayerFeedbackReceived
            if self._is_extended_log_enabled:
                arena = self._arenaVisitor.getArenaSubscription()
                if arena is not None:
                    arena.onVehicleUpdated -= self.onVehicleUpdated
                    arena.onVehicleKilled -= self.onVehicleKilled
                ammo_ctrl = self.sessionProvider.shared.ammo
                if ammo_ctrl is not None:
                    ammo_ctrl.onGunReloadTimeSet -= self._onGunReloadTimeSet
            if self._is_top_log_enabled:
                self.top_log.clear()
        # noinspection PyProtectedMember
        super(DamageLogs, self)._dispose()

    def _onGunReloadTimeSet(self, _, state, *__, **___):
        if state.isReloadingFinished():
            type_descriptor = getVehicleTypeDescriptor()
            if type_descriptor is None:
                self._playerShell = ('--', False)
            shell = type_descriptor.shot.shell
            shell_name = getI18nShellName(BATTLE_LOG_SHELL_TYPES.getType(shell))
            is_shell_gold = shell.isGold or PREMIUM_SHELL_END in shell.iconName
            self._playerShell = (shell_name, is_shell_gold)

    def onLogsAltMode(self, isKeyDown):
        """Hot key event"""
        self._is_key_down = int(isKeyDown)
        self.updateExtendedLog(self._damage_done)
        self.updateExtendedLog(self._damage_received)

    def parseEvent(self, event):
        """wg Feedback event parser"""
        eType = event.getType()
        extra = event.getExtra()
        if self.isTopLogEventEnabled(eType):
            self.addToTopLog(eType, event, extra)
        if self.isExtendedLogEventEnabled(eType):
            self.addToExtendedLog(eType, event.getTargetID(), extra)

    def addToTopLog(self, e_type, event, extra):
        avg_value_macros, avg_color_macros, value_macros = _EVENT_TO_TOP_LOG_MACROS[e_type]
        if e_type == FEEDBACK_EVENT_ID.PLAYER_ASSIST_TO_STUN_ENEMY and not self.top_log['stunIcon']:
            self.top_log_template = config.data['logTotal']['separate'].join(config.data['logTotal']['templateMainDMG'])
            self.top_log['stunIcon'] = config.data['logTotal']['icons']['stunIcon']
            self.top_log[value_macros] = 0
        self.top_log[value_macros] += self.unpackTopLogValue(e_type, event, extra)
        if avg_value_macros is not None:
            value = self.top_log[value_macros]
            avg_value = self.top_log[avg_value_macros]
            self.top_log[avg_color_macros] = self.getAVGColor(getPercent(value, avg_value))
        self.as_updateTopLogS(self.top_log_template % self.top_log)

    @staticmethod
    def unpackTopLogValue(e_type, event, extra):
        if e_type == FEEDBACK_EVENT_ID.PLAYER_SPOTTED_ENEMY:
            return event.getCount()
        return extra.getDamage()

    def __onPlayerFeedbackReceived(self, events):
        """Shared feedback player events"""
        if self.isPlayerVehicle:
            for event in events:
                self.parseEvent(event)

    @staticmethod
    def getAVGColor(percent):
        return percentToRGB(percent, **config.data['logTotal']['avgColor']) if percent else '#FFFFFF'

    def onVehicleUpdated(self, vehicleID, *_, **__):
        """update log item in GM-mode"""
        vehicle_info_vo = self.getVehicleInfo(vehicleID)
        if vehicle_info_vo:
            vehicle_type = vehicle_info_vo.vehicleType
            if vehicle_type and vehicle_type.maxHealth and vehicle_type.classTag:
                log_data = self.getLogData(FEEDBACK_EVENT_ID.ENEMY_DAMAGED_HP_PLAYER)
                vehicle = log_data.vehicles.get(vehicleID)
                if vehicle and vehicle.get('vehicleClass') is None:
                    self.createVehicle(vehicle_info_vo, vehicle, update=True)
                    self.updateExtendedLog(log_data)

    def onVehicleKilled(self, targetID, attackerID, *_, **__):
        if self.playerVehicleID in (targetID, attackerID):
            if self.playerVehicleID == targetID:
                log_data = self.getLogData(FEEDBACK_EVENT_ID.ENEMY_DAMAGED_HP_PLAYER)
                log_data.kills.add(attackerID)
            else:
                log_data = self.getLogData(FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY)
                log_data.kills.add(targetID)
            self.updateExtendedLog(log_data)

    def checkShell(self, extra, target_id):
        shell_type = extra.getShellType()
        is_gold = extra.isShellGold()
        if shell_type is not None:
            self.last_shell[target_id] = (getI18nShellName(shell_type), is_gold)
        return self.last_shell[target_id]

    def addToExtendedLog(self, e_type, target_id, extra):
        """add to log item"""
        log_data = self.getLogData(e_type)
        isPlayer = log_data.log_id == 0
        if target_id not in log_data.id_list:
            log_data.id_list.append(target_id)
        if extra.isShot() or extra.isFire():
            shell_name, gold = self._playerShell if isPlayer else self.checkShell(extra, target_id)
        else:
            shell_name, gold = '--', False
        logDebug(True, 'Shell type: {}, gold: {}, is_player: {}', shell_name, gold, isPlayer)
        vehicle = log_data.vehicles.setdefault(target_id, defaultdict(lambda: 'macros not found'))
        vehicleInfoVo = self.getVehicleInfo(target_id)
        if isPlayer:
            max_health = vehicleInfoVo.vehicleType.maxHealth
        else:
            max_health = self.getVehicleInfo().vehicleType.maxHealth
        if not vehicle:
            self.createVehicle(vehicleInfoVo, vehicle, index=len(log_data.id_list))
        self.updateVehicleData(extra, gold, shell_name, vehicle, max_health, isPlayer)
        self.updateExtendedLog(log_data)

    def updateVehicleData(self, extra, gold, shell_name, vehicle, maxHealth, isPlayer):
        vehicle['damageList'].append(extra.getDamage())
        vehicle['shots'] = len(vehicle['damageList'])
        vehicle['totalDamage'] = sum(vehicle['damageList'])
        vehicle['allDamages'] = ', '.join(str(x) for x in vehicle['damageList'])
        vehicle['lastDamage'] = vehicle['damageList'][-1]
        vehicle['attackReason'] = config.data['logExtended']['attackReason'][ATTACK_REASONS[extra.getAttackReasonID()]]
        vehicle['shellType'] = shell_name
        vehicle['shellColor'] = config.data['logExtended']['shellColor'].fromkeys([('normal', 'gold')[gold]])
        percent = getPercent(vehicle['totalDamage'], maxHealth)
        if not isPlayer:
            percent = max((1.0 - percent) * 0.7, 0.01)
        vehicle['percentDamageAvgColor'] = self.getAVGColor(percent)

    def createVehicle(self, vehicleInfoVO, vehicle, update=False, index=1):
        if not update:
            vehicle['index'] = index
            vehicle['damageList'] = list()
            vehicle['killedIcon'] = ''
            vehicle['userName'] = vehicleInfoVO.player.name
        vehicle['vehicleClass'] = vehicleInfoVO.vehicleType.classTag
        vehicle['tankName'] = vehicleInfoVO.vehicleType.guiName
        vehicle['iconName'] = vehicleInfoVO.vehicleType.iconName
        vehicle['TankLevel'] = vehicleInfoVO.vehicleType.level
        vehicle['classIcon'] = getVehicleClassIcon(vehicleInfoVO.vehicleType.classTag)
        vehicle['tankClassColor'] = self.getVehicleClassColor(vehicleInfoVO.vehicleType.classTag)

    def getLogLines(self, log_data):
        template = ''.join(config.data['logExtended']['templates'][self._is_key_down])
        for vehicleID in reversed(log_data.id_list) if config.data['logExtended']['reverse'] else log_data.id_list:
            if vehicleID in log_data.kills and not log_data.vehicles[vehicleID]['killedIcon']:
                log_data.vehicles[vehicleID]['killedIcon'] = config.data['logExtended']['killedIcon']
            yield template % log_data.vehicles[vehicleID]

    def updateExtendedLog(self, log_data):
        """
        Final log processing and flash output,
        also works when the alt mode activated by hot key.
        """
        if log_data is None or not log_data.id_list:
            return
        result = '\n'.join(self.getLogLines(log_data))
        self.as_updateExtendedLogS(log_data.log_id, result)


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DamageLogsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, DamageLogs, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))


@override(_LogViewComponent, 'addToLog')
def new__addToLog(func, self, event):
    if config.data['enabled']:
        return func(self, [x for x in event if not validated.get(x.getType(), False)])
    return func(self, event)


validated.update({
        _ETYPE.RECEIVED_CRITICAL_HITS: config.data['wgLogHideCritics'],
        _ETYPE.BLOCKED_DAMAGE: config.data['wgLogHideBlock'],
        _ETYPE.ASSIST_DAMAGE: config.data['wgLogHideAssist'],
        _ETYPE.STUN: config.data['wgLogHideAssist']
    })

DamageLogPanel._addToTopLog, DamageLogPanel._updateTopLog, DamageLogPanel._updateBottomLog, DamageLogPanel._addToBottomLog = reversed(BASE_WG_LOGS) if config.data['enabled'] and config.data['reversLog'] else BASE_WG_LOGS


def onBattleLoaded():
    app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
    if app is None:
        return
    app.loadView(SFViewLoadParams(AS_INJECTOR))


g_events.onBattleLoaded += onBattleLoaded
