# -*- coding: utf-8 -*-
import datetime
import locale

# import gui.shared.tooltips.vehicle as tooltips
from CurrentVehicle import g_currentVehicle
from HeroTank import HeroTank
from account_helpers.settings_core.settings_constants import GAME
from comp7.gui.impl.lobby.tournaments_widget import TournamentsWidgetComponent
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from gui.Scaleform.daapi.view.lobby.hangar.ammunition_panel import AmmunitionPanel
from gui.Scaleform.daapi.view.lobby.hangar.daily_quest_widget import BaseQuestsWidgetComponent
from gui.Scaleform.daapi.view.lobby.hangar.entry_points.event_entry_points_container import EventEntryPointsContainer
from gui.Scaleform.daapi.view.lobby.header.LobbyHeader import LobbyHeader
from gui.Scaleform.daapi.view.lobby.messengerBar.NotificationListButton import NotificationListButton
from gui.Scaleform.daapi.view.lobby.messengerBar.messenger_bar import MessengerBar
from gui.Scaleform.daapi.view.lobby.messengerBar.session_stats_button import SessionStatsButton
from gui.Scaleform.daapi.view.lobby.profile.ProfileTechnique import ProfileTechnique
from gui.Scaleform.daapi.view.lobby.rankedBattles.ranked_battles_results import RankedBattlesResults
from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import _TechTreeDataProvider
from gui.Scaleform.daapi.view.login.LoginView import LoginView
from gui.Scaleform.daapi.view.meta.MessengerBarMeta import MessengerBarMeta
from gui.Scaleform.locale.RES_ICONS import RES_ICONS
# from gui.Scaleform.locale.STORAGE import STORAGE
from gui.game_control.AwardController import ProgressiveItemsRewardHandler
from gui.game_control.PromoController import PromoController
from gui.game_control.achievements_earning_controller import EarningAnimationCommand
from gui.impl import backport
from gui.impl.gen import R
from gui.impl.lobby.lootbox_system.base.entry_point import LootBoxSystemEntryPoint
from gui.promo.hangar_teaser_widget import TeaserViewer
from gui.shared.personality import ServicesLocator
# from gui.shared.tooltips import getUnlockPrice
from helpers import dependency # , i18n
from helpers.time_utils import getTimeDeltaFromNow, makeLocalServerTime, ONE_DAY, ONE_HOUR, ONE_MINUTE
from messenger.gui.Scaleform.data.ChannelsCarouselHandler import ChannelsCarouselHandler
from messenger.gui.Scaleform.lobby_entry import LobbyEntry
from notification.NotificationListView import NotificationListView
from skeletons.account_helpers.settings_core import ISettingsCore
from vehicle_systems.tankStructure import ModelStates
from gui.impl.lobby.battle_pass.battle_pass_entry_point_view import BattlePassEntryPointComponent

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, callback, isReplay, logDebug, cancelCallback, calculate_version, logError, overrideStaticMethod
from DriftkingsInject import g_events, CyclicTimerEvent


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.callback = None
        self.macros = {}
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '3.7.0 (%(file_compile_date)s)'
        self.author = 'orig by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'autoLogin': True,
            # 'showXpToUnlockVeh': False,
            'showReferralButton': False,
            'showGeneralChatButton': True,
            'showPromoPremVehicle': False,
            'showPopUpMessages': False,
            'showUnreadCounter': True,
            'showRankedBattleResults': False,
            'showButton': False,
            'showAchievementPopups': False,
            'showBattleCount': True,
            'showDailyQuestWidget': False,
            'showProgressiveDecalsWindow': False,
            'showEventBanner': True,
            'showHangarPrestigeWidget': False,
            'showProfilePrestigeWidget': True,
            'showWotPlusButton': False,
            'showEventTournamentWidget': True,
            'showBuyPremiumButton': True,
            'showPremiumShopButton': True,
            'showButtonCounters': True,
            'allowExchangeXPInTechTree': True,
            'allowChannelButtonBlinking': True,
            'premiumTime': False,
            'lootBoxesWidget': False,
            'hideBtnCounters': False,
            'fieldMail': True,
            'clock': True,
            'showBattlePassWidget': True,
            'customClockFormat': False,
            'text': '<font face=\'$FieldFont\' color=\'#959688\'><textformat leading=\'-38\'><font size=\'32\'>\t   %H:%M:%S</font>\n</textformat><textformat rightMargin=\'85\' leading=\'-2\'>%A\n<font size=\'15\'>%d %b %Y</font></textformat></font>',
            'customClockText': '<font face=\'$FieldFont\' color=\'#FF9900\'><textformat leading=\'-38\'><font size=\'32\'>\t   %H:%M:%S</font>\n</textformat><textformat rightMargin=\'85\' leading=\'-2\'>%A\n<font size=\'15\'>%d %b %Y</font></textformat></font>',
            'panel': {
                'position': {'x': -40.0, 'y': 55.0},
                'width': 210,
                'height': 50,
                'shadow': {'distance': 0, 'angle': 0, 'strength': 0.5, 'quality': 3},
                'alignX': 'right',
                'alignY': 'top'
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_autoLogin_text': 'Automatic Login',
            'UI_setting_autoLogin_tooltip': 'Automatically log into the game',
            'UI_setting_clock_text': 'Clock Display',
            'UI_setting_clock_tooltip': 'Show clock in login screen and hangar',
            'UI_setting_customClockFormat_text': 'Custom Clock Format',
            'UI_setting_customClockFormat_tooltip': 'Use custom color and format for the clock display',
            'UI_setting_showButtonCounters_text': 'Button Counters',
            'UI_setting_showButtonCounters_tooltip': 'Show/hide notification counters on buttons',
            'UI_setting_hideBtnCounters_text': 'Disable tooltips',
            'UI_setting_hideBtnCounters_tooltip': (
                        '<img src=\'img://gui/maps/uiKit/dialogs/icons/alert.png\' width=\'16\' height=\'16\'>' +
                        '<font color=\'#FF0000\'>To enable/disable you need to restart the game.</font>' +
                        '<img src=\'img://gui/maps/uiKit/dialogs/icons/alert.png\' width=\'16\' height=\'16\'>'),
            'UI_setting_showWotPlusButton_text': 'WoT Plus Button',
            'UI_setting_showWotPlusButton_tooltip': 'Show/hide WoT Plus subscription button',
            'UI_setting_showBuyPremiumButton_text': 'Premium Account Button',
            'UI_setting_showBuyPremiumButton_tooltip': 'Show/hide premium account purchase button',
            'UI_setting_showPremiumShopButton_text': 'Premium Shop',
            'UI_setting_showPremiumShopButton_tooltip': 'Show/hide premium shop button',
            'UI_setting_premiumTime_text': 'Premium Time Display',
            'UI_setting_premiumTime_tooltip': 'Show detailed premium account time remaining',
            'UI_setting_showReferralButton_text': 'Referral Program Button',
            'UI_setting_showReferralButton_tooltip': 'Show/hide the Referral Program button',
            'UI_setting_showGeneralChatButton_text': 'General Chat',
            'UI_setting_showGeneralChatButton_tooltip': 'Show/hide the General Chat button',
            'UI_setting_showPromoPremVehicle_text': 'Premium Vehicle Preview',
            'UI_setting_showPromoPremVehicle_tooltip': 'Show/hide premium vehicle previews in hangar',
            'UI_setting_showPopUpMessages_text': 'Popup Notifications',
            'UI_setting_showPopUpMessages_tooltip': 'Show/hide popup notification messages',
            'UI_setting_showUnreadCounter_text': 'Notification Counter',
            'UI_setting_showUnreadCounter_tooltip': 'Show/hide unread notification counters',
            'UI_setting_showRankedBattleResults_text': 'Ranked Battle Results',
            'UI_setting_showRankedBattleResults_tooltip': 'Show/hide ranked battle results window',
            'UI_setting_showButton_text': 'Statistics Button',
            'UI_setting_showButton_tooltip': 'Show/hide the session statistics button',
            'UI_setting_showBattleCount_text': 'Battle Counter',
            'UI_setting_showBattleCount_tooltip': 'Show/hide the battle count display',
            'UI_setting_showDailyQuestWidget_text': 'Daily Missions',
            'UI_setting_showDailyQuestWidget_tooltip': 'Show/hide daily mission widget in hangar',
            'UI_setting_showProgressiveDecalsWindow_text': 'Progressive Decals',
            'UI_setting_showProgressiveDecalsWindow_tooltip': 'Show/hide progressive decal notifications',
            'UI_setting_showEventBanner_text': 'Event Banners',
            'UI_setting_showEventBanner_tooltip': 'Show/hide event banners in hangar',
            'UI_setting_showHangarPrestigeWidget_text': 'Hangar Prestige Display',
            'UI_setting_showHangarPrestigeWidget_tooltip': 'Show/hide elite level widget in hangar',
            'UI_setting_showProfilePrestigeWidget_text': 'Profile Prestige Display',
            'UI_setting_showProfilePrestigeWidget_tooltip': 'Show/hide elite level widget in profile',
            'UI_setting_allowExchangeXPInTechTree_text': 'XP Exchange in Tech Tree',
            'UI_setting_allowExchangeXPInTechTree_tooltip': 'Enable XP to gold exchange in tech tree',
            'UI_setting_allowChannelButtonBlinking_text': 'Allow Channel Button Blinking',
            'UI_setting_allowChannelButtonBlinking_tooltip': 'Allow messenger bar channel (clan or private chat) button blinking.',
            # 'UI_setting_showXpToUnlockVeh_text': 'Vehicle XP Requirements',
            # 'UI_setting_showXpToUnlockVeh_tooltip': 'Show required XP to unlock vehicles',
            'UI_setting_lootBoxesWidget_text': 'Lootbox Widget',
            'UI_setting_lootBoxesWidget_tooltip': 'Show/hide lootbox widget in hangar',
            'UI_setting_showEventTournamentWidget_text': 'Event Tournament Widget',
            'UI_setting_showEventTournamentWidget_tooltip': 'Show/hide event tournaments widget in hangar.',
            'UI_setting_showAchievementPopups_text': 'Achievement Popups',
            'UI_setting_showAchievementPopups_tooltip': 'Show/hide Achievement Popups.',
            'UI_setting_fieldMail_text': 'Field Mail',
            'UI_setting_fieldMail_tooltip': 'Show/hide Field Mail.',
            'UI_setting_showBattlePassWidget_text': 'Battle Pass Widget',
            'UI_setting_showBattlePassWidget_tooltip': 'Show/hide Battle Pass widget in hangar.'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('autoLogin'),
                self.tb.createControl('clock'),
                self.tb.createControl('customClockFormat'),
                self.tb.createControl('allowExchangeXPInTechTree'),
                self.tb.createControl('allowChannelButtonBlinking'),
                # self.tb.createControl('showXpToUnlockVeh'),
                self.tb.createControl('showBattleCount'),
                self.tb.createControl('showButton'),
                self.tb.createControl('showGeneralChatButton'),
                self.tb.createControl('showPopUpMessages'),
                self.tb.createControl('lootBoxesWidget'),
                self.tb.createControl('showDailyQuestWidget'),
                self.tb.createControl('showEventBanner'),
                self.tb.createControl('showProgressiveDecalsWindow'),
                self.tb.createControl('showBattlePassWidget')
            ],
            'column2': [
                self.tb.createControl('showPromoPremVehicle'),
                self.tb.createControl('showBuyPremiumButton'),
                self.tb.createControl('showPremiumShopButton'),
                self.tb.createControl('showWotPlusButton'),
                self.tb.createControl('showUnreadCounter'),
                self.tb.createControl('showButtonCounters'),
                self.tb.createControl('hideBtnCounters'),
                self.tb.createControl('showRankedBattleResults'),
                self.tb.createControl('showHangarPrestigeWidget'),
                self.tb.createControl('showProfilePrestigeWidget'),
                self.tb.createControl('showReferralButton'),
                self.tb.createControl('showEventTournamentWidget'),
                self.tb.createControl('showAchievementPopups'),
                self.tb.createControl('fieldMail')
            ]
        }

    def getPremiumLabelText(self, time_delta):
        delta = float(getTimeDeltaFromNow(makeLocalServerTime(time_delta)))
        if delta > ONE_DAY:
            template = '<b><font color=\'#FAFAFA\'>%(days)d {0}. %(hours)02d:%(min)02d:%(sec)02d</font></b>'.format(
                backport.text(R.strings.menu.header.account.premium.days()).replace('.', ''))
        else:
            template = '<b><font color=\'#FAFAFA\'>%(hours)d {0}. %(min)02d:%(sec)02d</font></b>'.format(backport.text(R.strings.menu.header.account.premium.hours()).replace('.', ''))
        self.macros['days'], delta = divmod(delta, ONE_DAY)
        self.macros['hours'], delta = divmod(delta, ONE_HOUR)
        self.macros['min'], self.macros['sec'] = divmod(delta, ONE_MINUTE)
        return template % self.macros

    def stopCallback(self):
        if self.callback is not None:
            cancelCallback(self.callback)
            self.callback = None


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


