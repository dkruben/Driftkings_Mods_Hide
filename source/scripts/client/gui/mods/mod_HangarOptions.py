# -*- coding: utf-8 -*-
import logging
import traceback
from math import sin, radians
from time import strftime

import ResMgr
import gui.shared.tooltips.vehicle as tooltips
import nations
from Account import PlayerAccount
from CurrentVehicle import g_currentVehicle
from HeroTank import HeroTank
from account_helpers.settings_core.settings_constants import GAME
from constants import ITEM_DEFS_PATH
from gui.Scaleform.daapi.view.common.vehicle_carousel.carousel_data_provider import CarouselDataProvider
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from gui.Scaleform.daapi.view.lobby.hangar.ammunition_panel import AmmunitionPanel
from gui.Scaleform.daapi.view.lobby.hangar.entry_points.event_entry_points_container import EventEntryPointsContainer
from gui.Scaleform.daapi.view.lobby.header.LobbyHeader import LobbyHeader
from gui.Scaleform.daapi.view.lobby.messengerBar.NotificationListButton import NotificationListButton
from gui.Scaleform.daapi.view.lobby.messengerBar.messenger_bar import MessengerBar
from gui.Scaleform.daapi.view.lobby.messengerBar.session_stats_button import SessionStatsButton
from gui.Scaleform.daapi.view.lobby.profile.ProfileTechnique import ProfileTechnique
from gui.Scaleform.daapi.view.lobby.rankedBattles.ranked_battles_results import RankedBattlesResults
from gui.Scaleform.daapi.view.login.LoginView import LoginView
from gui.Scaleform.daapi.view.meta.MessengerBarMeta import MessengerBarMeta
from gui.Scaleform.daapi.view.meta.ModuleInfoMeta import ModuleInfoMeta
from gui.Scaleform.locale.RES_ICONS import RES_ICONS
from gui.Scaleform.locale.STORAGE import STORAGE
from gui.game_control.AwardController import ProgressiveItemsRewardHandler
from gui.game_control.PromoController import PromoController
from gui.impl import backport
from gui.impl.gen import R
from gui.promo.hangar_teaser_widget import TeaserViewer
from gui.shared.formatters import text_styles
from gui.shared.personality import ServicesLocator
from gui.shared.tooltips import formatters, getUnlockPrice
from gui.shared.tooltips.shell import CommonStatsBlockConstructor
from gun_rotation_shared import calcPitchLimitsFromDesc
from helpers import dependency, i18n
from helpers.time_utils import getTimeDeltaFromNow, makeLocalServerTime, ONE_DAY, ONE_HOUR, ONE_MINUTE
from messenger.gui.Scaleform.data.ChannelsCarouselHandler import ChannelsCarouselHandler
from messenger.gui.Scaleform.lobby_entry import LobbyEntry
from notification.NotificationListView import NotificationListView
from shared_utils import safeCancelCallback
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.shared import IItemsCache
from vehicle_systems.tankStructure import ModelStates

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, callback, isReplay, logDebug, cancelCallback, calculate_version, logError, getRegion, overrideStaticMethod
from DriftkingsInject import g_events, CyclicTimerEvent

