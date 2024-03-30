# -*- coding: utf-8 -*-
import locale
import traceback
from math import sin, radians
from time import strftime

import ResMgr
import gui.shared.tooltips.vehicle as tooltips
import helpers
import nations
from Account import PlayerAccount
from CurrentVehicle import g_currentVehicle
from HeroTank import HeroTank
from constants import ITEM_DEFS_PATH
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.common.vehicle_carousel.carousel_data_provider import CarouselDataProvider
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from gui.Scaleform.daapi.view.lobby.hangar.ammunition_panel import AmmunitionPanel
from gui.Scaleform.daapi.view.lobby.hangar.carousels import TankCarousel
from gui.Scaleform.daapi.view.lobby.hangar.daily_quest_widget import DailyQuestWidget
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
from gui.Scaleform.daapi.view.meta.ModuleInfoMeta import ModuleInfoMeta
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.HANGAR_ALIASES import HANGAR_ALIASES
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
from helpers import dependency
from helpers.i18n import makeString
from helpers.time_utils import getTimeDeltaFromNow, makeLocalServerTime, ONE_DAY, ONE_HOUR, ONE_MINUTE
from messenger.gui.Scaleform.lobby_entry import LobbyEntry
from notification.NotificationListView import NotificationListView
from skeletons.gui.app_loader import GuiGlobalSpaceID
from skeletons.gui.shared import IItemsCache
from vehicle_systems.tankStructure import ModelStates

from DriftkingsCore import SimpleConfigInterface, Analytics, override, callback, isReplay, logDebug, cancelCallback
from DriftkingsInject import CyclicTimerEvent, g_events

firstTime = True

AS_SWF = 'DateTimes.swf'
AS_ALIASES = 'Driftkings_DateTimes_UI'