# update vehicle
@override(Hangar, '__onCurrentVehicleChanged')
@override(Hangar, '__updateAll')
def new__changeVehicle(func, *args, **kwargs):
    func(*args, **kwargs)
    g_events.onVehicleChanged()
    callback(1.0, g_events.onVehicleChangedDelayed, g_currentVehicle.item)


# hide referral program button
@override(MessengerBarMeta, 'as_setInitDataS')
def new__setInitDataS(func, self, data):
    if config.data.get('enabled', True) and not config.data.get('showReferralButton', True) and (
            'isReferralEnabled' in data):
        data['isReferralEnabled'] = False
    return func(self, data)


# hide button counters in lobby header
@override(LobbyHeader, '__setCounter')
def new__setCounter(func, *args, **kwargs):
    if not config.data.get('enabled', True) or config.data.get('hideBtnCounters', False):
        return None
    return func(*args, **kwargs)


# hide shared chat button
@override(LobbyEntry, '_LobbyEntry__handleLazyChannelCtlInited')
def new__handleLazyChannelCtlInited(func, self, event):
    if config.data.get('enabled', True) and not config.data.get('showGeneralChatButton', True):
        ctx = event.ctx
        controller = ctx.get('controller')
        if controller is None:
            logDebug(config.ID, True, 'Controller is not defined {}', ctx)
            return
        else:
            ctx.clear()
            return
    return func(self, event)