firstTime = True


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.callback = None
        self.macros = {}
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '3.2.0 (%(file_compile_date)s)'
        self.author = 'orig by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'autoLogin': True,
            'showXpToUnlockVeh': False,
            'showReferralButton': False,
            'showGeneralChatButton': True,
            'showPromoPremVehicle': False,
            'showPopUpMessages': False,
            'showUnreadCounter': True,
            'showRankedBattleResults': False,
            'showButton': False,
            'showBattleCount': True,
            'showDailyQuestWidget': False,
            'showProgressiveDecalsWindow': False,
            'showEventBanner': True,
            'showHangarPrestigeWidget': False,
            'showProfilePrestigeWidget': True,
            'showWotPlusButton': False,
            'showBuyPremiumButton': True,
            'showPremiumShopButton': True,
            'showButtonCounters': True,
            'allowExchangeXPInTechTree': True,
            'allowChannelButtonBlinking': True,
            'premiumTime': False,
            'lootboxesWidget': False,
            'clock': True,
            'text': '<font face=\'$FieldFont\' color=\'#959688\'><textformat leading=\'-38\'><font size=\'32\'>\t   %H:%M:%S</font>\n</textformat><textformat rightMargin=\'85\' leading=\'-2\'>%A\n<font size=\'15\'>%d %b %Y</font></textformat></font>',
            'panel': {
                'position':{'x': -10.0, 'y': 49.0},
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
            'UI_setting_showWotPlusButton_text': 'WoT Plus Button',
            'UI_setting_showWotPlusButton_tooltip': 'Show/hide WoT Plus subscription button',
            'UI_setting_showBuyPremiumButton_text': 'Premium Account Button',
            'UI_setting_showBuyPremiumButton_tooltip': 'Show/hide premium account purchase button',
            'UI_setting_showPremiumShopButton_text': 'Premium Shop',
            'UI_setting_showPremiumShopButton_tooltip': 'Show/hide premium shop button',
            'UI_setting_showButtonCounters_text': 'Button Counters',
            'UI_setting_showButtonCounters_tooltip': 'Show/hide notification counters on buttons',
            'UI_setting_allowExchangeXPInTechTree_text': 'XP Exchange in Tech Tree',
            'UI_setting_allowExchangeXPInTechTree_tooltip': 'Enable XP to gold exchange in tech tree',
            'UI_setting_allowChannelButtonBlinking_text': 'Allow Channel Button Blinking',
            'UI_setting_allowChannelButtonBlinking_tooltip': 'Allow messenger bar channel (clan or private chat) button blinking.',
            'UI_setting_showXpToUnlockVeh_text': 'Vehicle XP Requirements',
            'UI_setting_showXpToUnlockVeh_tooltip': 'Show required XP to unlock vehicles',
            'UI_setting_premiumTime_text': 'Premium Time Display',
            'UI_setting_premiumTime_tooltip': 'Show detailed premium account time remaining',
            'UI_setting_lootboxesWidget_text': 'Lootbox Widget',
            'UI_setting_lootboxesWidget_tooltip': 'Show/hide lootbox widget in hangar',
            'UI_setting_clock_text': 'Clock Display',
            'UI_setting_clock_tooltip': 'Show clock in login screen and hangar',
            'UI_techTree_shootingRadius': 'Firing Range',
            'UI_techTree_m': 'Mt'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('allowExchangeXPInTechTree'),
                self.tb.createControl('allowChannelButtonBlinking'),
                self.tb.createControl('autoLogin'),
                self.tb.createControl('clock'),
                self.tb.createControl('lootboxesWidget'),
                self.tb.createControl('showBattleCount'),
                self.tb.createControl('showButton'),
                self.tb.createControl('showDailyQuestWidget'),
                self.tb.createControl('showEventBanner'),
                self.tb.createControl('showGeneralChatButton'),
                self.tb.createControl('showPopUpMessages'),
                self.tb.createControl('showProgressiveDecalsWindow')
            ],
            'column2': [
                self.tb.createControl('showPromoPremVehicle'),
                self.tb.createControl('showRankedBattleResults'),
                self.tb.createControl('showReferralButton'),
                self.tb.createControl('showUnreadCounter'),
                self.tb.createControl('showButtonCounters'),
                self.tb.createControl('showBuyPremiumButton'),
                self.tb.createControl('showEventBanner'),
                self.tb.createControl('showHangarPrestigeWidget'),
                self.tb.createControl('showPremiumShopButton'),
                self.tb.createControl('showProfilePrestigeWidget'),
                self.tb.createControl('showWotPlusButton'),
                self.tb.createControl('showXpToUnlockVeh')
            ]
        }

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)
        if self.data['enabled']:
            ServicesLocator.settingsCore.onSettingsChanged({GAME.CAROUSEL_TYPE: None, GAME.DOUBLE_CAROUSEL_TYPE: None})

    def getPremiumLabelText(self, time_delta):
        delta = float(getTimeDeltaFromNow(makeLocalServerTime(time_delta)))
        if delta > ONE_DAY:
            template = '<b><font color=\'#FAFAFA\'>%(days)d {0}. %(hours)02d:%(min)02d:%(sec)02d</font></b>'.format(backport.text(R.strings.menu.header.account.premium.days()).replace('.', ''))
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
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


