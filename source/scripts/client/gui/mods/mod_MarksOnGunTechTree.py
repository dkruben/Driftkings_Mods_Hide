# -*- coding: utf-8 -*-
import math

import BigWorld
from CurrentVehicle import g_currentVehicle
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK
from dossiers2.ui.achievements import MARK_OF_MASTERY_RECORD
from dossiers2.ui.achievements import MARK_ON_GUN_RECORD
from gui.Scaleform.daapi.view.lobby.hangar.hangar_header import HangarHeader
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.Scaleform.daapi.view.lobby.techtree.dumpers import NationObjDumper
from gui.Scaleform.lobby_entry import LobbyEntry
from gui.Scaleform.locale.MENU import MENU as MU
from gui.shared.formatters import text_styles

from DriftkingsCore import SimpleConfigInterface, Analytics, override, callback


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.1.5 (%(file_compile_date)s)'
        self.author = 'orig. by spoter'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'showInTechTree': True,
            'showInTechTreeMarkOfGunPercent': True,
            'showInTechTreeMastery': True,
            'showInHangar': True,
            'techTreeX': 75,
            'techTreeY': -12,
            'techTreeHeight': 16,
            'techTreeWidth': 54,
            'colorRatting': {
                'neutral': '#FFFFFF',
                'very_bad': '#FF6347',
                'bad': '#FE7903',
                'normal': '#F8F400',
                'good': '#60FF00',
                'very_good': '#02C9B3',
                'unique': '#D042F3'
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': self.version,
            'UI_setting_showInTechTree_text': 'TechTree: enabled',
            'UI_setting_showInTechTree_tooltip': '',
            'UI_setting_showInTechTreeMastery_text': 'TechTree: show Mastery',
            'UI_setting_showInTechTreeMastery_tooltip': '',
            'UI_setting_showInTechTreeMarkOfGunPercent_text': 'TechTree: show MoE %',
            'UI_setting_showInTechTreeMarkOfGunPercent_tooltip': '',
            'UI_setting_showInTechTreeMarkOfGunTankNameColored_text': 'TechTree: MoE colorize vehicle name',
            'UI_setting_showInTechTreeMarkOfGunTankNameColored_tooltip': '',
            'UI_setting_showInHangar_text': 'Hangar: Show MoE mod',
            'UI_setting_showInHangar_tooltip': '',
            'UI_HangarStatsStart': '<b>{currentPercent}<font size=\'14\'>[{currentDamage}]</font> </b>',
            'UI_HangarStatsEnd': '{c_damageToMark65}, {c_damageToMark85}\n{c_damageToMark95}, {c_damageToMark100}'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showInTechTree'),
                self.tb.createControl('showInTechTreeMastery'),
                self.tb.createControl('showInTechTreeMarkOfGunPercent'),
                self.tb.createControl('showInHangar')],
            'column2': []
        }


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')
MARKS = [
    '   ',
    '<font face="Arial" color="%s"><b>  &#11361;</b></font>' % config.data['colorRatting']['good'],
    '<font face="Arial" color="%s"><b> &#11361;&#11361;</b></font>' % config.data['colorRatting']['very_good'],
    '<font face="Arial" color="%s"><b>&#11361;&#11361;&#11361;</b></font>' % config.data['colorRatting']['unique']
]

battleDamageRating0 = config.data['colorRatting']['very_bad']
battleDamageRating20 = config.data['colorRatting']['very_bad']
battleDamageRating40 = config.data['colorRatting']['bad']
battleDamageRating55 = config.data['colorRatting']['bad']
battleDamageRating65 = config.data['colorRatting']['normal']
battleDamageRating85 = config.data['colorRatting']['good']
battleDamageRating95 = config.data['colorRatting']['very_good']
battleDamageRating100 = config.data['colorRatting']['unique']

battleDamageRating = [battleDamageRating0, battleDamageRating20, battleDamageRating40, battleDamageRating55, battleDamageRating65, battleDamageRating85, battleDamageRating95, battleDamageRating100]

