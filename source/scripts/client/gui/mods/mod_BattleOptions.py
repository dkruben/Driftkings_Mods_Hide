# -*- coding: utf-8 -*-
import locale
from string import printable
from time import strftime

from Avatar import PlayerAvatar
from PlayerEvents import g_playerEvents
from adisp import adisp_process
from gui.Scaleform.daapi.view.battle.shared.hint_panel import plugins as hint_plugins
from gui.Scaleform.daapi.view.battle.shared.page import SharedPage
from gui.Scaleform.daapi.view.battle.shared.stats_exchange import BattleStatisticsDataController
from gui.Scaleform.daapi.view.battle.shared.timers_panel import TimersPanel
from gui.battle_control.arena_info.arena_vos import VehicleTypeInfoVO
from gui.battle_control.arena_visitor import _ClientArenaVisitor
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
from gui.battle_control.controllers.arena_border_ctrl import ArenaBorderController
from gui.battle_control.controllers.sound_ctrls.comp7_battle_sounds import _EquipmentZoneSoundPlayer
from gui.battle_control.controllers.team_bases_ctrl import BattleTeamsBasesController
from gui.doc_loaders import GuiColorsLoader
from gui.game_control.special_sound_ctrl import SpecialSoundCtrl
from gui.shared.gui_items.processors.vehicle import VehicleAutoBattleBoosterEquipProcessor
from messenger.gui.Scaleform.data.contacts_data_provider import _ContactsCategories
from messenger.storage import storage_getter
from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.app_loader.settings import APP_NAME_SPACE
from gui.shared.personality import ServicesLocator
from gui.battle_control.arena_info.arena_vos import PlayerInfoVO, VehicleArenaInfoVO

from DriftkingsCore import SimpleConfigInterface, Analytics, override, overrideMethod, logInfo, logDebug, isReplay
from DriftkingsInject import DriftkingsInjector, g_events, DateTimesMeta, CyclicTimerEvent

AS_SWF = 'BattleClock.swf'
AS_BATTLE = 'BattleClockView'
AS_INJECTOR = 'BattleClockInjector'
_cache = set()


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.1.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'showBattleHint': False,
            'postmortemTips': True,
            'showPostmortemDogTag': True,
            'disableSoundCommander': False,
            'stunSound': False,
            'muteTeamBaseSound': False,
            'showAnonymous': False,
            'hideBadges': False,
            'hideClanName': False,
            'hideBattlePrestige': False,
            'color': 'FF002A',
            'showFriends': False,
            'inBattle': True,
            'format': '<font face=\'$FieldFont\' size=\'16\' color=\'#FFFFFF\'><p align=\'left\'>%H:%M:%S</p></font>',
            'directivesOnlyFromStorage': False,
            'position': {'x': -870, 'y': 1},
            'version': sum(int(x) * (10 ** i) for i, x in enumerate(reversed(self.version.split(' ')[0].split('.'))))
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': sum(int(x) * (10 ** i) for i, x in enumerate(reversed(self.version.split(' ')[0].split('.')))),
            'UI_setting_showBattleHint_text': 'Hide Trajectory View.',
            'UI_setting_showBattleHint_tooltip': 'Hide the tips aiming mode changing in strategic mode.',
            'UI_setting_postmortemTips_text': 'Hide Postmortem Tips',
            'UI_setting_postmortemTips_tooltip': 'Disable pop-up panel at the bottom after death.',
            'UI_setting_showPostmortemDogTag_text': 'Show Postmortem DogTag',
            'UI_setting_showPostmortemDogTag_tooltip': 'Disable pop-up panel with a dog tag.',
            'UI_setting_colorCheck_text': 'Choose Map Border Color:',
            'UI_setting_color_text': '<font color=\'#%(color)s\'>Current color: #%(color)s</font>',
            'UI_setting_color_tooltip': 'This color will be applied to all Maps',
            'UI_setting_disableSoundCommander_text': 'Disable Sound Commander',
            'UI_setting_disableSoundCommander_tooltip': '',
            'UI_setting_stunSound_text': 'Stun Sound',
            'UI_setting_stunSound_tooltip': 'Disable Stun Sound Effect.',
            'UI_setting_muteTeamBaseSound_text': 'Mute Team Base Sound',
            'UI_setting_muteTeamBaseSound_tooltip': '',
            'UI_setting_inBattle_text': 'Clock In Battle',
            'UI_setting_inBattle_tooltip': 'Show clock in battle',
            'UI_setting_showFriends_text': 'Show Friends',
            'UI_setting_showFriends_tooltip': '',
            'UI_setting_directivesOnlyFromStorage_text': 'Directives Only From Storage',
            'UI_setting_directivesOnlyFromStorage_tooltip': '',
            'UI_setting_showAnonymous_text': 'Show Anonymous',
            'UI_setting_showAnonymous_tooltip': '',
            'UI_setting_hideClanName_text': 'Hide Clan Name',
            'UI_setting_hideClanName_tooltip': '',
            'UI_setting_hideBadges_text': 'Hide Badges',
            'UI_setting_hideBadges_tooltip': '',
            'UI_setting_hideBattlePrestige_text': 'Hide Battle Prestige',
            'UI_setting_hideBattlePrestige_tooltip': ''
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        colorLabel = self.tb.createControl('color', self.tb.types.ColorChoice)
        colorLabel['text'] = self.tb.getLabel('colorCheck')
        colorLabel['tooltip'] %= {'color': self.data['color']}
        return {
            'modDisplayName': self.ID,
            'settingsVersion': sum(int(x) * (10 ** i) for i, x in enumerate(reversed(self.version.split(' ')[0].split('.')))),
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showBattleHint'),
                self.tb.createControl('showPostmortemDogTag'),
                self.tb.createControl('stunSound'),
                self.tb.createControl('showAnonymous'),
                self.tb.createControl('hideClanName'),
                self.tb.createControl('hideBadges'),
                self.tb.createControl('hideBattlePrestige'),
            ],
            'column2': [
                self.tb.createControl('muteTeamBaseSound'),
                self.tb.createControl('postmortemTips'),
                colorLabel,
                self.tb.createControl('inBattle'),
                self.tb.createControl('disableSoundCommander'),
                self.tb.createControl('directivesOnlyFromStorage'),
                self.tb.createControl('showFriends')
            ]
        }

    @staticmethod
    def onBattleLoaded():
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if not app:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
statistic_mod = Analytics(config.ID, config.version, 'UA-121940539-1')