# update vehicle
@override(Hangar, '__onCurrentVehicleChanged')
@override(Hangar, '__updateAll')
def new__changeVehicle(func, *args, **kwargs):
    func(*args, **kwargs)
    g_events.onVehicleChanged()
    callback(1.0, g_events.onVehicleChangedDelayed, g_currentVehicle.item)


# Hangar
# hide referral program button
@override(MessengerBarMeta, 'as_setInitDataS')
def new__setInitDataS(func, self, data):
    if config.data['enabled'] and config.data['showReferralButton'] and ('isReferralEnabled' in data):
        data['isReferralEnabled'] = False
    return func(self, data)


# hide shared chat button
@override(LobbyEntry, '_LobbyEntry__handleLazyChannelCtlInited')
def new__handleLazyChannelCtlInited(func, self, event):
    if config.data['enabled'] and config.data['showGeneralChatButton']:
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
def new__recreateVehicle(func, self, typeDescriptor=None, state=ModelStates.UNDAMAGED, _callback=None, outfit=None):
    if config.data.get('enabled', True) and config.data.get('showPromoPremVehicle', True):
        return
    func(self, typeDescriptor, state, _callback, outfit)


# hide display pop-up messages in the hangar
@override(TeaserViewer, 'show')
def new__show(func, self, teaserData, promoCount):
    if config.data['enabled'] and config.data['showPopUpMessages']:
        return
    func(self, teaserData, promoCount)


# hide display unread notifications counter in the menu
@override(PromoController, 'getPromoCount')
def new__getPromoCount(func, self):
    if config.data['enabled'] and config.data['showUnreadCounter']:
        return
    func(self)


# hide ranked battle results window
@override(RankedBattlesResults, '_populate')
def new__populate(func, self):
    if config.data['enabled'] and config.data['showRankedBattleResults']:
        return
    func(self)


# hide display session statistics button
@override(MessengerBar, '_MessengerBar__updateSessionStatsBtn')
def new__updateSessionStatsBtn(func, self):
    if config.data['enabled'] and config.data['showButton']:
        self.as_setSessionStatsButtonVisibleS(False)
        self._MessengerBar__onSessionStatsBtnOnlyOnceHintHidden(True)
        return
    func(self)


# hide display the counter of spent battles on the button
@override(SessionStatsButton, '_SessionStatsButton__updateBatteleCount')
def new__updateBatteleCount(func, self):
    if config.data['enabled'] and config.data['showBattleCount']:
        return
    func(self)


# hide display widget with daily quests
def new__shouldHide(func, self):
    if not config.data.get('enabled', True) and not config.data.get('showDailyQuestWidget', True):
        return True
    return func(self)


# hide display pop-up window when receiving progressive decals
@override(ProgressiveItemsRewardHandler, '_showAward')
def new__showAward(func, self, ctx):
    if config.data['enabled'] and config.data['showProgressiveDecalsWindow']:
        return
    func(self, ctx)


# hide display banner of various events in the hangar
@override(EventEntryPointsContainer, 'as_updateEntriesS')
def new__updateEntries(func, self, data):
    if config.data['enabled'] and config.data['showEventBanner']:
        return func(self, [])
    return func(self, data)


# hide prestige (elite levels) system widget in the hangar
@override(Hangar, 'as_setPrestigeWidgetVisibleS')
def new__setPrestigeWidgetVisibleS(func, self, value):
    if config.data['enabled'] and config.data['showHangarPrestigeWidget']:
        value = False
    return func(self, value)