# hide premium vehicle on the background in the hangar
@override(HeroTank, 'recreateVehicle')
def new__recreateVehicle(func, self, typeDescriptor=None, state=ModelStates.UNDAMAGED, _callback=None, outfit=None):
    if config.data.get('enabled', True) and not config.data.get('showPromoPremVehicle', True):
        return
    func(self, typeDescriptor, state, _callback, outfit)


# hide display pop-up messages in the hangar
@override(TeaserViewer, 'show')
def new__show(func, self, teaserData, promoCount):
    if config.data.get('enabled', True) and not config.data.get('showPopUpMessages', True):
        return
    func(self, teaserData, promoCount)


# hide display unread notifications counter in the menu
@override(PromoController, 'getPromoCount')
def new__getPromoCount(func, self):
    if config.data.get('enabled', True) and not config.data.get('showUnreadCounter', True):
        return 0
    return func(self)


# disable field mail tips
@override(PromoController, '__tryToShowTeaser')
def new__tryToShowTeaser(func, *args):
    return None if config.data.get('enabled', True) and not config.data.get('fieldMail', True) else func(*args)


@override(PromoController, '__needToGetTeasersInfo')
def _needToGetTeasersInfo(func, *args):
    return False if config.data['enabled'] and not config.data['fieldMail'] else func(*args)