class ConfigInterface(SimpleConfigInterface):

    def __init__(self):
        ServicesLocator.appLoader.onGUISpaceEntered += self.onGUISpaceEntered
        self.values = {'vehicles': []}
        self.callback = None
        self.macros = {}
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '3.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'autoLogin': False,
            'showXpToUnlockVeh': True,
            'showReferralButton': True,
            'showGeneralChatButton': True,
            'showPromoPremVehicle': True,
            'showPopUpMessages': True,
            'showUnreadCounter': True,
            'showRankedBattleResults': True,
            'showButton': True,
            'showBattleCount': True,
            'showDailyQuestWidget': True,
            'showProgressiveDecalsWindow': True,
            'showEventBanner': True,
            'showHangarPrestigeWidget': True,
            'showProfilePrestigeWidget': True,
            'showWotPlusButton': True,
            'showBuyPremiumButton': True,
            'showPremiumShopButton': True,
            'showButtonCounters': True,
            'allowExchangeXPInTechTree': True,
            'premiumTime': False,
            'clock': True,
            'format': '<font face=\'$FieldFont\' color=\'#959688\'><textformat leading=\'-38\'><font size=\'30\'>\t%H:%M:%S</font><br/></textformat><textformat rightMargin=\'85\' leading=\'-2\'>%A<br/><font size=\'15\'>%d %b %Y</font></textformat></font>',
            'x': 1900,
            'y': 47,
            'rows': 2,
            'smallCarousel': False
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_autoLogin_text': 'Auto-Login',
            'UI_setting_autoLogin_tooltip': 'Auto enter to the game',
            'UI_setting_showReferralButton_text': 'Referral Button',
            'UI_setting_showReferralButton_tooltip': 'Disable "Referral Program" button.',
            'UI_setting_showGeneralChatButton_text': 'General Chat Button',
            'UI_setting_showGeneralChatButton_tooltip': 'Disable "General chat" button.',
            'UI_setting_showPromoPremVehicle_text': 'Promo Prem Vehicle',
            'UI_setting_showPromoPremVehicle_tooltip': 'Disable info windows with the battle results in the "Ranked battle" mode.',
            'UI_setting_showPopUpMessages_text': 'PopUpMessages',
            'UI_setting_showPopUpMessages_tooltip': 'Disable display "Session statistics" button.',
            'UI_setting_showUnreadCounter_text': 'UnreadCounter',
            'UI_setting_showUnreadCounter_tooltip': 'Disable display the counter of spent battles on the button.',
            'UI_setting_showRankedBattleResults_text': 'Ranked Battle Results',
            'UI_setting_showRankedBattleResults_tooltip': 'Disable info windows with the battle results in the "Ranked battle" mode.',
            'UI_setting_showButton_text': 'Button Statistics',
            'UI_setting_showButton_tooltip': 'Disable display "Session statistics" button.',
            'UI_setting_showBattleCount_text': 'Battle Count',
            'UI_setting_showBattleCount_tooltip': 'Disable display the counter of spent battles on the button.',
            'UI_setting_showDailyQuestWidget_text': 'Daily Quest Widget',
            'UI_setting_showDailyQuestWidget_tooltip': 'Disable widget "Daily Quests" in the hangar.',
            'UI_setting_showProgressiveDecalsWindow_text': 'Progressive Decals Window',
            'UI_setting_showProgressiveDecalsWindow_tooltip': 'Disable info windows when receiving progressive decals.',
            'UI_setting_showEventBanner_text': 'Event Banner',
            'UI_setting_showEventBanner_tooltip': 'Disable banner of various events in the hangar.',
            'UI_setting_showHangarPrestigeWidget_text': 'Hangar PrestigeWidget',
            'UI_setting_showHangarPrestigeWidget_tooltip': 'Disable elite levels widget in the hangar.',
            'UI_setting_showProfilePrestigeWidget_text': 'Profile Prestige Widget',
            'UI_setting_showProfilePrestigeWidget_tooltip': 'Disable elite levels widget in the profile for vehicle statistics.',
            'UI_setting_showWotPlusButton_text': 'Wot Plus Button',
            'UI_setting_showWotPlusButton_tooltip': 'Disable "WoT Plus" subscription button.',
            'UI_setting_showBuyPremiumButton_text': 'Buy Premium Button',
            'UI_setting_showBuyPremiumButton_tooltip': 'Disable "Buy premium" button.',
            'UI_setting_showPremiumShopButton_text': 'Premium Shop Button',
            'UI_setting_showPremiumShopButton_tooltip': 'Disable "Premium shop" button.',
            'UI_setting_showButtonCounters_text': 'Button Counters',
            'UI_setting_showButtonCounters_tooltip': 'Disable counter on buttons for new items.',
            'UI_setting_allowExchangeXPInTechTree_text': 'Allow Exchange XP In TechTree',
            'UI_setting_allowExchangeXPInTechTree_tooltip': 'Allow to consider the exchange of experience with gold in tech tree.',
            'UI_setting_showXpToUnlockVeh_text': 'Show Xp To Unlock Veh',
            'UI_setting_showXpToUnlockVeh_tooltip': 'Display of missing experience to unlock vehicles.',
            'UI_setting_premiumTime_text': 'Premium Time',
            'UI_setting_premiumTime_tooltip': 'Display exact premium time.',
            #
            'UI_setting_clock_text': 'Enable clock',
            'UI_setting_clock_tooltip': 'Enable clock in Login and Hangar',
            'UI_setting_x_text': 'Position X',
            'UI_setting_x_tooltip': 'Horizontal position',
            'UI_setting_y_text': 'Position Y',
            'UI_setting_y_tooltip': 'Vertical position',
            #
            'UI_setting_rows_text': 'Rows',
            'UI_setting_rows_tooltip': 'Rows Number',
            'UI_setting_smallCarousel_text': 'Small Carousel',
            'UI_setting_smallCarousel_tooltip': 'Enable Small Carousel',
            #
            'UI_techTree_shootingRadius': 'Shooting Radius',
            'UI_techTree_m': 'M.',
            #
            'UI_nations_order': '[\'ussr\', \'germany\', \'usa\', \'china\', \'france\', \'uk\', \'japan\', \'czech\', \'poland\', \'sweden\', \'italy\']',
            'UI_roles_order': '[\'commander\', \'gunner\', \'driver\', \'radioman\', \'loader\']',
            'UI_sorting_criteria': '[\'nation\', \'role\', \'level\', \'-level\', \'XP\', \'-XP\', \'gender\', \'-gender\', \'inVehicle\', \'-inVehicle\', \'vehicle\']',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'settingsVersion': 1,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('autoLogin'),
                self.tb.createControl('allowExchangeXPInTechTree'),
                self.tb.createControl('showReferralButton'),
                self.tb.createControl('showGeneralChatButton'),
                self.tb.createControl('showPromoPremVehicle'),
                self.tb.createControl('showPopUpMessages'),
                self.tb.createControl('showUnreadCounter'),
                self.tb.createControl('showRankedBattleResults'),
                self.tb.createControl('showButton'),
                self.tb.createControl('showBattleCount'),
                self.tb.createControl('showDailyQuestWidget'),
                self.tb.createControl('showProgressiveDecalsWindow'),
                self.tb.createControl('showEventBanner'),
            ],
            'column2': [
                self.tb.createControl('showHangarPrestigeWidget'),
                self.tb.createControl('showProfilePrestigeWidget'),
                self.tb.createControl('showWotPlusButton'),
                self.tb.createControl('showEventBanner'),
                self.tb.createControl('showBuyPremiumButton'),
                self.tb.createControl('showPremiumShopButton'),
                self.tb.createControl('showButtonCounters'),
                self.tb.createControl('showXpToUnlockVeh'),
                self.tb.createControl('clock'),
                self.tb.createSlider('x', -2000, 2000, 1, '{{value}}%s' % ' X'),
                self.tb.createSlider('y', -2000, 2000, 1, '{{value}}%s' % ' Y'),
                self.tb.createSlider('rows', 1, 10, 1, '{{value}} ' + ' Rows'),
                self.tb.createControl('smallCarousel')

            ]
        }

    @staticmethod
    def onGUISpaceEntered(spaceID):
        if spaceID == GuiGlobalSpaceID.LOBBY:
            ServicesLocator.appLoader.getApp().loadView(SFViewLoadParams(AS_ALIASES))

    def getPremiumLabelText(self, timeDelta):
        delta = float(getTimeDeltaFromNow(makeLocalServerTime(timeDelta)))
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
            logDebug(True, 'Controller is not defined', ctx)
            return
        else:
            ctx.clear()
            return
    return func(self, event)


