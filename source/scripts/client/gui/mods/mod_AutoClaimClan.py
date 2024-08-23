# -*- coding: utf-8 -*-
from threading import Thread

from adisp import adisp_process
from gui import SystemMessages
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.clans.clan_cache import g_clanCache
from gui.clans.data_wrapper.clan_supply import DataNames, QuestStatus
from gui.impl import backport
from gui.impl.gen import R
from gui.shared.money import Currency
from gui.wgcg.clan_supply.contexts import ClaimRewardsCtx, PurchaseProgressionStageCtx
from gui.wgnc import g_wgncEvents
from gui.wgnc.settings import WGNC_DATA_PROXY_TYPE
from helpers import dependency
from skeletons.gui.shared import IItemsCache
from skeletons.gui.shared.utils import IHangarSpace
from skeletons.gui.web import IWebController

from DriftkingsCore import SimpleConfigInterface, Analytics, logWarning, logDebug, calculateVersion

REWARD_STATUS_OK = (QuestStatus.REWARD_AVAILABLE, QuestStatus.REWARD_PENDING)
NEXT_DOUBLE = (3, 8, 13, 18)


class ConfigInterface(SimpleConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU_'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'claimRewards': False
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculateVersion(self.version),
            'UI_setting_claimRewards_text': 'Claim Rewards',
            'UI_setting_claimRewards_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('claimRewards'),
            ],
            'column2': []
        }


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


class AutoClaimClanReward(object):
    __webController = dependency.descriptor(IWebController)
    __itemsCache = dependency.descriptor(IItemsCache)
    __hangarSpace = dependency.descriptor(IHangarSpace)

    def __init__(self):
        self.__hangarSpace.onSpaceCreate += self.onCreate
        self.__cachedProgressData = None
        self.__cachedSettingsData = None
        self.__cachedQuestsData = None
        self.__enabled = config.data['enabled'] and config.data['claimRewards']
        self.__started = False

    def onCreate(self):
        if not self.__started and self.__enabled and g_clanCache.isInClan:
            self.start()
        elif self.__started and not self.__enabled and g_clanCache.isInClan:
            self.stop()
        if self.__cachedSettingsData is None:
            self.__requestClanData()

    def __requestClanData(self):
        g_clanCache.clanSupplyProvider.onDataReceived += self.__onDataReceived
        g_clanCache.clanSupplyProvider._requestData(DataNames.QUESTS_INFO_POST)
        g_clanCache.clanSupplyProvider._requestData(DataNames.PROGRESSION_SETTINGS)
        g_clanCache.clanSupplyProvider._requestData(DataNames.PROGRESSION_PROGRESS)

    def start(self):
        g_wgncEvents.onProxyDataItemShowByDefault += self.__onProxyDataItemShow
        g_clientUpdateManager.addCurrencyCallback(Currency.TOUR_COIN, self.__onTourcoin)
        self.__started = True

    def stop(self):
        g_wgncEvents.onProxyDataItemShowByDefault -= self.__onProxyDataItemShow
        g_clientUpdateManager.removeCurrencyCallback(Currency.TOUR_COIN, self.__onTourcoin)
        self.__started = False

    def __onProxyDataItemShow(self, _, item):
        if item.getType() == WGNC_DATA_PROXY_TYPE.CLAN_SUPPLY_QUEST_UPDATE and item.getStatus() in REWARD_STATUS_OK:
            self.__claimRewards()

    def __onTourcoin(self, *args):
        if all([self.__cachedProgressData, self.__cachedSettingsData]):
            self.parseProgression(self.__cachedProgressData)

    @adisp_process
    def __claimRewards(self):
        response = yield self.__webController.sendRequest(ctx=ClaimRewardsCtx())
        if not response.isSuccess():
            SystemMessages.pushMessage("DriftkingsCore: Auto Claim Clan Reward - " + backport.text(R.strings.clan_supply.messages.claimRewards.error()), type=SystemMessages.SM_TYPE.Error)
            logWarning(config.ID, 'Failed to claim rewards. Code: {}', response.getCode())

    @adisp_process
    def __claimProgression(self, stageID, price):
        response = yield self.__webController.sendRequest(ctx=PurchaseProgressionStageCtx(stageID, price))
        if not response.isSuccess():
            SystemMessages.pushMessage("DriftkingsCore: Auto Claim Clan Reward - Failed to claim Progression.", type=SystemMessages.SM_TYPE.Error)
            logWarning(config.ID, 'Failed to claim Progression. Code: {}', response.getCode())

    def __handleClaimError(self, action, response):
        SystemMessages.pushMessage("DriftkingsCore: Auto Claim Clan Reward - Failed to {}.".format(action), type=SystemMessages.SM_TYPE.Error)
        logWarning(config.data, 'Failed to {}, Code: {}'.format(action, response.getCode()))

    def parseQuests(self, data):
        if any(q.status in REWARD_STATUS_OK for q in data.quests):
            self.__claimRewards()

    @property
    def currency(self):
        return self.__itemsCache.items.stats.dynamicCurrencies.get(Currency.TOUR_COIN, 0)

    def parseProgression(self, data):
        last_purchased = int(data.last_purchased or 0)
        to_purchased = last_purchased + 1 if last_purchased not in NEXT_DOUBLE else last_purchased + 2
        next_points = self.__cachedSettingsData.points.get(str(to_purchased))
        if next_points is not None and self.currency >= next_points.price:
            self.__claimProgression(to_purchased, next_points.price)

    def __onDataReceived(self, data_name, data):
        logDebug(config.data, "__onDataReceived {} {}", data_name, data)
        if data_name in (DataNames.QUESTS_INFO, DataNames.QUESTS_INFO_POST):
            self.__cachedQuestsData = data
            if self.__started:
                self.parseQuests(data)
        elif data_name == DataNames.PROGRESSION_PROGRESS:
            self.__cachedProgressData = data
            if self.__started:
                self.parseProgression(data)
        elif data_name == DataNames.PROGRESSION_SETTINGS:
            self.__cachedSettingsData = data


g_autoClaimClanReward = Thread(target=AutoClaimClanReward, name="mod_AutoClaimClanReward")
g_autoClaimClanReward.daemon = True
g_autoClaimClanReward.start()