# hide ranked battle results window
@override(RankedBattlesResults, '_populate')
def new__populate(func, self):
    if config.data.get('enabled', True) and not config.data.get('showRankedBattleResults', True):
        return
    func(self)


# hide display session statistics button
@override(MessengerBar, '_MessengerBar__updateSessionStatsBtn')
def new__updateSessionStatsBtn(func, self):
    if config.data.get('enabled', True) and not config.data.get('showButton', True):
        self.as_setSessionStatsButtonVisibleS(False)
        self._MessengerBar__onSessionStatsBtnOnlyOnceHintHidden(True)
        return
    func(self)


# hide display the counter of spent battles on the button
@override(SessionStatsButton, '_SessionStatsButton__updateBatteleCount')
def new__updateBattleCount(func, self):
    if config.data.get('enabled', True) and not config.data.get('showBattleCount', True):
        return
    func(self)


# hide display widget with daily quests
@override(BaseQuestsWidgetComponent, '_shouldHide')
def new__shouldHide(func, self):
    if config.data.get('enabled', True) and not config.data.get('showDailyQuestWidget', True):
        return True
    return func(self)


# hide display pop-up window when receiving progressive decals
@override(ProgressiveItemsRewardHandler, '_showAward')
def new__showAward(func, self, ctx):
    if config.data.get('enabled', True) and not config.data.get('showProgressiveDecalsWindow', True):
        return
    func(self, ctx)