LEVELS = [0.0, 20.0, 40.0, 55.0, 65.0, 85.0, 95.0, 100.0]


class MarksInTechTree(object):

    @staticmethod
    def normalizeDigits(value):
        return int(math.ceil(value))

    @staticmethod
    def normalizeDigitsCoEff(value):
        return int(math.ceil(math.ceil(value / 10.0)) * 10)

    @staticmethod
    def percent(ema, start, end, d, p):
        while start <= end < 100.001 and ema < 30000:
            ema += 0.1
            start = ema / d * p

        return ema

    def statistics(self, p, d):
        pC = math.floor(p) + 1
        dC = self.percent(d, p, pC, d, p)
        p20 = self.percent(0, 0.0, 20.0, d, p)
        p40 = self.percent(0, 0.0, 40.0, d, p)
        p55 = self.percent(0, 0.0, 55.0, d, p)
        p65 = self.percent(0, 0.0, 65.0, d, p)
        p85 = self.percent(0, 0.0, 85.0, d, p)
        p95 = self.percent(0, 0.0, 95.0, d, p)
        p100 = self.percent(0, 0.0, 100.0, d, p)
        data = [0, p20, p40, p55, p65, p85, p95, p100]
        idx = filter(lambda x: x >= p, LEVELS)[0]
        limit1 = dC
        limit2 = data[LEVELS.index(idx)]
        check = LEVELS.index(idx)
        delta = limit2 - limit1
        for value in xrange(len(data)):
            if data[value] == limit1 or data[value] == limit2:
                continue
            if value > check:
                data[value] = self.normalizeDigitsCoEff(data[value] + delta)

        if pC == 101:
            pC = 100
            dC = data[7]
        return pC, dC, data[1], data[2], data[3], data[4], data[5], data[6], data[7]


g_marks = MarksInTechTree()


def htmlHangarBuilder():
    self = BigWorld.MoEHangarHTML
    if self.flashObject:
        self.flashObject.txtTankInfoName.htmlText = '<TEXTFORMAT INDENT="0" LEFTMARGIN="0" RIGHTMARGIN="0" LEADING="1"><P ALIGN="LEFT"><FONT FACE="$FieldFont" SIZE="16" COLOR="#FEFEEC" KERNING="0">%s</FONT></P></TEXTFORMAT>' % self.moeStart
        self.flashObject.txtTankInfoLevel.htmlText = '<TEXTFORMAT INDENT="0" LEFTMARGIN="0" RIGHTMARGIN="0" LEADING="1"><P ALIGN="LEFT"><FONT FACE="$FieldFont" SIZE="14" COLOR="#E9E2BF" KERNING="0">%s</FONT></P></TEXTFORMAT>' % self.moeEnd


