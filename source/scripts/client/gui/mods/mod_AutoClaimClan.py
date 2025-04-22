# -*- coding: utf-8 -*-
import time

from gui.clans.clan_cache import g_clanCache
from PlayerEvents import g_playerEvents
from gui.clans.data_wrapper.clan_supply import QuestStatus as DataQuestStatus, DataNames
from gui.wgcg.clan_supply.contexts import ClaimRewardsCtx
from adisp import adisp_process
from helpers import dependency
from skeletons.gui.web import IWebController
from skeletons.gui.shared import IItemsCache
from skeletons.gui.app_loader import IAppLoader
from gui import SystemMessages

from DriftkingsCore import DriftkingsConfigInterface, Analytics, logInfo, logWarning, logError, calculate_version, callback


class AutoClaimClanReward(DriftkingsConfigInterface):
    __webController = dependency.descriptor(IWebController)
    itemsCache = dependency.descriptor(IItemsCache)
    appLoader = dependency.descriptor(IAppLoader)
    started = False

    def __init__(self):
        self.lastClaimAttempt = 0
        self.claimCooldown = 10
        super(AutoClaimClanReward, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.1.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU_'
        self.data = {
            'enabled': True,
            'debugLog': False,
            'claimAfterBattle': True,
            'claimAfterSync': True,
            'claimOnDataReceived': True,
            'claimDelay': 1.0,
            'showNotifications': True,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_enabled_text': 'Enabled',
            'UI_setting_enabled_tooltip': 'Enable/disable the mod.',
            'UI_setting_debugLog_text': 'Debug Log',
            'UI_setting_debugLog_tooltip': 'Enable/disable debug logging.',
            'UI_setting_claimAfterBattle_text': 'Claim After Battle',
            'UI_setting_claimAfterBattle_tooltip': 'Claim rewards after a battle.',
            'UI_setting_claimAfterSync_text': 'Claim After Sync',
            'UI_setting_claimAfterSync_tooltip': 'Claim rewards after a sync.',
            'UI_setting_claimOnDataReceived_text': 'Claim On Data Received',
            'UI_setting_claimOnDataReceived_tooltip': 'Claim rewards when data is received.',
            'UI_setting_claimDelay_text': 'Claim Delay',
            'UI_setting_claimDelay_tooltip': 'Delay between claim attempts.',
            'UI_setting_showNotifications_text': 'Show Notifications',
            'UI_setting_showNotifications_tooltip': 'Show notifications.',
        }
        super(AutoClaimClanReward, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('debugLog'),
                self.tb.createControl('claimAfterBattle'),
                self.tb.createControl('claimAfterSync')
            ],
            'column2': [
                self.tb.createControl('claimOnDataReceived'),
                self.tb.createSlider('claimDelay', 1, 10, 1, '{{values}} sec.'),
                self.tb.createControl('showNotifications')
            ]
        }

    def fini(self):
        if self.data['debugLog']:
            logInfo(self.ID,'fini')
        if self.started:
            g_clanCache.clanSupplyProvider.onDataReceived -= self.__onDataReceived
        self.itemsCache.onSyncCompleted -= self._onSyncCompleted
        g_playerEvents.onBattleResultsReceived -= self._onBattleResultsReceived
        self.started = False

    def start(self):
        if not self.data['enabled']:
            return
        if self.data['debugLog']:
            logInfo(self.ID, 'start')
        self.itemsCache.onSyncCompleted += self._onSyncCompleted
        g_playerEvents.onBattleResultsReceived += self._onBattleResultsReceived
        g_clanCache.clanSupplyProvider.onDataReceived += self.__onDataReceived
        self.started = True
        if self.data['showNotifications']:
            self.showNotification('Auto Claim Clan Reward mod activated', isSuccess=True)

    def updateQuests(self):
        if not g_clanCache.isInClan:
            if self.data['debugLog']:
                logWarning(self.ID, 'Not in a clan, skipping claim')
            return
        currentTime = time.time()
        if currentTime - self.lastClaimAttempt < self.claimCooldown:
            if self.data['debugLog']:
                logInfo(self.ID, 'Claim on cooldown, skipping')
            return
        self.lastClaimAttempt = currentTime
        try:
            self.tryToClaimReward()
        except Exception:
            if self.data['debugLog']:
                logWarning(self.ID, 'try to claim exception')
        if self.data['debugLog']:
            logInfo(self.ID, 'updateQuests complete')

    def _onBattleResultsReceived(self, _, __):
        if not self.data['claimAfterBattle']:
            return
        if self.data['debugLog']:
            logInfo(self.ID, 'br 1', self.started)
        self.updateQuests()
        if self.data['debugLog']:
            logInfo(self.ID, 'br 2', self.started)

    def _onSyncCompleted(self, *args):
        if not self.data['claimAfterSync']:
            return
        if self.data['debugLog']:
            logInfo(self.ID, 'sync 1', self.started)
        self.updateQuests()
        if self.data['debugLog']:
            logInfo(self.ID, 'sync 2', self.started)

    @adisp_process
    def tryToClaimReward(self):
        if self.data['debugLog']:
            logInfo(self.ID, 'tryToClaimReward')
        if self.data['claimDelay'] > 0:
            yield callback(self.data['claimDelay'], lambda: None)
        response = yield self.__webController.sendRequest(ctx=ClaimRewardsCtx())
        if self.data['debugLog']:
            logInfo(self.ID, 'tryToClaimReward response', response)
        self.processClaimResponse(response)

    def processClaimResponse(self, response):
        success = False
        message = 'No rewards to claim'
        if response and response.isSuccess():
            if hasattr(response, 'data') and response.data:
                success = True
                message = 'Successfully claimed clan rewards!'
                if hasattr(response.data, 'rewards') and response.data.rewards:
                    rewardsText = self.formatRewards(response.data.rewards)
                    if rewardsText:
                        message += '\n' + rewardsText
        else:
            if response and hasattr(response, 'errorMessage') and response.errorMessage:
                message = 'Failed to claim rewards: ' + response.errorMessage
            else:
                message = 'Failed to claim rewards'
        if self.data['showNotifications']:
            self.showNotification(message, isSuccess=success)

    @staticmethod
    def formatRewards(rewards):
        if not rewards:
            return ''
        formatted = []
        if isinstance(rewards, dict):
            for reward_type, reward_value in rewards.items():
                formatted.append('{}: {}'.format(reward_type, reward_value))
        elif isinstance(rewards, list):
            for reward in rewards:
                if isinstance(reward, dict):
                    for k, v in reward.items():
                        formatted.append('{}: {}'.format(k, v))
                else:
                    formatted.append(str(reward))
        else:
            formatted.append(str(rewards))
        return "\n".join(formatted)

    def showNotification(self, message, isSuccess=True):
        try:
            if isSuccess:
                SystemMessages.pushMessage(message, type=SystemMessages.SM_TYPE.Information)
            else:
                SystemMessages.pushMessage(message, type=SystemMessages.SM_TYPE.Warning)
        except Exception:
            if self.data['debugLog']:
                logError(self.ID, 'Showing notification')

    def parseQuests(self, data):
        if self.data['debugLog']:
            logInfo(self.ID, 'parseQuests', data)
        has_available_rewards = False
        # Check if data has quests attribute
        if hasattr(data, 'quests') and data.quests:
            for q in data.quests:
                if q.status == DataQuestStatus.REWARD_AVAILABLE or q.status == DataQuestStatus.REWARD_PENDING:
                    has_available_rewards = True
                    break
            if has_available_rewards:
                self.tryToClaimReward()
            elif self.data['debugLog']:
                logWarning(self.ID, 'No rewards available to claim')
        elif self.data['debugLog']:
            logWarning(self.ID, 'Invalid data structure - missing quests')

    def __onDataReceived(self, dataName, data):
        if not self.data['claimOnDataReceived']:
            return
        if self.data['debugLog']:
            logInfo(self.ID, '__onDataReceived 1', dataName)
        if dataName not in (DataNames.QUESTS_INFO, DataNames.QUESTS_INFO_POST):
            return
        if self.data['debugLog']:
            logInfo(self.ID, '__onDataReceived 2')
        self.parseQuests(data)


# Create global instance
g_autoClaimClanReward = AutoClaimClanReward()
analytics = Analytics(g_autoClaimClanReward.ID, g_autoClaimClanReward.version)