# hide display banner of various events in the hangar
@override(EventEntryPointsContainer, '_EventEntryPointsContainer__updateEntries')
def new__updateEntries(func, self):
    if config.data.get('enabled', True) and not config.data.get('showEventBanner', True):
        return self.as_updateEntriesS([])
    func(self)


# hide prestige (elite levels) system widget in the hangar
@override(Hangar, 'as_setPrestigeWidgetVisibleS')
def new__setPrestigeWidgetVisibleS(func, self, value):
    if config.data.get('enabled', True) and not config.data.get('showHangarPrestigeWidget', True):
        value = False
    return func(self, value)


# hide prestige (elite levels) system widget in the profile
@override(ProfileTechnique, 'as_setPrestigeVisibleS')
def new__setPrestigeVisibleS(func, self, value):
    if config.data.get('enabled', True) and not config.data.get('showProfilePrestigeWidget', True):
        value = False
    return func(self, value)


# hide premium account, shop and WoT Plus buttons
LOBBY_HEADER_BUTTON_TO_CONFIG = {
    LobbyHeader.BUTTONS.WOT_PLUS: 'showWotPlusButton',
    LobbyHeader.BUTTONS.PREM: 'showBuyPremiumButton',
    LobbyHeader.BUTTONS.PREMSHOP: 'showPremiumShopButton'
}


@override(LobbyHeader, 'as_setHeaderButtonsS')
def new__setHeaderButtonsS(func, self, buttons):
    if config.data.get('enabled', True):
        for button, key in LOBBY_HEADER_BUTTON_TO_CONFIG.iteritems():
            if not config.data.get('%s' % key, True) and button in buttons:
                buttons.remove(button)
    return func(self, buttons)


# hide button counters in lobbyHeader
@override(LobbyHeader, '_LobbyHeader__setCounter')
def new__setCounter(func, self, alias, counter=None):
    if config.data.get('enabled', True) and not config.data.get('showButtonCounters', True):
        return
    return func(self, alias, counter)


# hide button counters on customization button
@override(AmmunitionPanel, 'as_setCustomizationBtnCounterS')
def new__setCustomizationBtnCounterS(func, self, value):
    if config.data.get('enabled', True) and not config.data.get('showButtonCounters', True):
        value = 0
    return func(self, value)


# hide counter on service channel button
@override(NotificationListButton, '_NotificationListButton__setState')
def new__setState(func, self, count):
    if config.data.get('enabled', True) and not config.data.get('showButtonCounters', True):
        return
    return func(self, count)


# hide counters in service channel
@override(NotificationListView, '_NotificationListView__updateCounters')
def new__updateCounters(func, self):
    if config.data.get('enabled', True) and not config.data.get('showButtonCounters', True):
        return
    return func(self)


# hide achievement popups
@override(EarningAnimationCommand, 'execute')
def new__execute(base, self):
    if config.data.get('enabled', True) and config.data.get('showAchievementPopups', True):
        base(self)
        return
    self.release()


# Auto-Login
class AutoLoginHandler:
    def __init__(self):
        self.firstTime = False

    def auto_login(self, login):
        if not self.firstTime:
            self.firstTime = True
            if config.data['enabled'] and config.data['autoLogin']:
                callback(0, login.as_doAutoLoginS)


autoLogin = AutoLoginHandler()


