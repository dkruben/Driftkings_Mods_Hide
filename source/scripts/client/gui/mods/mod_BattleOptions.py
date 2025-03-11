# -*- coding: utf-8 -*-
import locale
import math
import traceback
from collections import defaultdict
from functools import partial
from string import printable
from time import strftime

import CommandMapping
import messenger.gui.Scaleform.view.battle.messenger_view as messenger_view
from Avatar import PlayerAvatar
# from AvatarInputHandler import gun_marker_ctrl
from PlayerEvents import g_playerEvents
from adisp import adisp_process
from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
from comp7.gui.battle_control.controllers.sound_ctrls.comp7_battle_sounds import _EquipmentZoneSoundPlayer
from gambiter import g_guiFlash
from gambiter.flash import COMPONENT_TYPE, COMPONENT_ALIGN
from gui.Scaleform.daapi.view.battle.shared.hint_panel import plugins as hint_plugins
from gui.Scaleform.daapi.view.battle.shared.page import SharedPage
from gui.Scaleform.daapi.view.battle.shared.stats_exchange import BattleStatisticsDataController
from gui.Scaleform.daapi.view.battle.shared.timers_panel import TimersPanel
from gui.battle_control.arena_info.arena_vos import PlayerInfoVO, VehicleArenaInfoVO, VehicleTypeInfoVO
from gui.battle_control.arena_visitor import _ClientArenaVisitor
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
from gui.battle_control.controllers.arena_border_ctrl import ArenaBorderController
from gui.battle_control.controllers.team_bases_ctrl import BattleTeamsBasesController
from gui.battle_results.components.common import ShowRateSatisfactionCmp
from gui.doc_loaders import GuiColorsLoader
from gui.game_control.special_sound_ctrl import SpecialSoundCtrl
from gui.shared.gui_items.processors.vehicle import VehicleAutoBattleBoosterEquipProcessor
from messenger.gui.Scaleform.data.contacts_data_provider import _ContactsCategories
from messenger.storage import storage_getter

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, logInfo, logDebug, square_position, isReplay, calculate_version, callback
from DriftkingsInject import g_events, CyclicTimerEvent

_cache = set()