# hide prestige (elite levels) system widget in the profile
@override(ProfileTechnique, 'as_setPrestigeVisibleS')
def new__setPrestigeVisibleS(func, self, value):
    if config.data['enabled'] and config.data['showProfilePrestigeWidget']:
        value = False
    return func(self, value)


# hide premium account, shop and WoT Plus buttons
LOBBY_HEADER_BUTTON_TO_CONFIG = {
    LobbyHeader.BUTTONS.WOT_PLUS: 'showWotPlusButton',
    LobbyHeader.BUTTONS.PREM: 'showBuyPremiumButton',
    LobbyHeader.BUTTONS.PREMSHOP: 'showPremiumShopButton'
}


def new__setHeaderButtonsS(func, self, buttons):
    for button, key in LOBBY_HEADER_BUTTON_TO_CONFIG.iteritems():
        if not config.data.get('%s' % key, True) and button in buttons:
            buttons.remove(button)
    return func(self, buttons)


# hide button counters in lobbyHeader
@override(LobbyHeader, '_LobbyHeader__setCounter')
def new__setCounter(func, self, alias, counter=None):
    if config.data['enabled'] and config.data['showButtonCounters']:
        return
    return func(self, alias, counter)


# hide button counters on customization button
@override(AmmunitionPanel, 'as_setCustomizationBtnCounterS')
def new__setCustomizationBtnCounterS(func, self, value):
    if config.data['enabled'] and config.data['showButtonCounters']:
        value = 0
    return func(self, value)


# hide counter on service channel button
@override(NotificationListButton, '_NotificationListButton__setState')
def new__setState(func, self, count):
    if config.data['enabled'] and config.data['showButtonCounters']:
        return
    return func(self, count)


# hide counters in service channel
@override(NotificationListView, '_NotificationListView__updateCounters')
def new__updateCounters(func, self):
    if config.data['enabled'] and config.data['showButtonCounters']:
        return
    return func(self)


# Auto-Login
def new__LoginViewPopulate(func, self):
    func(self)
    if not isReplay() and not self.loginManager.wgcAvailable:
        global firstTime
        if firstTime:
            firstTime = False
            if config.data['enabled'] and config.data['autoLogin']:
                callback(0, self.as_doAutoLoginS)


# Show Xp To Unlock Veh.
@override(tooltips.StatusBlockConstructor, 'construct')
def new__construct(func, self):
    block = func(self)
    if block and config.data['enabled'] and config.data['showXpToUnlockVeh']:
        try:
            techTreeNode = self.configuration.node
            vehicle = self.vehicle
            isUnlocked = vehicle.isUnlocked
            parentCD = int(techTreeNode.unlockProps.parentID) if techTreeNode is not None else None
            if parentCD is not None:
                isAvailable, cost, need, defCost, discount = getUnlockPrice(vehicle.intCD, parentCD, vehicle.level)
                if isAvailable and not isUnlocked and need > 0 and techTreeNode is not None:
                    if isAvailable and not isUnlocked and need > 0 and techTreeNode is not None:
                        icon = '<img src=\'{}\' vspace=\'{}\''.format(RES_ICONS.MAPS_ICONS_LIBRARY_XPCOSTICON_1.replace('..', 'img://gui'), -3)
                        template = '<font face=\'$TitleFont\' size=\'14\'><font color=\'#ff2717\'>{}</font> {}</font> {}'
                        block[0]['data']['text'] = template.format(i18n.makeString(STORAGE.BLUEPRINTS_CARD_CONVERTREQUIRED), need, icon)
            return block
        except Exception:
            logging.getLogger('Driftkings/HangarOptions').exception('new__construct')
            return block
    else:
        return block


