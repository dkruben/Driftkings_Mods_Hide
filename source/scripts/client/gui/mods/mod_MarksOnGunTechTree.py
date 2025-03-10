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

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, callback, calculate_version, color_tables, getColor


class ConfigInterface(DriftkingsConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.2.0 (%(file_compile_date)s)'
        self.author = 'orig. by spoter, reworked by Driftkings'
        self.data = {
            'enabled': True,
            'colorRatting': 0,
            'showInTechTree': True,
            'showInTechTreeMarkOfGunPercent': True,
            'showInTechTreeMastery': True,
            'showInHangar': True,
            'techTreeX': 75,
            'techTreeY': -12,
            'techTreeHeight': 16,
            'techTreeWidth': 54,
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
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

    def read_colors(self, rating_color, rating_value):
        colors = color_tables[self.data['colorRatting']].get('colors')
        return getColor(colors, rating_color, rating_value)


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


class MarksInTechTree(object):
    def __init__(self):
        self.marks_mog = [
            '   ',
            '<font face="Arial" color="%s"><b>  &#11361;</b></font>' % config.read_colors('moe', 65.0),
            '<font face="Arial" color="%s"><b> &#11361;&#11361;</b></font>' % config.read_colors('moe', 85.0),
            '<font face="Arial" color="%s"><b>&#11361;&#11361;&#11361;</b></font>' % config.read_colors('moe', 95.0)
        ]
        self.levels_mog = [0.0, 20.0, 40.0, 55.0, 65.0, 85.0, 95.0, 100.0]


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
        idx = next((x for x in self.levels_mog if x >= p), None)
        if idx is None:
            raise ValueError("No level found for the given percent.")
        limit1 = dC
        limit2 = data[self.levels_mog.index(idx)]
        check = self.levels_mog.index(idx)
        delta = limit2 - limit1
        for value in range(len(data)):
            if data[value] == limit1 or data[value] == limit2:
                continue
            if value > check:
                data[value] = self.normalizeDigitsCoEff(data[value] + delta)
        if pC == 101:
            pC = 100
            dC = data[7]
        return pC, dC, data[1], data[2], data[3], data[4], data[5], data[6], data[7]

    @staticmethod
    def calculate_damage_data(target_data, damage_rating):
        damage = ProfileUtils.getValueOrUnavailable(target_data.getRandomStats().getAvgDamage())
        track = ProfileUtils.getValueOrUnavailable(target_data.getRandomStats()._getAvgValue(target_data.getRandomStats().getBattlesCountVer2, target_data.getRandomStats().getDamageAssistedTrack))
        radio = ProfileUtils.getValueOrUnavailable(target_data.getRandomStats()._getAvgValue(target_data.getRandomStats().getBattlesCountVer2, target_data.getRandomStats().getDamageAssistedRadio))
        stun = ProfileUtils.getValueOrUnavailable(target_data.getRandomStats().getAvgDamageAssistedStun())
        current_damage = int(damage + max(track, radio, stun))
        moving_avg_damage = target_data.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
        pC, dC, p20, p40, p55, p65, p85, p95, p100 = g_marks.statistics(damage_rating, moving_avg_damage)
        return current_damage, moving_avg_damage, pC, dC, p20, p40, p55, p65, p85, p95, p100

    @staticmethod
    def htmlHangarBuilder():
        self = BigWorld.MoEHangarHTML
        if self.flashObject:
            self.flashObject.txtTankInfoName.htmlText = '<TEXTFORMAT INDENT="0" LEFTMARGIN="0" RIGHTMARGIN="0" LEADING="1"><P ALIGN="LEFT"><FONT FACE="$FieldFont" SIZE="16" COLOR="#FEFEEC" KERNING="0">%s</FONT></P></TEXTFORMAT>' % self.moeStart
            self.flashObject.txtTankInfoLevel.htmlText = '<TEXTFORMAT INDENT="0" LEFTMARGIN="0" RIGHTMARGIN="0" LEADING="1"><P ALIGN="LEFT"><FONT FACE="$FieldFont" SIZE="14" COLOR="#E9E2BF" KERNING="0">%s</FONT></P></TEXTFORMAT>' % self.moeEnd


g_marks = MarksInTechTree()


@override(HangarHeader, '_makeHeaderVO')
def new_makeHeaderVO(func, *args):
    result = func(*args)
    if config.data['showInHangar'] and 'tankInfoName' in result:
        self = args[0]
        vehicle = self._currentVehicle.item
        target_data = g_currentVehicle.getDossier()
        damage_rating = target_data.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
        if not damage_rating:
            return result
        current_damaged, moving_avg_damage, pC, dC, p20, p40, p55, p65, p85, p95, p100 = g_marks.calculate_damage_data(target_data, damage_rating)
        colors = [
            config.read_colors('very_bad', 20.0),
            config.read_colors('bad', 40.0),
            config.read_colors('normal', 55.0),
            config.read_colors('good', 65.0),
            config.read_colors('very_good', 85.0),
            config.read_colors('unique', 95.0),
            config.read_colors('super_unique', 100.0)
        ]
        levels = [p55, p65, p85, p95, p100, 10000000]
        current_damage_color_index = next((index for index, value in enumerate(levels) if value >= current_damaged), None)
        moving_avg_damage_color_index = next((index for index, value in enumerate(levels) if value >= moving_avg_damage), None)
        current_damaged = '<font color="%s">%s</font>' % (colors[current_damage_color_index], current_damaged)
        current_moving_avg_damage = '<font color="%s">%s</font>' % (colors[moving_avg_damage_color_index], moving_avg_damage)
        data = {
            'currentPercent': '%s%%' % damage_rating,
            'currentMovingAvgDamage': current_moving_avg_damage,
            'currentDamage': current_damaged if current_damaged > moving_avg_damage else current_moving_avg_damage,
            'nextPercent': '<font color="%s">%s%%</font>' % (config.read_colors('good', pC), pC),
            'needDamage': '<font color="%s">%s</font>' % (colors[next((index for index, value in enumerate(levels) if value >= int(dC)), None)], int(dC)),
            'c_damageToMark20': '<font color="%s"><b>20%%:%s</b></font>' % (colors[0], g_marks.normalizeDigits(p20)),
            'c_damageToMark40': '<font color="%s"><b>40%%:%s</b></font>' % (colors[1], g_marks.normalizeDigits(p40)),
            'c_damageToMark55': '<font color="%s"><b>55%%:%s</b></font>' % (colors[2], g_marks.normalizeDigits(p55)),
            'c_damageToMark65': '<font color="%s"><b>65%%:%s</b></font>' % (colors[3], g_marks.normalizeDigits(p65)),
            'c_damageToMark85': '<font color="%s"><b>85%%:%s</b></font>' % (colors[4], g_marks.normalizeDigits(p85)),
            'c_damageToMark95': '<font color="%s"><b>95%%:%s</b></font>' % (colors[5], g_marks.normalizeDigits(p95)),
            'c_damageToMark100': '<font color="%s"><b>100%%:%s</b></font>' % (colors[6], g_marks.normalizeDigits(p100))
        }
        moe_start = text_styles.promoSubTitle(config.i18n['UI_HangarStatsStart'].format(**data))
        moe_end = text_styles.stats(config.i18n['UI_HangarStatsEnd'].format(**data))
        old_data = '<b>%s%s %s</b>' % (moe_start, text_styles.promoSubTitle(vehicle.shortUserName), text_styles.stats(MU.levels_roman(vehicle.level)))
        self.moeStart = text_styles.concatStylesToMultiLine(old_data, moe_end)
        self.moeEnd = moe_end
        BigWorld.MoEHangarHTML = self
        callback(0.1, g_marks.htmlHangarBuilder)
        if 'tankInfo' in result:
            result['tankInfo'] = old_data + moe_end
    return result


@override(NationObjDumper, '_getVehicleData')
def new__getExtraInfo(func, *args):
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
            mark_of_gun = dossier.getTotalStats().getAchievement(MARK_ON_GUN_RECORD)
            mark_of_gun_value = mark_of_gun.getValue()
            mark_of_gun_stars = '%s ' % g_marks.marks_mog[mark_of_gun.getValue()]
            color = ['#F8F400', '#60FF00', '#02C9B3', '#D042F3']
            percents = float(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0)
            if config.data['showInTechTreeMarkOfGunPercent'] and percents:
                percent = '%.2f' % percents if percents < 100 else '100.0'
                percent = '%s%%' % percent.rjust(5)
            mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
            mastery_value = mastery.getValue()
            if config.data['showInTechTreeMastery'] and mastery_value and mastery_value < 5:
                mark_of_gun_stars = '<img src="%s" width="16" height="16" vspace="-16"/></img>' % mastery.getSmallIcon().replace('../', '')
            percent_text = '||%s<font color="%s">%s</font>||%s||%s||%s||%s' % (mark_of_gun_stars, color[mark_of_gun_value], percent, config.data['techTreeX'], config.data['techTreeY'], config.data['techTreeHeight'], config.data['techTreeWidth'])
            result['nameString'] += percent_text
    return result


@override(LobbyEntry, '_getRequiredLibraries')
def new__getRequiredLibraries(func, *args):
    return func(*args) + ['marksInTechtree.swf',]