@override(HangarHeader, '_makeHeaderVO')
def makeHeaderVO(func, *args):
    result = func(*args)
    if config.data['showInHangar'] and 'tankInfoName' in result:
        self = args[0]
        vehicle = self._currentVehicle.item
        targetData = g_currentVehicle.getDossier()
        damageRating = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
        moeStart = ''
        moeEnd = ''
        if damageRating:
            damage = ProfileUtils.getValueOrUnavailable(
                ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamage()))
            # noinspection PyProtectedMember
            track = ProfileUtils.getValueOrUnavailable(
                targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2,
                                                         targetData.getRandomStats().getDamageAssistedTrack))
            # noinspection PyProtectedMember
            radio = ProfileUtils.getValueOrUnavailable(
                targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedRadio))
            stun = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamageAssistedStun())
            currentDamage = int(damage + max(track, radio, stun))
            movingAvgDamage = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
            pC, dC, p20, p40, p55, p65, p85, p95, p100 = g_marks.statistics(damageRating, movingAvgDamage)
            color = ['#F8F400', '#F8F400', '#60FF00', '#02C9B3', '#D042F3', '#D042F3']
            levels = [p55, p65, p85, p95, p100, 10000000]
            currentDamaged = '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= currentDamage, levels)[0])], currentDamage)
            currentMovingAvgDamage = '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= movingAvgDamage, levels)[0])], movingAvgDamage)
            data = {
                'currentPercent': '%s%%' % damageRating,
                'currentMovingAvgDamage': currentMovingAvgDamage,
                'currentDamage': currentDamaged if currentDamage > movingAvgDamage else currentMovingAvgDamage,
                'nextPercent': '<font color="%s">%s%%</font>' % (battleDamageRating[LEVELS.index(filter(lambda x: x >= pC, LEVELS)[0])], pC),
                'needDamage': '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= int(dC), levels)[0])], int(dC)),
                'c_damageToMark20': '<font color="%s"><b>20%%:%s</b></font>' % (config.data['colorRatting']['very_bad'], g_marks.normalizeDigits(p20)),
                'c_damageToMark40': '<font color="%s"><b>40%%:%s</b></font>' % (config.data['colorRatting']['bad'], g_marks.normalizeDigits(p40)),
                'c_damageToMark55': '<font color="%s"><b>55%%:%s</b></font>' % (config.data['colorRatting']['normal'], g_marks.normalizeDigits(p55)),
                'c_damageToMark65': '<font color="%s"><b>65%%:%s</b></font>' % (config.data['colorRatting']['good'], g_marks.normalizeDigits(p65)),
                'c_damageToMark85': '<font color="%s"><b>85%%:%s</b></font>' % (config.data['colorRatting']['very_good'], g_marks.normalizeDigits(p85)),
                'c_damageToMark95': '<font color="%s"><b>95%%:%s</b></font>' % (config.data['colorRatting']['unique'], g_marks.normalizeDigits(p95)),
                'c_damageToMark100': '<font color="%s"><b>100%%:%s</b></font>' % (config.data['colorRatting']['unique'], g_marks.normalizeDigits(p100))
            }
            moeStart = text_styles.promoSubTitle(config.i18n['UI_HangarStatsStart'].format(**data))
            moeEnd = text_styles.stats(config.i18n['UI_HangarStatsEnd'].format(**data))
        oldData = '<b>%s%s %s</b>' % (moeStart, text_styles.promoSubTitle(vehicle.shortUserName), text_styles.stats(MU.levels_roman(vehicle.level)))
        self.moeStart = text_styles.concatStylesToMultiLine(oldData, moeEnd)
        self.moeEnd = moeEnd
        BigWorld.MoEHangarHTML = self
        callback(0.1, htmlHangarBuilder)
    if config.data['showInHangar'] and 'tankInfo' in result:
        self = args[0]
        vehicle = self._currentVehicle.item
        targetData = g_currentVehicle.getDossier()
        damageRating = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
        moeStart = ''
        moeEnd = ''
        if damageRating:
            damage = ProfileUtils.getValueOrUnavailable(
                ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamage()))
            # noinspection PyProtectedMember
            track = ProfileUtils.getValueOrUnavailable(
                targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2,
                                                         targetData.getRandomStats().getDamageAssistedTrack))
            # noinspection PyProtectedMember
            radio = ProfileUtils.getValueOrUnavailable(
                targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2,
                                                         targetData.getRandomStats().getDamageAssistedRadio))
            stun = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamageAssistedStun())
            currentDamage = int(damage + max(track, radio, stun))
            movingAvgDamage = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
            pC, dC, p20, p40, p55, p65, p85, p95, p100 = g_marks.statistics(damageRating, movingAvgDamage)
            color = ['#F8F400', '#F8F400', '#60FF00', '#02C9B3', '#D042F3', '#D042F3']
            levels = [p55, p65, p85, p95, p100, 10000000]
            currentDamaged = '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= currentDamage, levels)[0])], currentDamage)
            currentMovingAvgDamage = '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= movingAvgDamage, levels)[0])], movingAvgDamage)
            data = {
                'currentPercent': '%s%%' % damageRating,
                'currentMovingAvgDamage': currentMovingAvgDamage,
                'currentDamage': currentDamaged if currentDamage > movingAvgDamage else currentMovingAvgDamage,
                'nextPercent': '<font color="%s">%s%%</font>' % (battleDamageRating[LEVELS.index(filter(lambda x: x >= pC, LEVELS)[0])], pC),
                'needDamage': '<font color="%s">%s</font>' % (color[levels.index(filter(lambda x: x >= int(dC), levels)[0])], int(dC)),
                'c_damageToMark20': '<font color="%s"><b>20%%:%s</b></font>' % (config.data['colorRatting']['very_bad'], g_marks.normalizeDigits(p20)),
                'c_damageToMark40': '<font color="%s"><b>40%%:%s</b></font>' % (config.data['colorRatting']['bad'], g_marks.normalizeDigits(p40)),
                'c_damageToMark55': '<font color="%s"><b>55%%:%s</b></font>' % (config.data['colorRatting']['normal'], g_marks.normalizeDigits(p55)),
                'c_damageToMark65': '<font color="%s"><b>65%%:%s</b></font>' % (config.data['colorRatting']['good'], g_marks.normalizeDigits(p65)),
                'c_damageToMark85': '<font color="%s"><b>85%%:%s</b></font>' % (config.data['colorRatting']['very_good'], g_marks.normalizeDigits(p85)),
                'c_damageToMark95': '<font color="%s"><b>95%%:%s</b></font>' % (config.data['colorRatting']['unique'], g_marks.normalizeDigits(p95)),
                'c_damageToMark100': '<font color="%s"><b>100%%:%s</b></font>' % (config.data['colorRatting']['unique'], g_marks.normalizeDigits(p100))
            }
            moeStart = text_styles.promoSubTitle(config.i18n['UI_HangarStatsStart'].format(**data))
            moeEnd = text_styles.stats(config.i18n['UI_HangarStatsEnd'].format(**data))
        oldData = '%s%s %s' % (moeStart, text_styles.promoSubTitle(vehicle.shortUserName),
                               text_styles.stats(MU.levels_roman(vehicle.level)))
        result['tankInfo'] = text_styles.concatStylesToMultiLine(oldData, moeEnd)
    return result