# TechTree
class RangeCalculator:
    def __init__(self, turret, gun, nation, v_class):
        self.turret = turret
        self.gun = gun
        self.nation = nation
        self.v_class = v_class

    def get_ranges(self):
        vision_radius = int(self.turret.circularVisionRadius)
        firing_radius = 0
        arty_radius = 0
        # Gun-dependent
        shots = self.gun.shots
        for shot in shots:
            radius = int(shot.maxDistance)
            if firing_radius < radius:
                firing_radius = radius
            if self.v_class == 'SPG' and shot.shell.kind == 'HIGH_EXPLOSIVE':
                try:
                    pitch_limit_rad = min(radians(45), -calcPitchLimitsFromDesc(0, self.gun.pitchLimits)[0])
                except StandardError:
                    min_pitch = radians(-45)
                    for gun in self.turret.guns:
                        if gun.name == self.gun.name:
                            min_pitch = gun.pitchLimits['minPitch'][0][1]
                            break
                    pitch_limit_rad = min(radians(45), -min_pitch)
                radius = int(pow(shot.speed, 2) * sin(2 * pitch_limit_rad) / shot.gravity)
                if arty_radius < radius:
                    arty_radius = radius
        return vision_radius, firing_radius, arty_radius


# add shooting range in gun info window for SPG/machine guns
@override(ModuleInfoMeta, 'as_setModuleInfoS')
def new__setModuleInfoS(func, self, moduleInfo):
    try:
        if moduleInfo['type'] == 'vehicleGun':
            veh_id = self._ModuleInfoWindow__vehicleDescr.type.compactDescr
            itemsCache = dependency.instance(IItemsCache)
            vehicle = itemsCache.items.getItemByCD(veh_id)
            _gun = itemsCache.items.getItemByCD(self.moduleCompactDescr).descriptor
            turret = self._ModuleInfoWindow__vehicleDescr.turret
            range_calculator = RangeCalculator(turret, _gun, vehicle.nationName, vehicle.type)
            viewRange, shellRadius, artiRadius = range_calculator.get_ranges()
            if vehicle.type == 'SPG':
                moduleInfo['parameters']['params'].append({'type': '<h>' + config.i18n['UI_techTree_shootingRadius'] + ' <p>' + config.i18n['UI_techTree_m'] + '</p></h>','value': '<h>' + str(artiRadius) + '</h>'})
            elif shellRadius < 707:
                moduleInfo['parameters']['params'].append({'type': '<h>' + config.i18n['UI_techTree_shootingRadius'] + ' <p>' + config.i18n['UI_techTree_m'] + '</p></h>', 'value': '<h>' + str(shellRadius) + '</h>'})
    except StandardError:
        traceback.print_exc()

    return func(self, moduleInfo)


def new__getAllVehiclePossibleXP(func, self, nodeCD, unlockStats):
    try:
        if config.data.get('enabled', True) and not config.data.get('allowExchangeXPInTechTree', True):
            return unlockStats.getVehTotalXP(nodeCD)
    except Exception:
        logging.getLogger('Driftkings/HangarOptions').exception('new__getAllVehiclePossibleXP')
    return func(self, nodeCD, unlockStats)


# ToolTips Shell
class VehicleData:
    def __init__(self):
        self.item_defs_path = ITEM_DEFS_PATH
        self.shells = {}
        self.my_vehicles = set()

    def get_shots(self, nation):
        xml_path = '%svehicles/%s/components/guns.xml' % (self.item_defs_path, nation)
        section = ResMgr.openSection(xml_path)
        shared = section['shared']
        result = {}
        for gun, val in shared.items():
            shots = val['shots']
            result.update({shot: (result.get(shot, set()) | {gun}) for shot in shots.keys()})
        return result

    def get_guns(self, nation):
        xml_path = '%svehicles/%s/list.xml' % (self.item_defs_path, nation)
        vehicles = ResMgr.openSection(xml_path)
        result = {}
        for veh, v_v in vehicles.items():
            if veh in ['Observer', 'xmlns:xmlref']:
                continue
            i18n_veh = v_v['userString'].asString
            xml_path = '%svehicles/%s/%s.xml' % (self.item_defs_path, nation, veh)
            vehicle = ResMgr.openSection(xml_path)
            turrets0 = vehicle['turrets0']
            for turret in turrets0.values():
                for gun in turret['guns'].keys():
                    result.setdefault(gun, set()).add(i18n.makeString(i18n_veh))
        return result

    def update_shells(self):
        for nation in nations.NAMES:
            shots = self.get_shots(nation)
            guns = self.get_guns(nation)
            self.shells[nation] = {}
            for k_s, v_s in shots.iteritems():
                for gun in v_s:
                    self.shells[nation][k_s] = self.shells[nation].get(k_s, set()) | guns.get(gun, set())

    def update_my_vehicles(self):
        # global myVehicles
        items_cache = dependency.instance(IItemsCache)
        vehicles = items_cache.items.getVehicles()
        self.my_vehicles = {v.userName for v in vehicles.itervalues() if v.invID >= 0}

