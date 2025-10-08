# -*- coding: utf-8 -*-
import math

import BigWorld
from CurrentVehicle import g_currentVehicle
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_OF_MASTERY_RECORD, MARK_ON_GUN_RECORD
from gui.Scaleform.daapi.view.lobby.hangar.hangar_header import HangarHeader
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.Scaleform.daapi.view.lobby.techtree.dumpers import NationObjDumper
from gui.Scaleform.lobby_entry import LobbyEntry
from gui.Scaleform.locale.MENU import MENU as MU
from gui.shared.formatters import text_styles

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, callback, calculate_version, color_tables, getColor, logError


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
            'techTreeMarkHeight': 24,
            'techTreeMarkWidth': 100,
            'showMasteryBadgeHeight': 16,
            'showMasteryBadgeWidth': 16,
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
        # Safeguard against division by zero or invalid values
        if d <= 0 or p <= 0:
            return 0
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
        # Find the index directly instead of finding value then index
        check = next((i for i, x in enumerate(self.levels_mog) if x >= p), len(self.levels_mog) - 1)
        limit1 = dC
        limit2 = data[check]
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
    def calculateDamageData(targetData, damageRating):
        damage = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamage())
        track = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedTrack))
        radio = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedRadio))
        stun = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamageAssistedStun())
        # Ensure all values are numeric before using max()
        try:
            damage = float(damage) if isinstance(damage, (int, float)) else 0
            track = float(track) if isinstance(track, (int, float)) else 0
            radio = float(radio) if isinstance(radio, (int, float)) else 0
            stun = float(stun) if isinstance(stun, (int, float)) else 0
        except (ValueError, TypeError):
            damage, track, radio, stun = 0, 0, 0, 0
        current_damage = int(damage + max(track, radio, stun))
        moving_avg_damage = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
        pC, dC, p20, p40, p55, p65, p85, p95, p100 = g_marks.statistics(damageRating * 100, moving_avg_damage)
        return current_damage, moving_avg_damage, pC, dC, p20, p40, p55, p65, p85, p95, p100

    @staticmethod
    def htmlHangarBuilder():
        self = getattr(BigWorld, 'MoEHangarHTML', None)
        if self is not None and hasattr(self, 'flashObject') and self.flashObject:
            self.flashObject.txtTankInfoName.htmlText = '<TEXTFORMAT INDENT="0" LEFTMARGIN="0" RIGHTMARGIN="0" LEADING="1"><P ALIGN="LEFT"><FONT FACE="$FieldFont" SIZE="16" COLOR="#FEFEEC" KERNING="0">%s</FONT></P></TEXTFORMAT>' % self.moeStart
            self.flashObject.txtTankInfoLevel.htmlText = '<TEXTFORMAT INDENT="0" LEFTMARGIN="0" RIGHTMARGIN="0" LEADING="1"><P ALIGN="LEFT"><FONT FACE="$FieldFont" SIZE="14" COLOR="#E9E2BF" KERNING="0">%s</FONT></P></TEXTFORMAT>' % self.moeEnd


g_marks = MarksInTechTree()