# hide premium vehicle on the background in the hangar
@override(HeroTank, 'recreateVehicle')
def new__recreateVehicle(func, self, typeDescriptor=None, state=ModelStates.UNDAMAGED, _=None, outfit=None):
    if config.data['enabled'] and config.data['showPromoPremVehicle']:
        return
    func(self, typeDescriptor, state, _, outfit)


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
@override(DailyQuestWidget, '_DailyQuestWidget__shouldHide')
def new__shouldHide(func, self):
    if config.data['enabled'] and config.data['showDailyQuestWidget']:
        return True
    return func(self)


# hide display pop-up window when receiving progressive decals
@override(ProgressiveItemsRewardHandler, '_showAward')
def new__showAward(func, self, ctx):
    if config.data['enabled'] and config.data['showProgressiveDecalsWindow']:
        return
    func(self, ctx)


# hide display banner of various events in the hangar
@override(EventEntryPointsContainer, '_EventEntryPointsContainer__updateEntries')
def new__updateEntries(func, self):
    if config.data['enabled'] and config.data['showEventBanner']:
        self.as_updateEntriesS([])
        return
    func(self)


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
@override(LobbyHeader, 'as_setHeaderButtonsS')
def new__setHeaderButtonsS(func, self, data):
    if config.data['enabled'] and config.data['showWotPlusButton'] and self.BUTTONS.WOT_PLUS in data:
        data.remove(self.BUTTONS.WOT_PLUS)
    if config.data['enabled'] and config.data['showBuyPremiumButton'] and self.BUTTONS.PREM in data:
        data.remove(self.BUTTONS.PREM)
    if config.data['enabled'] and config.data['showPremiumShopButton'] and self.BUTTONS.PREMSHOP in data:
        data.remove(self.BUTTONS.PREMSHOP)
    return func(self, data)


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
@override(LoginView, '_populate')
def new__populate(func, self):
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
                        icon = "<img src='{}' vspace='{}'".format(RES_ICONS.MAPS_ICONS_LIBRARY_XPCOSTICON_1.replace('..', 'img://gui'), -3)
                        template = "<font face='$TitleFont' size='14'><font color='#ff2717'>{}</font> {}</font> {}"
                        block[0]['data']['text'] = template.format(helpers.i18n.makeString(STORAGE.BLUEPRINTS_CARD_CONVERTREQUIRED), need, icon)
            return block
        except StandardError:
            traceback.format_exc()
            return block
    else:
        return block