# class VehicleData():
vehicle_data = VehicleData()
vehicle_data.update_shells()


@override(CommonStatsBlockConstructor, 'construct')
def new__construct(fun, self):
    block = fun(self)
    if self.configuration.params:
        topPadding = formatters.packPadding(top=5)
        block.append(formatters.packTitleDescBlock(title=text_styles.middleTitle(i18n.makeString('#tooltips:quests/vehicles/header')), padding=formatters.packPadding(top=8)))
        shell = vehicle_data.shells.get(self.shell.nationName, None)
        select_shell = shell.get(self.shell.name, set())
        if vehicle_data.my_vehicles:
            vehicles = select_shell & vehicle_data.my_vehicles
            block.append(formatters.packTitleDescBlock(title=text_styles.stats(', '.join(vehicles)), padding=topPadding))
            vehicles = select_shell - vehicles
            block.append(formatters.packTitleDescBlock(title=text_styles.standard(', '.join(vehicles)), padding=topPadding))
        else:
            block.append(formatters.packTitleDescBlock(title=text_styles.standard(', '.join(select_shell)), padding=topPadding))
    return block


@override(CarouselDataProvider, 'buildList')
def new__buildList(func, self):
    func(self)
    vehicle_data.update_my_vehicles()


# hide lootBoxes widget in tank carousel in hangar
def new__getIsActive(func, state):
    if not config.data.get('enabled', True) and not config.data.get('showLootboxesWidget', True):
        return False
    return func(state)


def new__updateCarouselEventEntryStateS(func, self, isVisible):
    if not config.data.get('enabled', True) and not config.data.get('showLootboxesWidget', True):
        isVisible = False
    return func(self, isVisible)


def new__setEventTournamentBannerVisibleS(func, self, alias, visible):
    if not config.data.get('enabled', True) and not config.data.get('showLootboxesWidget', True):
        visible = False
    return func(self, alias, visible)


# Destroy widget if hidden
def new__makeInjectView(func, self):
    if not config.data.get('enabled', True) and not config.data.get('showLootboxesWidget', True):
        self.destroy()
        return
    return func(self)


# PremiumTime
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
    if not config.data.get('enabled', True) and not config.data.get('allowChannelButtonBlinking', True):
        isNotified = False
    func(self, channel, lazy, isNotified)


@override(ChannelsCarouselHandler, '_ChannelsCarouselHandler__setItemField')
def new__setItemField(func, self, clientID, key, value):
    if not config.data.get('enabled', True) and not config.data.get('allowChannelButtonBlinking', True) and key == 'isNotified':
        value = False
    return func(self, clientID, key, value)