class ConfigInterface(DriftkingsConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.5.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'clipLoad': True,
            'color': 'FF002A',
            'directivesOnlyFromStorage': False,
            'disableSoundCommander': False,
            'format': '<font face=\'$FieldFont\' size=\'16\' color=\'#FFFFFF\'>%H:%M:%S</p></font>',
            'hideBadges': False,
            'hideBattlePrestige': False,
            'hideClanName': False,
            'inBattle': True,
            'loadTxt': 'Reloading at %(pos)s, for %(load)s seconds.',
            'maxChatLines': 6,
            'muteTeamBaseSound': False,
            'postmortemTips': True,
            'showAnonymous': False,
            'showBattleHint': False,
            # 'camLimits' False,
            'showFriends': False,
            'showPostmortemDogTag': True,
            'stunSound': False,
            'showPlayerSatisfactionWidget': False
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_clipLoad_text': 'ReLoad Status',
            'UI_setting_clipLoad_tooltip': 'Clip Load Time Massage',
            'UI_setting_color_text': '<font color=\'#%(color)s\'>Current color: #%(color)s</font>',
            'UI_setting_color_tooltip': 'This color will be applied to all Maps',
            'UI_setting_colorCheck_text': 'Choose Map Border Color:',
            'UI_setting_directivesOnlyFromStorage_text': 'Directives Only From Storage',
            'UI_setting_directivesOnlyFromStorage_tooltip': 'Disable overriding directives from the storage.',
            'UI_setting_disableSoundCommander_text': 'Disable Sound Commander',
            'UI_setting_disableSoundCommander_tooltip': 'Disable Sound Commander in battle.',
            'UI_setting_hideBadges_text': 'Hide Badges',
            'UI_setting_hideBadges_tooltip': 'Hide Badges in players panel.',
            'UI_setting_hideBattlePrestige_text': 'Hide Battle Prestige',
            'UI_setting_hideBattlePrestige_tooltip': 'Hide Battle Prestige in players panel.',
            'UI_setting_hideClanName_text': 'Hide Clan Name',
            'UI_setting_hideClanName_tooltip': 'Remove clan name in players panel.',
            'UI_setting_inBattle_text': 'Clock In Battle',
            'UI_setting_inBattle_tooltip': 'Show clock in battle',
            'UI_setting_loadTxt_text': 'Text Format',
            'UI_setting_loadTxt_tooltip': 'Use macros to edit the message\n (macros: \'{load}\' - \'{pos}\')',
            'UI_setting_maxChatLines_text': 'Max Chat Lines',
            'UI_setting_maxChatLines_tooltip': 'Limit the number of battle chat lines.',
            'UI_setting_muteTeamBaseSound_text': 'Mute Team Base Sound',
            'UI_setting_muteTeamBaseSound_tooltip': 'Disable team base sound wen this option is enabled.',
            'UI_setting_postmortemTips_text': 'Hide Postmortem Tips',
            'UI_setting_postmortemTips_tooltip': 'Disable pop-up panel at the bottom after death.',
            'UI_setting_showAnonymous_text': 'Show Anonymous',
            'UI_setting_showAnonymous_tooltip': 'Show \'Anonymous\' name in players panel.',
            'UI_setting_showBattleHint_text': 'Hide Trajectory View.',
            'UI_setting_showBattleHint_tooltip': 'Hide the tips aiming mode changing in strategic mode.',
            'UI_setting_showFriends_text': 'Show Friends',
            'UI_setting_showFriends_tooltip': 'Show friends in players panel.',
            # 'UI_setting_camLimits_text': 'Camera Limits',
            # 'UI_setting_camLimits_tooltip': 'Enable camera limits.',
            'UI_setting_showPostmortemDogTag_text': 'Show Postmortem DogTag',
            'UI_setting_showPostmortemDogTag_tooltip': 'Disable pop-up panel with a dog tag.',
            'UI_setting_stunSound_text': 'Stun Sound',
            'UI_setting_stunSound_tooltip': 'Disable Stun Sound Effect.',
            'UI_setting_showPlayerSatisfactionWidget_text': 'Show Player Satisfaction Widget',
            'UI_setting_showPlayerSatisfactionWidget_tooltip': 'Display battle rating "player satisfaction" widget.'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        colorLabel = self.tb.createControl('color', self.tb.types.ColorChoice)
        colorLabel['text'] = self.tb.getLabel('colorCheck')
        colorLabel['tooltip'] %= {'color': self.data['color']}
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showBattleHint'),
                self.tb.createControl('showPostmortemDogTag'),
                self.tb.createControl('stunSound'),
                self.tb.createControl('showAnonymous'),
                self.tb.createControl('hideClanName'),
                self.tb.createControl('hideBadges'),
                self.tb.createControl('hideBattlePrestige'),
                self.tb.createSlider('maxChatLines', 1, 15, 1, '{{value}} Lines'),
                self.tb.createControl('muteTeamBaseSound'),
                self.tb.createControl('postmortemTips')
            ],
            'column2': [
                colorLabel,
                self.tb.createControl('showPlayerSatisfactionWidget'),
                self.tb.createControl('inBattle'),
                self.tb.createControl('disableSoundCommander'),
                self.tb.createControl('directivesOnlyFromStorage'),
                self.tb.createControl('showFriends'),
                # self.tb.createControl('camLimits'),
                self.tb.createControl('clipLoad'),
                self.tb.createControl('loadTxt', self.tb.types.TextInput, 300)
            ]
        }


config = ConfigInterface()
statistic_mod = Analytics(config.ID, config.version)


# Battle Clock
class BattleClock(object):
    def __init__(self):
        self.coding = None
        self.timerEvent = CyclicTimerEvent(1.0, self.updateTimeData)
        g_guiFlash.createComponent(config.ID, COMPONENT_TYPE.LABEL, {'x': 200, 'y': 1, 'alignX': COMPONENT_ALIGN.LEFT, 'alignY': COMPONENT_ALIGN.TOP, 'text': '', 'border': False, 'limit': False})

    def start(self):
        g_playerEvents.onAvatarReady += self.updateDecoder
        if config.data['enabled'] and config.data['inBattle']:
            self.timerEvent.start()

    def stop(self):
        g_playerEvents.onAvatarReady -= self.updateDecoder
        self.timerEvent.stop()

    @staticmethod
    def checkDecoder(string):
        for char in string:
            if char not in printable:
                return locale.getpreferredencoding()
        return None

    def updateDecoder(self):
        self.coding = self.checkDecoder(strftime(config.data['format']))

    def updateTimeData(self):
        time = strftime(config.data['format'])
        if self.coding is not None:
            time = time.decode(self.coding)
        g_guiFlash.updateComponent(config.ID, {'text': time})