# TechTree
def _getRanges(turret, gun, nation, vClass):
    visionRadius = 0
    firingRadius = 0
    artyRadius = 0
    gunsInfoPath = 'scripts/item_defs/vehicles/' + nation + '/components/guns.xml/shared/'
    # Turret-dependent
    visionRadius = int(turret.circularVisionRadius)
    # Gun-dependent
    shots = gun.shots
    for shot in shots:
        radius = int(shot.maxDistance)
        if firingRadius < radius:
            firingRadius = radius

        if vClass == 'SPG' and shot.shell.kind == 'HIGH_EXPLOSIVE':
            try:
                pitchLimit_rad = min(radians(45), -calcPitchLimitsFromDesc(0, gun.pitchLimits)[0])
            except StandardError:
                minPitch = radians(-45)
                for gun in turret.guns:
                    if gun.name == gun.name:
                        minPitch = gun.pitchLimits['minPitch'][0][1]
                        break
                pitchLimit_rad = min(radians(45), -minPitch)
            radius = int(pow(shot.speed, 2) * sin(2 * pitchLimit_rad) / shot.gravity)
            if artyRadius < radius:
                artyRadius = radius

        return visionRadius, firingRadius, artyRadius


@override(_TechTreeDataProvider, 'getAllVehiclePossibleXP')
def new__getAllVehiclePossibleXP(func, self, nodeCD, unlockStats):
    if config.data['enabled'] and config.data['allowExchangeXPInTechTree']:
        return unlockStats.getVehTotalXP(nodeCD)
    return func(self, nodeCD, unlockStats)


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
            (viewRange, shellRadius, artiRadius) = _getRanges(turret, _gun, vehicle.nationName, vehicle.type)
            if vehicle.type == 'SPG':
                moduleInfo['parameters']['params'].append({'type': '<h>' + config.i18n['UI_techTree_shootingRadius'] + ' <p>' + config.i18n['UI_techTree_m'] + '</p></h>', 'value': '<h>' + str(artiRadius) + '</h>'})
            elif shellRadius < 707:
                moduleInfo['parameters']['params'].append({'type': '<h>' + config.i18n['UI_techTree_shootingRadius'] + ' <p>' + config.i18n['UI_techTree_m'] + '</p></h>', 'value': '<h>' + str(shellRadius) + '</h>'})
    except StandardError:
        traceback.format_exc()
    return func(self, moduleInfo)


# ToolTips Shell
shells = {}
myVehicles = set()


def getShots():
    xmlPath = '%svehicles/%s/components/guns.xml' % (ITEM_DEFS_PATH, nation)
    section = ResMgr.openSection(xmlPath)
    shared = section['shared']
    result = {}
    for gun, val in shared.items():
        shots = val['shots']
        result.update({shot: (result.get(shot, set()) | {gun}) for shot in shots.keys()})
    return result


def getGuns():
    xmlPath = '%svehicles/%s/list.xml' % (ITEM_DEFS_PATH, nation)
    vehicles = ResMgr.openSection(xmlPath)
    result = {}
    for veh, v_v in vehicles.items():
        if (veh == 'Observer') or (veh == 'xmlns:xmlref'):
            continue
        i18n_veh = v_v['userString'].asString
        xmlPath = '%svehicles/%s/%s.xml' % (ITEM_DEFS_PATH, nation, veh)
        vehicle = ResMgr.openSection(xmlPath)
        turrets0 = vehicle['turrets0']
        result.update({gun: (result.get(gun, set()) | {makeString(i18n_veh)}) for turret in turrets0.values() for gun in turret['guns'].keys()})
    return result