@override(HangarHeader, '_makeHeaderVO')
def new_makeHeaderVO(func, *args):
    result = func(*args)
    if config.data['enabled'] and config.data['showInHangar'] and 'tankInfoName' in result:
        try:
            self = args[0]
            vehicle = self._currentVehicle.item
            target_data = g_currentVehicle.getDossier()
            try:
                damage_rating = target_data.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
                if not damage_rating:
                    return result
            except (AttributeError, TypeError, ZeroDivisionError):
                return result
            current_damaged, moving_avg_damage, pC, dC, p20, p40, p55, p65, p85, p95, p100 = g_marks.calculateDamageData(target_data, damage_rating)
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
            try:
                current_damage_color_index = next((index for index, value in enumerate(levels) if value >= current_damaged), 0)
                if current_damage_color_index >= len(colors):
                    current_damage_color_index = len(colors) - 1
            except (ValueError, TypeError):
                current_damage_color_index = 0
            try:
                moving_avg_damage_color_index = next((index for index, value in enumerate(levels) if value >= moving_avg_damage), 0)
                if moving_avg_damage_color_index >= len(colors):
                    moving_avg_damage_color_index = len(colors) - 1
            except (ValueError, TypeError):
                moving_avg_damage_color_index = 0
            current_damaged_str = '<font color="%s">%s</font>' % (colors[current_damage_color_index], current_damaged)
            current_moving_avg_damage_str = '<font color="%s">%s</font>' % (colors[moving_avg_damage_color_index], moving_avg_damage)
            current_damage_display = current_damaged_str if current_damaged > moving_avg_damage else current_moving_avg_damage_str
            data = {
                'currentPercent': '%.1f%%' % (damage_rating * 100),
                'currentMovingAvgDamage': current_moving_avg_damage_str,
                'currentDamage': current_damage_display,
                'nextPercent': '<font color="%s">%s%%</font>' % (config.read_colors('good', pC), pC),
                'needDamage': '<font color="%s">%s</font>' % (colors[min(next((index for index, value in enumerate(levels) if value >= int(dC)), 0), len(colors) - 1)], int(dC)),
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
        except Exception as e:
            logError(config.ID, "error in new_makeHeaderVO:", e)
    return result


@override(NationObjDumper, '_getVehicleData')
def new_getVehicleData(func, *args):
    result = func(*args)
    if not (config.data['enabled'] and config.data['showInTechTree']):
        return result
    try:
        item = None
        if len(args) > 2:
            item = args[2]
        else:
            try:
                item = args[1]._RealNode__item
            except Exception:
                try:
                    item = args[1].getItem()
                except Exception:
                    item = None
        dossier = None
        if item is not None:
            try:
                dossier = g_currentVehicle.itemsCache.items.getVehicleDossier(item.intCD)
            except Exception:
                dossier = None
        if not dossier:
            return result
        # Mark of Gun (MoG)
        try:
            mog = dossier.getTotalStats().getAchievement(MARK_ON_GUN_RECORD)
            mog_val = int(mog.getValue()) if mog is not None else 0
        except Exception:
            mog_val = 0
        try:
            mark_html = g_marks.marks_mog[mog_val] if 0 <= mog_val < len(g_marks.marks_mog) else g_marks.marks_mog[0]
        except Exception:
            mark_html = ''
        percent_html = ''
        if config.data['showInTechTreeMarkOfGunPercent']:
            try:
                damage_rating = float(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') or 0.0)
                percent_value = min(damage_rating / 100.0, 100.0)
                if percent_value > 0:
                    color = config.read_colors('moe', percent_value)
                    percent_html = '<font color="%s">%.1f%%</font>' % (color, percent_value)
            except Exception:
                percent_html = ''
        mastery_html = ''
        if config.data['showInTechTreeMastery']:
            try:
                mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
                mv = int(mastery.getValue()) if mastery is not None else 0
                if mv and mv < 5:
                    icon = mastery.getSmallIcon().replace('../', '')
                    mastery_html = '<img src="%s" width="%d" height="%d" vspace="-%d"/>' % (icon, config.data.get('showMasteryBadgeWidth', 16), config.data.get('showMasteryBadgeHeight', 16), config.data.get('showMasteryBadgeHeight', 16))
            except Exception:
                mastery_html = ''
        try:
            posX = str(int(config.data.get('techTreeX', 75)))
        except (ValueError, TypeError):
            posX = "75"
        try:
            posY = str(int(config.data.get('techTreeY', -12)))
        except (ValueError, TypeError):
            posY = "-12"
        try:
            markHeight = str(int(config.data.get('techTreeMarkHeight', 24)))
        except (ValueError, TypeError):
            markHeight = "24"
        try:
            markWidth = str(int(config.data.get('techTreeMarkWidth', 100)))
        except (ValueError, TypeError):
            markWidth = "100"
        if 'nameString' in result:
            vehicle_name = result['nameString'].split('||')[0] if '||' in result['nameString'] else result['nameString']
            combined_mark_html = mark_html
            if percent_html:
                combined_mark_html = mark_html + ' ' + percent_html if mark_html else percent_html
            result['nameString'] = '%s||%s||%s||%s||%s||%s||%s' % (vehicle_name, combined_mark_html, posX, posY, markHeight, markWidth, mastery_html)
            if 'markOfExcellence' not in result:
                result['markOfExcellence'] = mog_val
            if 'markOfMastery' not in result and config.data['showInTechTreeMastery']:
                try:
                    mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
                    result['markOfMastery'] = int(mastery.getValue()) if mastery is not None else 0
                except Exception:
                    result['markOfMastery'] = 0
    except Exception as e:
        logError(config.ID, "Error in new_getVehicleData:", str(e))
    return result


@override(LobbyEntry, '_getRequiredLibraries')
def new_getRequiredLibraries(func, *args):
    return func(*args) + ['MarksInTechTree.swf',]