battle_clock = BattleClock()


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    battle_clock.start()

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
def new_playStunSoundIfNeed(func, *args, **kwargs):
    if not config.data['enabled'] and not config.data['stunSound']:
        return func(*args, **kwargs)


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
    result = func(self, colorBlind)
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
    return result


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    if not config.data['enabled'] and not config.data['inBattle']:
        return
    config.isLobby = False


# is friends
def showFriends():
    return config.data['enabled'] and config.data['showFriends'] and not isReplay()


@override(VehicleTypeInfoVO, '__init__')
def new_VehicleTypeInfoVO(func, self, *args, **kwargs):
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


# Battle Messages
def onReload(avatar):
    macro = defaultdict(lambda: 'Macros not found')
    macro['load'] = str(math.ceil(avatar.guiSessionProvider.shared.ammo.getGunReloadingState().getTimeLeft()))
    macro['pos'] = square_position.getSquarePosition()
    message = config.data['loadTxt'] % macro
    if len(message) > 0:
         avatar.guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(message, 0)
    else:
        avatar.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.RELOADINGGUN)


@override(PlayerAvatar, 'handleKey')
def new__handleKey(func, self, isDown, key, mods):
    if config.data['enabled'] and config.data['clipLoad']:
        try:
            if CommandMapping.g_instance.isFired(CommandMapping.CMD_RELOAD_PARTIAL_CLIP, key) and isDown and self.isVehicleAlive:
                self.guiSessionProvider.shared.ammo.reloadPartialClip(self)
                callback(0.5, partial(onReload, self))
                return True
        except StandardError:
            traceback.print_exc()
    func(self, isDown, key, mods)


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

# limit of lines in battle
@override(messenger_view, '_makeSettingsVO')
def new__makeSettingsVO(func, self):
    makeSettingsVO = func(self)
    makeSettingsVO['numberOfMessagesInHistory'] = config.data['maxChatLines']
    return makeSettingsVO

# remove camara limits
# @override(gun_marker_ctrl, '_setupGunMarkerSizeLimits')
# def _setupGunMarkerSizeLimits(func, self, scale=None):
#    args = func(self, scale)
#    if not config.data['enabled'] and config.data['camLimits']:
#        return
#    newLimits = (1.0, args[1])
#    self.sizeConstraint = newLimits
#    return newLimits


# PlayerSatisfactionWidget/ShowRateSatisfactionCmp
@override(ShowRateSatisfactionCmp, '_convert')
def new_showRateSatisfactionCmp(func, self, value, reusable):
    if not config.data.get('showPlayerSatisfactionWidget', True):
        return False
    return func(self, value, reusable)


@adisp_process
def changeValue(vehicle, value):
    yield VehicleAutoBattleBoosterEquipProcessor(vehicle, value).request()


def onVehicleChanged(vehicle):
    if not config.data['enabled'] and not config.data['directivesOnlyFromStorage']:
        return
    if vehicle is None or vehicle.isLocked or vehicle.isInBattle:
        return
    if not hasattr(vehicle, 'battleBoosters') or vehicle.battleBoosters is None:
        logDebug(config.ID, True, 'No battle boosters available for this vehicle: {vehicle}', vehicle=vehicle.userName)
        return
    is_auto = vehicle.isAutoBattleBoosterEquip()
    boosters = vehicle.battleBoosters.installed.getItems()
    for battleBooster in boosters:
        value = battleBooster.inventoryCount > 0
        if value != is_auto:
            changeValue(vehicle, value)
            logInfo(config.ID, 'VehicleAutoBattleBoosterEquipProcessor: value={} vehicle={}, booster={}', value, vehicle.userName, battleBooster.userName)


def onGuiCacheSyncCompleted(_):
    _cache.clear()
    users = storage_getter('users')().getList(_ContactsCategories().getCriteria())
    _cache.update(user._userID for user in users if not user.isIgnored())


g_playerEvents.onGuiCacheSyncCompleted += onGuiCacheSyncCompleted
g_events.onVehicleChangedDelayed += onVehicleChanged

def fini():
    g_events.onVehicleChangedDelayed -= onVehicleChanged