class Flash(object):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self, ID):
        self.ID = ID
        self.__isLobby = True
        self.isBattle = False
        self.updateCallback = None
        self.timerEvent = CyclicTimerEvent(1.0, self.updateTimeData)
        if config.data.get('enabled', False) and config.data.get('clock', False):
            self.timerEvent.start()
        self.setup()
        COMPONENT_EVENT.UPDATED += self.__updatePosition

    def setup(self):
        panel_config = dict(config.data['panel']['position'], width=config.data['panel']['width'], height=config.data['panel']['height'], alignX=config.data['panel'].get('alignX', COMPONENT_ALIGN.RIGHT), alignY=config.data['panel'].get('alignY', COMPONENT_ALIGN.TOP), drag=False, border=False, limit=False)
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
        if self.updateCallback:
            self.updateCallback = safeCancelCallback(self.updateCallback)
        COMPONENT_EVENT.UPDATED -= self.__updatePosition
        g_guiFlash.destroyComponent(self.ID)

    @property
    def isLobby(self):
        return self.__isLobby

    @isLobby.setter
    def isLobby(self, value):
        self.__isLobby = value
        if self.updateCallback:
            self.updateCallback = safeCancelCallback(self.updateCallback)
        self.updateCallback = callback(1.0, self.updateTimeData) if not value else self.updateTimeData()

    def updateTimeData(self):
        if not config.data.get('enabled', False) or not config.data.get('clock', False):
            return
        current_time = strftime(config.data['text'])
        g_guiFlash.updateComponent(self.ID, {'text': current_time})


g_flash = None
try:
    from gambiter import g_guiFlash
    from gambiter.flash import COMPONENT_TYPE, COMPONENT_EVENT, COMPONENT_ALIGN
    g_flash = Flash(config.ID)
except ImportError:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    logError(config.ID, 'Loading mod: Not found \'gambiter.flash\' module, loading stop!')
except Exception:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    traceback.print_exc()


def new__onArenaCreated(func, *args, **kwargs):
    g_flash.isBattle = True
    return func(*args, **kwargs)


def new__hangarPopulate(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    finally:
        g_flash.isBattle = False


__initialized = False

def init():
    global __initialized
    override(LobbyHeader, 'as_setPremiumParamsS', new__startCallback)
    override(LoginView, '_populate', new__LoginViewPopulate)
    override(HeroTank, 'recreateVehicle', new__recreateVehicle)
    override(Hangar, 'as_setEventTournamentBannerVisibleS', new__setEventTournamentBannerVisibleS)
    override(ChannelsCarouselHandler, '__setItemField', new__setItemField)
    override(ChannelsCarouselHandler, 'addChannel', new__addChannel)
    override(Hangar, 'as_updateCarouselEventEntryStateS', new__updateCarouselEventEntryStateS)
    override(LobbyHeader, 'as_setHeaderButtonsS', new__setHeaderButtonsS)
    override(PlayerAccount, 'onArenaCreated', new__onArenaCreated)
    override(Hangar, '_populate', new__hangarPopulate)

    if getRegion() != 'RU':
        from gui.Scaleform.daapi.view.lobby.hangar.daily_quest_widget import BaseQuestsWidgetComponent
        from gui.impl.lobby.lootbox_system.entry_point import LootBoxSystemEntryPoint
        from gui.impl.lobby.comp7.tournaments_widget import TournamentsWidgetComponent
        from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import _TechTreeDataProvider

        override(BaseQuestsWidgetComponent, '_shouldHide', new__shouldHide)
        overrideStaticMethod(LootBoxSystemEntryPoint, 'getIsActive', new__getIsActive)
        override(TournamentsWidgetComponent, '_makeInjectView', new__makeInjectView)
        override(_TechTreeDataProvider, 'getAllVehiclePossibleXP', new__getAllVehiclePossibleXP)
    else:
        from gui_lootboxes.gui.impl.lobby.gui_lootboxes.entry_point_view import LootBoxesEntryPointWidget
        from gui.Scaleform.daapi.view.lobby.hangar.daily_quest_widget import DailyQuestWidget
        from gui.techtree.techtree_dp import TechTreeDataProvider

        override(DailyQuestWidget, '_DailyQuestWidget__shouldHide', new__shouldHide)
        overrideStaticMethod(LootBoxesEntryPointWidget, 'getIsActive', new__getIsActive)
        override(TechTreeDataProvider, 'getAllVehiclePossibleXP', new__getAllVehiclePossibleXP)
        __initialized = True
