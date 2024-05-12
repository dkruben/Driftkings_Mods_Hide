# -*- coding: utf-8 -*-
import math
import re
import textwrap

from CurrentVehicle import g_currentVehicle
from gui.Scaleform.daapi.view.lobby.hangar.VehicleParameters import VehicleParameters, _VehParamsDataProvider as VehParamsDataProvider
from gui.Scaleform.genConsts.HANGAR_ALIASES import HANGAR_ALIASES
from gui.Scaleform.locale.QUESTS import QUESTS
from gui.impl.backport.backport_system_locale import getIntegralFormat
from gui.server_events.personal_missions_cache import vehicleRequirementsCheck
from gui.server_events.personal_progress.formatters import PMTooltipConditionsFormatters
from gui.shared.tooltips import getUnlockPrice
from gui.shared.utils.requesters import REQ_CRITERIA
from helpers import i18n
from helpers import int2roman, dependency
from personal_missions import PM_BRANCH
from skeletons.gui.server_events import IEventsCache
from skeletons.gui.shared import IItemsCache

from DriftkingsCore import SimpleConfigInterface, Analytics, override


class ConfigInterface(SimpleConfigInterface):
    eventsCache = dependency.descriptor(IEventsCache)
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        self._expandedGroups = {}
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'DriftKing\'s'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'useFreeExp': True,
            'isTruncateNumbers': True,
            'showModuleStatus': True,
            'showEliteStatus': True,
            'showNextVehicle': True,
            'showVehicleInfo': True,
            'showQuestTitle': True,
            'showConditions': True,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_useFreeExp_text': 'Factor Free Experience',
            'UI_setting_useFreeExp_tooltip': '',
            'UI_setting_isTruncateNumbers_text': 'Short numbers',
            'UI_setting_isTruncateNumbers_tooltip': '',
            'UI_setting_showModuleStatus_text': 'Display experience required to research next module',
            'UI_setting_showModuleStatus_tooltip': '',
            'UI_setting_showEliteStatus_text': 'Display experience required to reach the Elite status',
            'UI_setting_showEliteStatus_tooltip': '',
            'UI_setting_showNextVehicle_text': 'Display experience required to research a higher-tier vehicle',
            'UI_setting_showNextVehicle_tooltip': '',
            'UI_setting_showVehicleInfo_text': 'Display vehicle characteristics',
            'UI_setting_showVehicleInfo_tooltip': '',
            'UI_setting_showQuestTitle_text': 'Display title',
            'UI_setting_showQuestTitle_tooltip': '',
            'UI_setting_showConditions_text': 'Display description',
            'UI_setting_showConditions_tooltip': '',

            'UI_setting_eliteStatus_text': '<img align=\'top\' src=\'img://gui/maps/icons/library/EliteXpIcon-2.png\' height=\'16\' width=\'16\' vspace=\'-3\'> <font color=\'#00FF00\'>{chk-exp}</font><img align=\'top\' src=\'img://gui/maps/icons/library/XpIcon-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'> from <font color=\'#FF0000\'>{need-exp}</font><img align=\'top\' src=\'img://gui/maps/icons/library/XpIcon-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'> (~{battles-left}<img align=\'top\' src=\'img://gui/maps/icons/library/BattleResultIcon-1.png\' height=\'14\' width=\'14\' vspace=\'-3\'>)',
            'UI_setting_eliteStatusReady_text': '<img align=\'top\' src=\'img://gui/maps/icons/library/EliteXpIcon-2.png\' height=\'16\' width=\'16\' vspace=\'-3\'> <font color=\'#00FF00\'>Elite status available!</font>',
            'UI_setting_eliteStatusReadyTitle_text': '{tank-name}',
            'UI_setting_eliteStatusTitle_text': '{tank-name}',
            'UI_setting_eliteStatus_tooltip': 'Discount {discount}<img align=\'top\' src=\'img://gui/maps/icons/library/XpIcon-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'>',

            'UI_setting_experience_header': 'Research',

            'UI_setting_moduleStatus_text': '<img align=\'top\' src=\'img://gui/maps/icons/buttons/removeGold.png\' height=\'15\' width=\'13\' vspace=\'-2\'> <font color=\'#00FF00\'>{chk-exp}</font><img align=\'top\' src=\'img://gui/maps/icons/library/XpIcon-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'> from <font color=\'#FF0000\'>{need-exp}</font><img align=\'top\' src=\'img://gui/maps/icons/library/XpIcon-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'> (~{battles-left}<img align=\'top\' src=\'img://gui/maps/icons/library/BattleResultIcon-1.png\' height=\'14\' width=\'14\' vspace=\'-3\'>)',
            'UI_setting_moduleStatusReady_text': '<img align=\'top\' src=\'img://gui/maps/icons/buttons/removeGold.png\' height=\'16\' width=\'14\' vspace=\'-2\'> <font color=\'#00FF00\'>Module research available!</font>',
            'UI_setting_moduleStatusReadyTitle_text': 'Modules',
            'UI_setting_moduleStatusTitle_text': 'Modules',

            'UI_setting_nextTanks_text': '<img align=\'top\' src=\'img://gui/maps/icons/library/UnlockPrice.png\' height=\'16\' width=\'16\' vspace=\'-2\'> <font color=\'#00FF00\'>{chk-exp}</font><img align=\'top\' src=\'img://gui/maps/icons/library/XpIcon-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'> from <font color=\'#FF0000\'>{need-exp}</font><img align=\'top\' src=\'img://gui/maps/icons/library/XpIcon-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'> (~{battles-left}<img align=\'top\' src=\'img://gui/maps/icons/library/BattleResultIcon-1.png\' height=\'14\' width=\'14\' vspace=\'-3\'>)',
            'UI_setting_nextTanksReady_text': '<img align=\'top\' src=\'img://gui/maps/icons/library/UnlockPrice.png\' height=\'16\' width=\'16\' vspace=\'-2\'> <font color=\'#00FF00\'>Research available!</font>',
            'UI_setting_nextTanksReadyTitle_text': '{tank-name}',
            'UI_setting_nextTanksTitle_text': '{tank-name}',
            'UI_setting_nextTanks_tooltip': 'Discount {discount}<img align=\'top\' src=\'img://gui/maps/icons/library/XpIcon-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'>',

            'UI_setting_questSettingsLabel_text': 'Personal Mission status:',
            'UI_setting_questsHeader': 'Personal Assignments',
            'UI_setting_questsHeader_pm2': 'Personal Assignments Campagin 2',
            'UI_setting_questsHeader_regular': 'Personal Assignments Campagin 1',

            'UI_text_add_condition': '<font color=\'#aefe57\'>{quest-add-condition}</font>',
            'UI_text_add_condition_extra': 'Secondary condition',
            'UI_text_main_condition': '<b><font color=\'#aefe57\'>{quest-main-condition}</font></b>',
            'UI_text_main_condition_extra': 'Main condition',

            'UI_setting_questInfo_text': '<b><font color=\'#E8E0BD\'>{quest-name}</b></font> (min. level #{quest-min-level})',


        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        xQuestsHeader = self.tb.createLabel('questSettingsLabel')
        xQuestsHeader['text'] += ''
        return {
            'modDisplayName': self.ID,
            'settingsVersion': 1,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('isTruncateNumbers'),
                self.tb.createControl('showVehicleInfo'),
                xQuestsHeader,
                self.tb.createControl('showQuestTitle'),
                self.tb.createControl('showConditions'),
            ],
            'column2': [
                self.tb.createControl('useFreeExp'),
                self.tb.createControl('showNextVehicle'),
                self.tb.createControl('showModuleStatus'),
                self.tb.createControl('showEliteStatus'),
            ]
        }

    def onApplySettings(self, settings, isFirst=False):
        if not isFirst:
            g_currentVehicle.onChanged()

    @staticmethod
    def formatConditions(conditions):
        orConditions = []
        andConditions = []
        dot = i18n.makeString(QUESTS.QUEST_CONDITION_DOT)
        for cond in conditions:
            for x in ('text', 'title'):
                if hasattr(cond, x):
                    text = getattr(cond, x)
                    text = re.sub('<.*?>', '', text)
                    text = dot + ' ' + text
                    if cond.isInOrGroup:
                        orConditions.append(text)
                    andConditions.append(text)
                    continue

        andResult = '\n'.join(andConditions)
        orResult = ('\n%s\n' % i18n.makeString(QUESTS.QUEST_CONDITION_OR)).join(orConditions)
        return '%s\n%s' % (orResult, andResult) if orResult else andResult

    def isExpanded(self, paramID):
        return self._expandedGroups.get(paramID, False)

    def setExpanded(self, paramID, value):
        self._expandedGroups[paramID] = value

    def getInfo(self):
        result = []
        if g_currentVehicle.isPresent():
            for branch in PM_BRANCH.ACTIVE_BRANCHES:
                result.extend(self.getQuest(branch))

            result.extend(self.getVehicleExperience())
        return result

    def getQuest(self, branch):
        data = []
        quests = self.eventsCache.getPersonalMissions()
        for quest in quests.getSelectedQuestsForBranch(branch).values():
            if vehicleRequirementsCheck(quest, (g_currentVehicle.item.intCD,), self.itemsCache.items.getItemByCD):
                if self.data['showQuestTitle']:
                    level = quest.getVehMinLevel()
                    formatData = {
                        'quest-name': quest.getUserName(),
                        'quest-min-level': level,
                        'quest-min-level-roman': int2roman(level)
                    }
                    data.extend(self.pack('', self.i18n['UI_setting_questInfo_text'].format(**formatData)))
                if self.data['showConditions']:
                    for condType in ('main', 'add'):
                        conditions = PMTooltipConditionsFormatters().format(quest, condType == 'main')
                        conditionsText = self.formatConditions(conditions)
                        if conditionsText:
                            data.extend(self.getQuestCondition(condType, conditionsText))

        if not data:
            return []
        branch_name = PM_BRANCH.TYPE_TO_NAME[branch]
        header = self.getHeader(self.i18n['UI_setting_questsHeader_' + branch_name])
        if not self.isExpanded(self.i18n['UI_setting_questsHeader_' + branch_name]):
            return header
        data = header + data
        return data

    def getVehicleExperience(self):
        exp, avgXP, freeXP = self.getExperienceInfo()
        vehicles = self.itemsCache.items.getVehicles(REQ_CRITERIA.EMPTY)
        modulesNeedXP, eliteNeedXP, eliteDiscountXP, researchVehicles, isEliteReady, isModulesReady = self.getExperienceStatus(vehicles)
        data = self.getModuleStatus(modulesNeedXP, isModulesReady)
        data.extend(self.getEliteStatus(isEliteReady, eliteNeedXP, eliteDiscountXP))
        data.extend(self.getNextTankStatus(researchVehicles))
        if not data:
            return []
        else:
            header = self.getHeader(self.i18n['UI_setting_experience_header'])
            value = min((exp + freeXP if self.data['useFreeExp'] else exp) + eliteDiscountXP, eliteNeedXP)
            header.append({
                'indicatorVO': {
                    'useAnim': True,
                    'markerValue': value,
                    'maxValue': eliteNeedXP,
                    'value': value,
                    'minValue': 0
                },
                'state': 'simpleBottom',
                'paramID': self.i18n['UI_setting_experience_header'],
                'isEnabled': True,
                'tooltip': None
            })
            if not self.isExpanded(self.i18n['UI_setting_experience_header']):
                return header
            data = header + data
            return data

    def getModuleStatus(self, modulesNeedXP, isModulesReady):
        exp, avgXP, freeXP = self.getExperienceInfo()
        data = []
        if self.data['showModuleStatus']:
            formatData = self.getExpStringFormat()
            modules_exp = modulesNeedXP
            modulesNeedXP -= exp
            if self.data['useFreeExp']:
                modulesNeedXP -= freeXP
            if modulesNeedXP > 0:
                modules_battles = modulesNeedXP / avgXP if avgXP > 0 else 1
                modules_battles = self.getNumber(modules_battles)
                formatData['need-exp'] = self.getNumber(modules_exp)
                formatData['chk-exp'] = self.getNumber(modulesNeedXP)
                formatData['battles-left'] = modules_battles if avgXP > 0 else 'X'
                data.extend(self.pack(self.i18n['UI_setting_moduleStatusTitle_text'].format(**formatData), self.i18n['UI_setting_moduleStatus_text'].format(**formatData)))
            elif isModulesReady:
                data.extend(self.pack(self.i18n['UI_setting_moduleStatusReadyTitle_text'].format(**formatData), self.i18n['UI_setting_moduleStatusReady_text'].format(**formatData)))
        return data

    def getEliteStatus(self, isEliteReady, eliteNeedXP, eliteDiscountXP):
        exp, avgXP, freeXP = self.getExperienceInfo()
        data = []
        if self.data['showEliteStatus']:
            formatData = self.getExpStringFormat()
            elite_exp = eliteNeedXP
            eliteNeedXP -= exp + eliteDiscountXP
            if self.data['useFreeExp']:
                eliteNeedXP -= freeXP
            if eliteNeedXP > 0:
                if avgXP > 0:
                    formatData['battles-left'] = self.getNumber(eliteNeedXP / avgXP if avgXP > 0 else 1)
                else:
                    formatData['battles-left'] = 'X'
                formatData['need-exp'] = self.getNumber(elite_exp)
                formatData['chk-exp'] = self.getNumber(eliteNeedXP)
                formatData['discount'] = self.getNumber(eliteDiscountXP)
                data.extend(self.pack(self.i18n['UI_setting_eliteStatusTitle_text'].format(**formatData), self.i18n['UI_setting_eliteStatus_text'].format(**formatData), self.i18n['UI_setting_eliteStatus_tooltip'].format(**formatData) if eliteDiscountXP else None))
            elif isEliteReady:
                data.extend(self.pack(self.i18n['UI_setting_eliteStatusReadyTitle_text'].format(**formatData), self.i18n['UI_setting_eliteStatusReady_text'].format(**formatData)))
        return data

    def getNextTankStatus(self, researchVehicles):
        exp, avgXP, freeXP = self.getExperienceInfo()
        data = []
        if self.data['showNextVehicle']:
            for vehicle_id in researchVehicles:
                formatData = self.getExpStringFormat()
                formatData['tank-name'] = researchVehicles[vehicle_id]['vehicle'].shortUserName
                researchVehicles[vehicle_id]['exp_need'] = researchVehicles[vehicle_id]['exp']
                researchVehicles[vehicle_id]['exp'] -= exp + researchVehicles[vehicle_id]['discount']
                if self.data['useFreeExp']:
                    researchVehicles[vehicle_id]['exp'] -= freeXP
                if researchVehicles[vehicle_id]['exp'] > 0:
                    researchVehicles[vehicle_id]['battles'] = researchVehicles[vehicle_id]['exp'] / avgXP if avgXP > 0 else 1
                    researchVehicles[vehicle_id]['battles'] = self.getNumber(researchVehicles[vehicle_id]['battles'])
                    formatData['need-exp'] = self.getNumber(researchVehicles[vehicle_id]['exp_need'])
                    formatData['chk-exp'] = self.getNumber(researchVehicles[vehicle_id]['exp'])
                    formatData['battles-left'] = researchVehicles[vehicle_id]['battles'] if avgXP > 0 else 'X'
                    formatData['discount'] = self.getNumber(researchVehicles[vehicle_id]['discount'])
                    data.extend(self.pack(self.i18n['UI_setting_nextTanksTitle_text'].format(**formatData), self.i18n['UI_setting_nextTanks_text'].format(**formatData), self.i18n['UI_setting_nextTanks_tooltip'].format(**formatData) if researchVehicles[vehicle_id]['discount'] else None))
                data.extend(self.pack(self.i18n['UI_setting_nextTanksReadyTitle_text'].format(**formatData), self.i18n['UI_setting_nextTanksReady_text'].format(**formatData)))

        return data

    def getQuestCondition(self, conditionType, texts):
        data = []
        text = texts.splitlines()
        format_key = 'quest-%s-condition' % conditionType
        for word in text:
            op = textwrap.wrap('%s' % word, 44, break_long_words=False)
            for sight in op:
                if not op.index(sight) and not text.index(word):
                    data.extend(self.pack(self.i18n['UI_text_%s_condition_extra' % conditionType], self.i18n['UI_text_%s_condition' % conditionType].format(**{format_key: sight}), tooltip=texts))
                data.extend(self.pack('', self.i18n['UI_text_%s_condition' % conditionType].format(**{format_key: sight}), tooltip=texts))

        return data

    def getNumber(self, number):
        return self.truncate(number) if self.data['isTruncateNumbers'] else getIntegralFormat(number)

    def getExpStringFormat(self):
        return {
            'tank-name': g_currentVehicle.item.shortUserName,
            'cur-tank-exp': self.getNumber(g_currentVehicle.item.xp),
            'freeXp': self.getNumber(self.itemsCache.items.stats.freeXP)
        }

    def getExperienceInfo(self):
        return g_currentVehicle.item.xp, self.getAvgXP(), self.itemsCache.items.stats.freeXP

    def getHeader(self, header):
        return [{
            'buffIconSrc': '',
            'state': 'simpleTop',
            'isOpen': self.isExpanded(header),
            'tooltip': 'default',
            'isEnabled': True,
            'paramID': header,
            'titleText': '<font face=\'$TitleFont\' size=\'15\' color=\'#E9E2BF\'>%s</font>' % header,
            'valueText': '<font face=\'$TitleFont\' size=\'14\' color=\'#f5f0e5\'></font>'
        }]

    @staticmethod
    def pack(valueText, titleText, tooltip=None):
        return [{
            'buffIconSrc': '',
            'isOpen': False,
            'isEnabled': False,
            'iconSource': '',
            'state': 'advanced',
            'tooltip': 'default' if tooltip else None,
            'paramID': tooltip,
            'titleText': '<font face=\'$FieldFont\' size=\'14\' color=\'#8C8C7E\'>%s</font>' % titleText,
            'valueText': '<font face=\'$FieldFont\' size=\'14\' color=\'#E9E2BF\'>%s</font>' % valueText
        }]

    def getAvgXP(self):
        avgXP = self.itemsCache.items.getVehicleDossier(g_currentVehicle.item.intCD).getRandomStats().getAvgXP()
        return 0 if avgXP is None else avgXP

    @staticmethod
    def getExperienceStatus(vehicles):
        modulesNeedXP = 0
        eliteNeedXP = 0
        eliteDiscountXP = 0
        researchVehicles = {}
        isEliteReady = False
        isModulesReady = False
        for unlocks in g_currentVehicle.item.descriptor.type.unlocksDescrs:
            compactDescr = unlocks[1]
            if compactDescr in vehicles:
                vehicle = vehicles[compactDescr]
                if vehicle and not vehicle.isUnlocked:
                    isAvailable, cost, need, fullCost, discount = getUnlockPrice(compactDescr, g_currentVehicle.item.intCD, vehicle.level)
                    researchVehicles[compactDescr] = {'exp': fullCost, 'battles': 1, 'vehicle': vehicle, 'discount': fullCost - cost}
                    eliteNeedXP += fullCost
                    eliteDiscountXP += fullCost - cost
                    isEliteReady = True
                    for research in unlocks[1:]:
                        isAvailable, cost, need, fullCost, discount = getUnlockPrice(research, g_currentVehicle.item.intCD, vehicle.level)
                        if not isAvailable:
                            researchVehicles[compactDescr]['exp'] += fullCost
                            researchVehicles[compactDescr]['discount'] += discount

            isAvailable, cost, need, defCost, discount = getUnlockPrice(compactDescr, g_currentVehicle.item.intCD)
            if not isAvailable:
                modulesNeedXP += cost
                eliteNeedXP += cost
                isEliteReady = True
                isModulesReady = True

        return modulesNeedXP, eliteNeedXP, eliteDiscountXP, researchVehicles, isEliteReady, isModulesReady

    @staticmethod
    def truncate(value):
        value = float(value)
        if value < 1000:
            return '%s' % int(value)
        elif value < 100000:
            return '{:0.1f}k'.format(value / 1000.0)
        elif value < 1000000:
            return '{0:d}k'.format(int(math.ceil(value / 1000.0)))
        else:
            return '{:0.1f}M'.format(value / 1000000.0)


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(VehParamsDataProvider, 'buildList')
def new_buildList(func, self, cache):
    if not config.data['enabled']:
        return func(self, cache)
    self.clear()
    self._cache = cache
    info = config.getInfo()
    if config.data['showVehicleInfo']:
        func(self, cache)
        info.extend(self._list)
    if len(info) == 0:
        info.append({'state': HANGAR_ALIASES.VEH_PARAM_RENDERER_STATE_SEPARATOR, 'isEnabled': False, 'tooltip': ''})
    self._list = info


@override(VehicleParameters, 'onParamClick')
def new_onParamClick(func, self, paramID):
    try:
        func(self, paramID)
    except KeyError:
        config.setExpanded(paramID, not config.isExpanded(paramID))
        self._setDPUseAnimAndRebuild(False)