@override(LoginView, '_populate')
def new__LoginViewPopulate(func, self):
    func(self)
    if not isReplay() and not self.loginManager.wgcAvailable:
        autoLogin.auto_login(self)


# Show Xp To Unlock Veh.
# @override(tooltips.StatusBlockConstructor, 'construct')
# def new__construct(func, self):
#    result = func(self)
#    if result and config.data['enabled'] and config.data['showXpToUnlockVeh']:
#        techTreeNode = self.configuration.node
#        vehicle = self.vehicle
#        isUnlocked = vehicle.isUnlocked
#        parentCD = int(techTreeNode.unlockProps.parentID) if techTreeNode is not None else None
#        if parentCD is not None:
#            isAvailable, cost, need, defCost, discount = getUnlockPrice(vehicle.intCD, parentCD, vehicle.level)
#            if isAvailable and not isUnlocked and need > 0 and techTreeNode is not None:
#                icon = '<img src=\'{}\' vspace=\'{}\''.format(RES_ICONS.MAPS_ICONS_LIBRARY_XPCOSTICON_1.replace('..', 'img://gui'), -3)
#                template = '<font face=\'$TitleFont\' size=\'14\'><font color=\'#ff2717\'>{}</font> {}</font> {}'
#                # Check if result has the expected structure before trying to modify it
#                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and 'data' in result[0] and isinstance(result[0]['data'], dict):
#                    result[0]['data']['text'] = template.format(i18n.makeString(STORAGE.BLUEPRINTS_CARD_CONVERTREQUIRED), need, icon)
#    return result


@override(_TechTreeDataProvider, 'getAllVehiclePossibleXP')
def new__getAllVehiclePossibleXP(func, self, nodeCD, unlockStats):
    try:
        if config.data.get('enabled', True) and not config.data.get('allowExchangeXPInTechTree', True):
            return unlockStats.getVehTotalXP(nodeCD)
    except Exception:
        logError(config.ID, '_TechTreeDataProvider_getAllVehiclePossibleXP')
    return func(self, nodeCD, unlockStats)


# hide lootBoxes widget in tank carousel in hangar
@overrideStaticMethod(LootBoxSystemEntryPoint, 'getIsActive')
def new__getIsActive(func, state):
    if config.data.get('enabled', True) and not config.data.get('lootBoxesWidget', True):
        return False
    return func(state)


@override(Hangar, 'as_updateCarouselEventEntryStateS')
def new__updateCarouselEventEntryStateS(func, self, isVisible):
    if config.data.get('enabled', True) and not config.data.get('lootBoxesWidget', True):
        isVisible = False
    return func(self, isVisible)


# hide lootBoxes widget in hangar
@override(Hangar, 'as_setEventTournamentBannerVisibleS')
def new__setEventTournamentBannerVisibleS(func, self, alias, visible):
    if config.data.get('enabled', True) and not config.data.get('showEventTournamentWidget', True):
        visible = False
    return func(self, alias, visible)


# Destroy widget if hidden
@override(TournamentsWidgetComponent, '_makeInjectView')
def new__makeInjectView(func, self):
    if config.data.get('enabled', True) and not config.data.get('showEventTournamentWidget', True):
        self.destroy()
        return
    return func(self)


# Hide Battle Pass Widget
@override(BattlePassEntryPointComponent, '_makeInjectView')
def new__makeBPInjectView(func, self):
    if config.data.get('enabled', True) and not config.data.get('showBattlePassWidget', True):
        self.destroy()
        return
    return func(self)


# PremiumTime
@override(LobbyHeader, 'as_setPremiumParamsS')
def new__startCallback(func, self, data):
    config.stopCallback()
    if config.data['enabled'] and config.data['premiumTime'] and self.itemsCache.items.stats.isPremium:
        config.callback = callback(1.0, new__startCallback, func, self, data)
        data['doLabel'] = config.getPremiumLabelText(self.itemsCache.items.stats.activePremiumExpiryTime)
    func(self, data)


@override(LobbyHeader, '_removeListeners')
def new__removeListeners(func, self):
    config.stopCallback()
    return func(self)