class DateTimes(DateTimesMeta):

    def __init__(self):
        super(DateTimes, self).__init__(config.ID)
        self.coding = None
        self.timerEvent = CyclicTimerEvent(1.0, self.updateTimeData)

    def getSettings(self):
        return config.data

    def _populate(self):
        super(DateTimes, self)._populate()
        g_playerEvents.onAvatarReady += self.updateDecoder
        if config.data['enabled'] and config.data['inBattle']:
            self.timerEvent.start()

    def _dispose(self):
        g_playerEvents.onAvatarReady -= self.updateDecoder
        self.timerEvent.stop()
        super(DateTimes, self)._dispose()

    @staticmethod
    def checkDecoder(string):
        for char in string:
            if char not in printable:
                return locale.getpreferredencoding()
        return None

    def updateDecoder(self):
        self.coding = self.checkDecoder(strftime(config.data['format']))

    def updateTimeData(self):
        _time = strftime(config.data['format'])
        if self.coding is not None:
            _time = _time.decode(self.coding)
        self.as_setDateTimeS(_time)


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, DriftkingsInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, DateTimes, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))


# disable commander voices
@override(SpecialSoundCtrl, '__setSpecialVoiceByTankmen')
@override(SpecialSoundCtrl, '__setSpecialVoiceByCommanderSkinID')
def new_setSoundMode(func, *args, **kwargs):
    if config.data['enabled'] and config.data['disableSoundCommander']:
        return False
    return func(*args, **kwargs)


# disable dogTag
@override(_ClientArenaVisitor, 'hasDogTag')
def new_hasDogTag(func, *args, **kwargs):
    return False if config.data['enabled'] and config.data['showPostmortemDogTag'] else func(*args, **kwargs)


# disable battle hints
@override(hint_plugins, 'createPlugins')
def new_createPlugins(func, *args, **kwargs):
    result = func(*args, **kwargs)
    if config.data['enabled'] and config.data['showBattleHint']:
        result.clear()
    return result


# postmortemTips
@override(SharedPage, 'as_onPostmortemActiveS')
def new_setPostmortemTipsVisibleS(func, self, value):
    if config.data['enabled']:
        if not config.data['postmortemTips']:
            value = False
    func(self, value)


@override(SharedPage, '_switchToPostmortem')
def new_switchToPostmortem(func, *args):
    if config.data['enabled'] and config.data['postmortemTips']:
        func(*args)


# force update quests in FullStats
@override(BattleStatisticsDataController, 'as_setQuestsInfoS')
def new_setQuestsInfoS(func, self, data, _):
    func(self, data, True)


# disable battle artillery_stun_effect sound
@override(TimersPanel, '__playStunSoundIfNeed')
def new_playStunSoundIfNeed(base, *args, **kwargs):
    if not config.data['enabled'] and not config.data['stunSound']:
        return base(*args, **kwargs)