@override(NationObjDumper, '_getVehicleData')
def getExtraInfo(func, *args):
    result = func(*args)
    if config.data['enabled'] and config.data['showInTechTree']:
        dossier = None
        if len(args) > 2:
            item = args[2]
            dossier = g_currentVehicle.itemsCache.items.getVehicleDossier(item.intCD)
        else:
            try:
                # noinspection PyProtectedMember
                item = args[1]._RealNode__item
                dossier = g_currentVehicle.itemsCache.items.getVehicleDossier(item.intCD)
            except StandardError:
                pass
        if dossier:
            percent = ''
            markOfGun = dossier.getTotalStats().getAchievement(MARK_ON_GUN_RECORD)
            markOfGunValue = markOfGun.getValue()
            markOfGunStars = '%s ' % MARKS[markOfGun.getValue()]
            color = ['#F8F400', '#60FF00', '#02C9B3', '#D042F3']
            percents = float(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0)
            if config.data['showInTechTreeMarkOfGunPercent'] and percents:
                percent = '%.2f' % percents if percents < 100 else '100.0'
                percent = '%s%%' % percent.rjust(5)
            mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
            masteryValue = mastery.getValue()
            if config.data['showInTechTreeMastery'] and masteryValue and masteryValue < 5:
                markOfGunStars = '<img src="%s" width="16" height="16" vspace="-16"/></img>' % mastery.getSmallIcon().replace('../', '')
            percentText = '||%s<font color="%s">%s</font>||%s||%s||%s||%s' % (markOfGunStars, color[markOfGunValue], percent, config.data['techTreeX'], config.data['techTreeY'], config.data['techTreeHeight'], config.data['techTreeWidth'])
            result['nameString'] += percentText
    return result


@override(LobbyEntry, '_getRequiredLibraries')
def new_getRequiredLibraries(func, *args):
    return func(*args) + ['marksInTechtree.swf',]