# Handlers
@override(ChannelsCarouselHandler, 'addChannel')
def new__addChannel(func, self, channel, lazy=False, isNotified=False):
    if config.data.get('enabled', True) and not config.data.get('allowChannelButtonBlinking', True):
        isNotified = False
    return func(self, channel, lazy, isNotified)


@override(ChannelsCarouselHandler, '_ChannelsCarouselHandler__setItemField')
def new__setItemField(func, self, clientID, key, value):
    if config.data.get('enabled', True) and not config.data.get('allowChannelButtonBlinking', True) and key == 'isNotified':
        value = False
    return func(self, clientID, key, value)


# Hangar Clock
class Flash(object):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self, ID):
        self.ID = ID
        self.__isLobby = True
        self.isBattle = False
        self.updateCallback = None
        self.timerEvent = CyclicTimerEvent(1.0, self.updateTimeData)
        self.startTimer()
        self.setup()
        COMPONENT_EVENT.UPDATED += self.__updatePosition

    def startTimer(self):
        if config.data.get('enabled') and config.data.get('clock'):
            self.timerEvent.start()

    def stopTimer(self):
        self.timerEvent.stop()

    def setup(self):
        panel_config = {'x': config.data['panel']['position']['x'], 'y': config.data['panel']['position']['y'], 'width': config.data['panel']['width'], 'height': config.data['panel']['height'], 'alignX': config.data['panel'].get('alignX', COMPONENT_ALIGN.RIGHT), 'alignY': config.data['panel'].get('alignY', COMPONENT_ALIGN.TOP), 'drag': False, 'border': False, 'limit': False}
        g_guiFlash.createComponent(self.ID, COMPONENT_TYPE.LABEL, panel_config, battle=False, lobby=True)
        self.setShadow()

    def onApplySettings(self):
        panel_config = dict(config.data['panel']['position'], width=config.data['panel']['width'], height=config.data['panel']['height'], alignX=config.data['panel']['alignX'], alignY=config.data['panel']['alignY'], drag=False, border=False)
        g_guiFlash.updateComponent(self.ID, panel_config)

    def setShadow(self):
        g_guiFlash.updateComponent(self.ID, {'shadow': config.data['panel']['shadow']})

    def __updatePosition(self, alias, data):
        if alias != self.ID:
            return
        config.onApplySettings({'panel': {'position': data}})

    def cleanup(self):
        self.stopTimer()
        if self.updateCallback:
            self.updateCallback = cancelCallback(self.updateCallback)
        COMPONENT_EVENT.UPDATED -= self.__updatePosition
        g_guiFlash.destroyComponent(self.ID)

    @property
    def isLobby(self):
        return self.__isLobby

    @isLobby.setter
    def isLobby(self, value):
        self.__isLobby = value
        if self.updateCallback:
            self.updateCallback = cancelCallback(self.updateCallback)
        self.updateCallback = callback(1.0, self.updateTimeData) if not value else self.updateTimeData()

    def updateTimeData(self):
        if not config.data.get('enabled', False) or not config.data.get('clock', False):
            return
        encoding = 'utf-8' if locale.getpreferredencoding() in ('cp65001', 'UTF-8') else locale.getpreferredencoding()
        current_time = datetime.datetime.now()
        weekday_capitalized = current_time.strftime('%A').capitalize()
        if config.data.get('customClockFormat', False):
            format_with_capital = config.data['customClockText'].replace('%A', weekday_capitalized)
        else:
            format_with_capital = config.data['text'].replace('%A', weekday_capitalized)
        current_time_str = current_time.strftime(format_with_capital)
        formatted_time = current_time_str.decode(encoding) if isinstance(current_time_str, str) else current_time_str
        g_guiFlash.updateComponent(self.ID, {'text': formatted_time})
        if not self.__isLobby and self.updateCallback is None:
            self.updateCallback = callback(1.0, self.updateTimeData)


g_flash = None
try:
    from gambiter import g_guiFlash
    from gambiter.flash import COMPONENT_TYPE, COMPONENT_EVENT, COMPONENT_ALIGN
    g_flash = Flash(config.ID)
except ImportError as e:
    logError(config.ID, 'Missing required module: {}', e)
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