@override(_EquipmentZoneSoundPlayer, '_onVehicleStateUpdated')
def new_onVehicleStateUpdated(func, self, state, value):
    if state == VEHICLE_VIEW_STATE.STUN and config.data['stunSound']:
        return
    return func(self, state, value)


# mute battle bases
@override(BattleTeamsBasesController, '__playCaptureSound')
def new_muteCaptureSound(func, *args):
    if config.data['enabled'] and not config.data['muteTeamBaseSound']:
        return func(*args)


# border color
@override(ArenaBorderController, '_ArenaBorderController__getCurrentColor')
def new_getBorderColor(func, self, colorBlind):
    if not config.data['enabled']:
        colors = GuiColorsLoader.load()
        scheme = colors.getSubScheme('areaBorder', 'color_blind' if colorBlind else 'default')
        color = scheme['rgba'] / 255
        return color
    elif config.data['enabled']:
        color = int(config.data['color'], 16)
        alpha = int(100)
        red = ((color & 0xff0000) >> 16) / 255.0
        green = ((color & 0x00ff00) >> 8) / 255.0
        blue = (color & 0x0000ff) / 255.0
        alpha = (alpha / 100.0)
        return red, green, blue, alpha
    func(self, colorBlind)


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    if not config.data['enabled'] and not config.data['inBattle']:
        return
    config.isLobby = False


# is friends
def showFriends():
    return config.data['enabled'] and config.data['showFriends'] and not isReplay()


@overrideMethod(VehicleTypeInfoVO)
def new_VehicleArenaInfoVO(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if config.data['enabled'] and showFriends():
        self.isPremiumIGR |= kwargs.get('accountDBID') in _cache


@override(VehicleTypeInfoVO, 'update')
def new_VehicleTypeInfoVO_update(func, self, *args, **kwargs):
    if config.data['enabled'] and showFriends():
        result = func(self, *args, **kwargs)
        if hasattr(self, 'isPremiumIGR'):
            self.isPremiumIGR |= kwargs.get('accountDBID') in _cache
        return result
    return func(self, *args, **kwargs)


# hide badges
@override(VehicleArenaInfoVO, '__init__')
def new__VehicleArenaInfoVO(func, self, *args, **kwargs):
    if kwargs:
        if config.data['hideBadges'] and 'badges' in kwargs:
            kwargs['badges'] = None
            kwargs['overriddenBadge'] = None
        if config.data['showAnonymous'] and 'accountDBID' in kwargs:
            if kwargs['accountDBID'] == 0:
                kwargs['name'] = kwargs['fakeName'] = 'Anonymous'
        if config.data['hideClanName'] and 'clanAbbrev' in kwargs:
            kwargs['clanAbbrev'] = ''
        if config.data['hideBattlePrestige']:
            kwargs['prestigeLevel'] = kwargs['prestigeGradeMarkID'] = None
    return func(self, *args, **kwargs)


@override(PlayerInfoVO, 'update')
def new__VehicleArenaInfoVO(func, self, **kwargs):
    if kwargs:
        if config.data['showAnonymous'] and 'accountDBID' in kwargs:
            if kwargs['accountDBID'] == 0:
                kwargs['name'] = kwargs['fakeName'] = 'Anonymous'
        if config.data['hideClanName'] and 'clanAbbrev' in kwargs:
            kwargs['clanAbbrev'] = ''
    return func(self, **kwargs)


@adisp_process
def changeValue(vehicle, value):
    yield VehicleAutoBattleBoosterEquipProcessor(vehicle, value).request()


def onVehicleChanged(vehicle):
    if not config.data['enabled'] and not config.data['directivesOnlyFromStorage']:
        return
    if vehicle is None or vehicle.isLocked or vehicle.isInBattle:
        return
    if not hasattr(vehicle, 'battleBoosters') or vehicle.battleBoosters is None:
        logDebug(config.ID, True, 'No battle boosters available for this vehicle: {}', vehicle.userName)
        return
    isAuto = vehicle.isAutoBattleBoosterEquip()
    boosters = vehicle.battleBoosters.installed.getItems()
    for battleBooster in boosters:
        value = battleBooster.inventoryCount > 0
        if value != isAuto:
            changeValue(vehicle, value)
            logInfo(config.ID, 'VehicleAutoBattleBoosterEquipProcessor: value={} vehicle={}, booster={}'.format(value, vehicle.userName, battleBooster.userName))


def onGuiCacheSyncCompleted(_):
    _cache.clear()
    users = storage_getter('users')().getList(_ContactsCategories().getCriteria())
    _cache.update(user._userID for user in users if not user.isIgnored())


g_playerEvents.onGuiCacheSyncCompleted += onGuiCacheSyncCompleted
g_events.onVehicleChangedDelayed += onVehicleChanged