for nation in nations.NAMES:
    shots = getShots()
    guns = getGuns()
    shells[nation] = {}
    for k_s, v_s in shots.iteritems():
        for gun in v_s:
            shells[nation][k_s] = shells[nation].get(k_s, set()) | guns.get(gun, set())


def updateMyVehicles():
    global myVehicles
    itemsCache = dependency.instance(IItemsCache)
    vehicles = itemsCache.items.getVehicles()
    myVehicles = {v.userName for v in vehicles.itervalues() if v.invID >= 0}


@override(CommonStatsBlockConstructor, 'construct')
def new__construct(fun, self):
    block = fun(self)
    if self.configuration.params:
        topPadding = formatters.packPadding(top=5)
        block.append(formatters.packTitleDescBlock(title=text_styles.middleTitle(makeString('#tooltips:quests/vehicles/header')), padding=formatters.packPadding(top=8)))
        n_shell = shells.get(self.shell.nationName, None)
        select_shell = n_shell.get(self.shell.name, set())
        if myVehicles:
            vehicles = select_shell & myVehicles
            block.append(formatters.packTitleDescBlock(title=text_styles.stats(', '.join(vehicles)), padding=topPadding))
            vehicles = select_shell - vehicles
            block.append(formatters.packTitleDescBlock(title=text_styles.standard(', '.join(vehicles)), padding=topPadding))
        else:
            block.append(formatters.packTitleDescBlock(title=text_styles.standard(', '.join(select_shell)), padding=topPadding))
    return block


@override(CarouselDataProvider, 'buildList')
def new__buildList(func, self):
    func(self)
    updateMyVehicles()


@override(PlayerAccount, 'onArenaCreated')
def new__onArenaCreated(func, *args, **kwargs):
    config.isBattle = True
    return func(*args, **kwargs)


@override(Hangar, '_populate')
def new__populate(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    finally:
        config.isBattle = False


# CAROUSEL
@override(TankCarousel, 'as_rowCountS')
def new__rowCountS(func, self, row_count):
    if config.data['enabled'] and self.getAlias() == HANGAR_ALIASES.TANK_CAROUSEL:
        row_count = max(config.data['rows'], row_count)
    return func(self, row_count)


@override(TankCarousel, 'as_setSmallDoubleCarouselS')
def new__setSmallDoubleCarouselS(func, self, small):
    return func(self, small or config.data['enabled'] and config.data['smallCarousel'])


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


class DateTimesMeta(View):

    def __init__(self):
        super(DateTimesMeta, self).__init__()

    def _populate(self):
        # noinspection PyProtectedMember
        super(DateTimesMeta, self)._populate()

    def _dispose(self):
        # noinspection PyProtectedMember
        super(DateTimesMeta, self)._dispose()

    def as_startUpdateS(self, *args):
        return self.flashObject.as_startUpdate(*args) if self._isDAAPIInited() else None

    def as_setDateTimeS(self, text):
        return self.flashObject.as_setDateTime(text) if self._isDAAPIInited() else None

    def as_clearSceneS(self):
        return self.flashObject.as_clearScene() if self._isDAAPIInited() else None


class DateTimesUI(DateTimesMeta):

    def __init__(self):
        super(DateTimesUI, self).__init__()
        self.config = {
            'enabled': config.data['clock'],
            'x': config.data['x'],
            'y': config.data['y'],
            'format': config.data['format']
        }
        self.timerEvent = CyclicTimerEvent(1.0, self.updateTimeData)

    def _populate(self):
        super(DateTimesUI, self)._populate()
        self.as_startUpdateS(self.config)
        if config.data['enabled'] and self.config['enabled']:
            self.timerEvent.start()

    def _dispose(self):
        self.timerEvent.stop()
        super(DateTimesUI, self)._dispose()

    @staticmethod
    def getEncoding():
        coding = locale.getpreferredencoding()
        if coding in locale.locale_encoding_alias:
            return locale.locale_encoding_alias[coding]
        return coding

    def updateTimeData(self):
        self.as_setDateTimeS(unicode(strftime(self.config['format']), self.getEncoding(), 'ignore'))


g_entitiesFactories.addSettings(ViewSettings(AS_ALIASES, DateTimesUI, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
