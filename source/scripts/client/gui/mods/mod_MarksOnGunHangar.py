# -*- coding: utf-8 -*-
import math

from CurrentVehicle import g_currentVehicle
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_OF_MASTERY_RECORD
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.Scaleform.framework import ScopeTemplates, ViewSettings, g_entitiesFactories
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.HANGAR_ALIASES import HANGAR_ALIASES
from gui.app_loader.settings import APP_NAME_SPACE
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement
from gui.shared.personality import ServicesLocator

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, logException, logError, calculate_version, color_tables, getColor
from DriftkingsStats import getVehicleInfoData


AS_ALIAS = 'MarksOnGunHangar'
AS_SWF = 'MarksOnGunHangar.swf'

g_controller = None


class ConfigInterface(DriftkingsConfigInterface):
    _FALLBACK_COLORS = {
        'very_bad': '#FF6347',
        'bad': '#FE7903',
        'normal': '#F8F400',
        'good': '#60FF00',
        'very_good': '#02C9B3',
        'unique': '#D042F3',
        'super_unique': '#D042F3'
    }

    def __init__(self):
        self.levels = [20.0, 40.0, 55.0, 65.0, 85.0, 95.0, 100.0]
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.5 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (native hangar Scaleform UI)'
        self.data = {
            'enabled': True,
            'showInHangar': True,
            'showInStatistic': True,
            'textLock': False,
            'showTooltipTargets': True,
            'colorRating': 0,
            'starAnimationWindow': 5.0,
            'panel': {
                'x': 215.0,
                'y': -246.0,
                'width': 360.0,
                'height': 188.0,
                'alignX': 'left',
                'alignY': 'bottom'
            },
            'card': {
                'backgroundColor': 0x101114,
                'backgroundAlpha': 0.94,
                'outlineColor': 0x2B2D33,
                'headerColor': '#C7A86A',
                'titleColor': '#F5F1E8',
                'mutedColor': '#8E949F',
                'lineColor': '#262A31',
                'accentColor': '#E2C07A',
                'accentSoftColor': '#3A2B17',
                'warningColor': '#F3B14B'
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_showInHangar_text': 'Hangar: enabled',
            'UI_setting_showInHangar_tooltip': '',
            'UI_setting_showInStatistic_text': 'Tooltip: enabled',
            'UI_setting_showInStatistic_tooltip': '',
            'UI_setting_showTooltipTargets_text': 'Tooltip: show target levels',
            'UI_setting_showTooltipTargets_tooltip': '',
            'UI_setting_textLock_text': 'Hangar: lock panel position',
            'UI_setting_textLock_tooltip': '',
            'UI_setting_colorRating_text': 'Choose Color Rating',
            'UI_setting_colorRating_tooltip': 'Select the color scheme for MoE, WN8 and winrate',
            'UI_setting_colorRating_NoobMeter': 'NoobMeter',
            'UI_setting_colorRating_XVM': 'XVM',
            'UI_setting_colorRating_WotLabs': 'WotLabs',
            'UI_tooltips': (
                '<font color="#FFFFFF" size="12">{currentMovingAvgDamage} current moving average damage</font>\n'
                '<font color="#FFFFFF" size="12">{currentDamage} current summary damage</font>\n'
                'To <font color="#FFFFFF" size="12">{nextPercent}% </font> need '
                '<font color="#FFFFFF" size="12">{needDamage}</font> moving average damage\n'
                '<font color="#FFFFFF" size="12">{mastery}</font>   '
                '<font color="#FFFFFF" size="12">WN8: {wn8}</font>   '
                '<font color="#FFFFFF" size="12">WR: {winRate}</font>'
            ),
            'UI_tooltipsFull': (
                '<font color="#FFFFFF" size="12">{currentMovingAvgDamage} current moving average damage</font>\n'
                '<font color="#FFFFFF" size="12">{currentDamage} current summary damage</font>\n'
                'To <font color="#FFFFFF" size="12">{nextPercent}% </font> need '
                '<font color="#FFFFFF" size="12">{needDamage}</font> moving average damage\n'
                '<font color="#FFFFFF" size="12">{mastery}</font>   '
                '<font color="#FFFFFF" size="12">WN8: {wn8}</font>   '
                '<font color="#FFFFFF" size="12">WR: {winRate}</font>\n'
                'This statistic is available from the last battle on this vehicle\n'
                'To <font color="#FFFFFF" size="12">20% </font> need <font color="{c20}" size="12">~{_20}</font>\n'
                'To <font color="#FFFFFF" size="12">40% </font> need <font color="{c40}" size="12">~{_40}</font>\n'
                'To <font color="#FFFFFF" size="12">55% </font> need <font color="{c55}" size="12">~{_55}</font>\n'
                'To <font color="#FFFFFF" size="12">65% </font> need <font color="{c65}" size="12">~{_65}</font>\n'
                'To <font color="#FFFFFF" size="12">85% </font> need <font color="{c85}" size="12">~{_85}</font>\n'
                'To <font color="#FFFFFF" size="12">95% </font> need <font color="{c95}" size="12">~{_95}</font>\n'
                'To <font color="#FFFFFF" size="12">100% </font> need <font color="{c100}" size="12">~{_100}</font>'
            )
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        x_color_key = 'UI_setting_colorRating_'
        x_color_list = ('NoobMeter', 'XVM', 'WotLabs')
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showInHangar'),
                self.tb.createControl('showInStatistic'),
                self.tb.createOptions('colorRating', [self.i18n[x_color_key + x] for x in x_color_list])
            ],
            'column2': [
                self.tb.createControl('showTooltipTargets'),
                self.tb.createControl('textLock')
            ]
        }

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)
        if g_controller is not None:
            g_controller.onApplySettings()

    def get_view_config(self):
        panel = dict(self.data['panel'])
        panel['locked'] = bool(self.data['textLock'])
        panel['visible'] = bool(self.data['enabled'] and self.data['showInHangar'])
        panel['starAnimationWindow'] = float(self.data.get('starAnimationWindow', 5.0))
        panel['backgroundColor'] = self.data['card']['backgroundColor']
        panel['backgroundAlpha'] = self.data['card']['backgroundAlpha']
        panel['outlineColor'] = self.data['card']['outlineColor']
        panel['lineColor'] = self.data['card']['lineColor']
        panel['accentColor'] = self.data['card']['accentColor']
        panel['accentSoftColor'] = self.data['card']['accentSoftColor']
        panel['mutedColor'] = self.data['card']['mutedColor']
        panel['warningColor'] = self.data['card']['warningColor']
        panel['starColor65'] = self.getRatingColor('mog', 65.0, 'good')
        panel['starColor85'] = self.getRatingColor('mog', 85.0, 'very_good')
        panel['starColor95'] = self.getRatingColor('mog', 95.0, 'unique')
        return panel

    def readColors(self, rating_color, rating_value):
        try:
            colors = color_tables[self.data['colorRating']].get('colors')
            color = getColor(colors, rating_color, rating_value)
            if color:
                return color
        except Exception:
            pass
        return None

    def getDefaultColor(self, key, default=None):
        return self._FALLBACK_COLORS.get(key, default or self.data['card']['titleColor'])

    def getRatingColor(self, rating_color, rating_value, fallback_key):
        return self.readColors(rating_color, rating_value) or self.getDefaultColor(fallback_key)


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


class MarksOnGunData(object):
    _MASTERY_LABELS = {
        1: '3rd class',
        2: '2nd class',
        3: '1st class',
        4: 'Ace Tanker'
    }

    @staticmethod
    def _safe(value, default=0.0):
        try:
            if value is None or math.isnan(value):
                return default
        except TypeError:
            if value is None:
                return default
        return value

    @staticmethod
    def _normalizeDigits(value):
        return int(math.ceil(value))

    @staticmethod
    def _normalizeDigitsCoeff(value):
        return int(math.ceil(math.ceil(value / 10.0)) * 10)

    @staticmethod
    def _calcPercent(ema, start, end, damage, percent):
        if not damage or not percent:
            return 0.0
        while start <= end < 100.001 and ema < 30000:
            ema += 0.1
            start = ema / damage * percent
        return ema

    @staticmethod
    def _format_int(value):
        return '{:,}'.format(int(value)).replace(',', ' ')

    @staticmethod
    def _format_float(value, digits=2):
        fmt = '%%.%sf' % digits
        return fmt % float(value)

    @staticmethod
    def _escape_html(value):
        text = unicode(value if value is not None else '')
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _mastery_label(self, value):
        return self._MASTERY_LABELS.get(int(value or 0), '--')

    def _pick_color(self, value, levels):
        colors = [
            config.getRatingColor('mog', 55.0, 'normal'),
            config.getRatingColor('mog', 55.0, 'normal'),
            config.getRatingColor('mog', 65.0, 'good'),
            config.getRatingColor('mog', 85.0, 'very_good'),
            config.getRatingColor('mog', 95.0, 'unique'),
            config.getRatingColor('mog', 100.0, 'super_unique')
        ]
        for idx, level in enumerate(levels):
            if value <= level:
                return colors[idx]
        return colors[-1]

    def _color_by_wn8(self, wn8):
        return config.readColors('wn8', wn8) or config.getDefaultColor('unique')

    def _color_by_winrate(self, winrate):
        return config.readColors('winrate', winrate) or config.getDefaultColor('normal')

    def _calculate_wn8(self, vehicle, random_stats, total_stats):
        vehicleCD = getattr(vehicle, 'intCD', None) or getattr(vehicle, 'compactDescr', None)
        if not vehicleCD:
            return 0
        vInfo = getVehicleInfoData(vehicleCD)
        if not vInfo:
            return 0
        expected = {}
        for key in ('wn8expDamage', 'wn8expSpot', 'wn8expFrag', 'wn8expDef', 'wn8expWinRate'):
            expected[key] = self._safe(vInfo.get(key), 0.0)
        if not all(expected.values()):
            return 0
        damage = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgDamage()))
        spot = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgEnemiesSpotted()))
        frags = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgFrags()))
        defence = self._safe(ProfileUtils.getValueOrUnavailable(random_stats._getAvgValue(random_stats.getBattlesCount, random_stats.getDroppedCapturePoints)))
        winrate = self._safe(total_stats.getWinsEfficiency()) * 100.0

        r_damage = float(damage) / max(1.0, expected['wn8expDamage'])
        r_spot = float(spot) / max(1.0, expected['wn8expSpot'])
        r_frag = float(frags) / max(1.0, expected['wn8expFrag'])
        r_def = float(defence) / max(1.0, expected['wn8expDef'])
        r_win = float(winrate) / max(1.0, expected['wn8expWinRate'])

        r_winc = max(0.0, (r_win - 0.71) / (1.0 - 0.71))
        r_damagec = max(0.0, (r_damage - 0.22) / (1.0 - 0.22))
        r_spotc = max(0.0, min(r_damagec + 0.1, max(0.0, (r_spot - 0.38) / (1.0 - 0.38))))
        r_fragc = max(0.0, min(r_damagec + 0.2, max(0.0, (r_frag - 0.12) / (1.0 - 0.12))))
        r_defc = max(0.0, min(r_damagec + 0.1, max(0.0, (r_def - 0.10) / (1.0 - 0.10))))
        return int(980 * r_damagec + 210 * r_damagec * r_fragc + 155 * r_fragc * r_spotc + 75 * r_defc * r_fragc + 145 * min(1.8, r_winc))

    def _get_mastery_info(self, dossier):
        mastery_value = 0
        mastery_icon = ''
        try:
            mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
            if mastery is not None:
                mastery_value = int(mastery.getValue() or 0)
                mastery_icon = mastery.getSmallIcon().replace('../', '')
                if mastery_icon and not mastery_icon.startswith('img://'):
                    mastery_icon = 'img://%s' % mastery_icon
        except Exception:
            mastery_value = 0
            mastery_icon = ''
        return {
            'value': mastery_value,
            'icon': mastery_icon
        }

    def calc_statistics(self, percent, damage):
        percent = self._safe(percent, 0.0)
        damage = self._safe(damage, 0.0)
        if damage <= 0.0:
            damage = 1.0
        next_percent = math.floor(percent) + 1
        next_damage = self._calcPercent(damage, percent, next_percent, damage, percent)
        p20 = self._calcPercent(0.0, 0.0, 20.0, damage, percent)
        p40 = self._calcPercent(0.0, 0.0, 40.0, damage, percent)
        p55 = self._calcPercent(0.0, 0.0, 55.0, damage, percent)
        p65 = self._calcPercent(0.0, 0.0, 65.0, damage, percent)
        p85 = self._calcPercent(0.0, 0.0, 85.0, damage, percent)
        p95 = self._calcPercent(0.0, 0.0, 95.0, damage, percent)
        p100 = self._calcPercent(0.0, 0.0, 100.0, damage, percent)
        data = [0.0, p20, p40, p55, p65, p85, p95, p100]
        idx = None
        for level in [0.0] + config.levels:
            if level >= percent:
                idx = level
                break
        if idx is None:
            idx = 100.0
        check = ([0.0] + config.levels).index(idx)
        limit2 = data[check]
        delta = limit2 - next_damage
        for value in xrange(len(data)):
            if data[value] == next_damage or data[value] == limit2:
                continue
            if value > check:
                data[value] = self._normalizeDigitsCoeff(data[value] + delta)
        if next_percent == 101:
            next_percent = 100
            next_damage = data[7]
        return (next_percent, next_damage, data[1], data[2], data[3], data[4], data[5], data[6], data[7])

    def collect(self, dossier=None):
        vehicle = g_currentVehicle.item
        if dossier is None:
            if not vehicle:
                return None
            dossier = g_currentVehicle.getDossier()
        if dossier is None:
            return None

        total_stats = dossier.getTotalStats()
        random_stats = dossier.getRandomStats()
        battles = int(self._safe(total_stats.getBattlesCount(), 0))
        wins = int(self._safe(total_stats.getWinsCount(), 0))
        winrate = self._safe(total_stats.getWinsEfficiency(), 0.0) * 100.0 if battles else 0.0

        avg_damage = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgDamage()))
        track = self._safe(ProfileUtils.getValueOrUnavailable(random_stats._getAvgValue(random_stats.getBattlesCountVer2, random_stats.getDamageAssistedTrack)))
        radio = self._safe(ProfileUtils.getValueOrUnavailable(random_stats._getAvgValue(random_stats.getBattlesCountVer2, random_stats.getDamageAssistedRadio)))
        stun = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgDamageAssistedStun()))
        current_damage = int(avg_damage + max(track, radio, stun))

        wn8 = self._calculate_wn8(vehicle, random_stats, total_stats)
        mastery = self._get_mastery_info(dossier)
        damage_rating = self._safe(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0, 0.0)
        moving_avg_damage = self._safe(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage'), 0.0)

        result = {
            'vehicleName': vehicle.shortUserName,
            'battles': battles,
            'wins': wins,
            'winRate': winrate,
            'winRateColor': self._color_by_winrate(winrate),
            'wn8': wn8,
            'wn8Color': self._color_by_wn8(wn8) if wn8 else config.data['card']['mutedColor'],
            'masteryValue': mastery['value'],
            'masteryIcon': mastery['icon'],
            'hasMoE': damage_rating > 0.0
        }

        if damage_rating <= 0.0:
            result.update({
                'damageRating': 0.0,
                'currentDamage': current_damage,
                'movingAvgDamage': 0.0
            })
            return result

        next_percent, need_damage, p20, p40, p55, p65, p85, p95, p100 = self.calc_statistics(damage_rating, moving_avg_damage)
        levels = [p55, p65, p85, p95, p100, 10000000]
        result.update({
            'damageRating': damage_rating,
            'currentDamage': current_damage,
            'movingAvgDamage': moving_avg_damage,
            'nextPercent': int(next_percent),
            'needDamage': int(need_damage),
            'p20': self._normalizeDigits(p20),
            'p40': self._normalizeDigits(p40),
            'p55': self._normalizeDigits(p55),
            'p65': self._normalizeDigits(p65),
            'p85': self._normalizeDigits(p85),
            'p95': self._normalizeDigits(p95),
            'p100': self._normalizeDigits(p100),
            'currentDamageColor': self._pick_color(current_damage, levels),
            'movingAvgDamageColor': self._pick_color(moving_avg_damage, levels),
            'needDamageColor': self._pick_color(int(need_damage), levels)
        })
        return result

    def build_tooltip(self, dossier):
        data = self.collect(dossier)
        if data is None or not data.get('hasMoE'):
            return None
        c20 = config.getDefaultColor('very_bad')
        c40 = config.getDefaultColor('bad')
        c55 = config.getDefaultColor('normal')
        c65 = config.getDefaultColor('good')
        c85 = config.getDefaultColor('very_good')
        c95 = config.getDefaultColor('unique')
        c100 = config.getDefaultColor('super_unique')
        ctx = {
            'nextPercent': data['nextPercent'],
            'needDamage': '<font color="%s">%s</font>' % (data['needDamageColor'], self._format_int(data['needDamage'])),
            'currentMovingAvgDamage': '<font color="%s">%s</font>' % (data['movingAvgDamageColor'], self._format_int(data['movingAvgDamage'])),
            'currentDamage': '<font color="%s">%s</font>' % (data['currentDamageColor'], self._format_int(data['currentDamage'])),
            'mastery': self._mastery_label(data['masteryValue']),
            'wn8': data['wn8'] if data['wn8'] else '--',
            'winRate': '%s%%' % self._format_float(data['winRate']) if data['battles'] else '--',
            '_20': data['p20'],
            '_40': data['p40'],
            '_55': data['p55'],
            '_65': data['p65'],
            '_85': data['p85'],
            '_95': data['p95'],
            '_100': data['p100'],
            'c20': c20,
            'c40': c40,
            'c55': c55,
            'c65': c65,
            'c85': c85,
            'c95': c95,
            'c100': c100
        }
        template = config.i18n['UI_tooltipsFull'] if config.data['showTooltipTargets'] else config.i18n['UI_tooltips']
        return template.format(**ctx)

    def _build_chip_html(self, label, value, value_color, icon_path=''):
        muted = config.data['card']['mutedColor']
        title = config.data['card']['titleColor']
        icon_html = ''
        if icon_path:
            icon_html = '<img src="%s" width="18" height="18" vspace="-4" /> ' % icon_path
        return (
            "<font face='$FieldFont' size='10' color='%s'>%s</font><br>"
            "<font face='$FieldFont' size='13' color='%s'><b>%s%s</b></font>" % (
                muted,
                label,
                value_color or title,
                icon_html,
                value
            )
        )

    def build_panel_model(self):
        header_html = "<font face='$FieldFont' size='10' color='%s' letterSpacing='1.2'><b>MARKS ON GUN</b></font>" % config.data['card']['headerColor']
        muted = config.data['card']['mutedColor']
        title = config.data['card']['titleColor']
        accent = config.data['card']['accentColor']
        c65 = config.get_rating_color('mog', 65.0, 'good')
        c85 = config.get_rating_color('mog', 85.0, 'very_good')
        c95 = config.get_rating_color('mog', 95.0, 'unique')

        if not g_currentVehicle.item:
            return {
                'state': 'empty',
                'headerHtml': header_html,
                'vehicleHtml': "<font face='$TitleFont' size='20' color='%s'><b>No vehicle selected</b></font>" % title,
                'percentHtml': "<font face='$TitleFont' size='30' color='%s'><b>--</b></font>" % title,
                'nextHtml': "<font face='$FieldFont' size='12' color='%s'>Choose a tank in the hangar</font>" % muted,
                'statsHtml': "<font face='$FieldFont' size='13' color='%s'>The card updates automatically when you switch vehicle.</font>" % muted,
                'targetsHtml': "<font face='$FieldFont' size='12' color='%s'>MoE, Mastery Badge, WN8 and winrate are shown here.</font>" % muted,
                'masteryHtml': self._build_chip_html('Mastery', '--', title),
                'wn8Html': self._build_chip_html('WN8', '--', title),
                'winrateHtml': self._build_chip_html('Winrate', '--', title),
                'battlesHtml': "<font face='$FieldFont' size='11' color='%s'>No battles loaded</font>" % muted,
                'damageRating': 0.0
            }

        data = self.collect()
        if data is None:
            return {
                'state': 'empty',
                'headerHtml': header_html,
                'vehicleHtml': "<font face='$TitleFont' size='20' color='%s'><b>%s</b></font>" % (title, g_currentVehicle.item.shortUserName),
                'percentHtml': "<font face='$TitleFont' size='30' color='%s'><b>--</b></font>" % title,
                'nextHtml': "<font face='$FieldFont' size='12' color='%s'>Vehicle dossier not available</font>" % muted,
                'statsHtml': "<font face='$FieldFont' size='13' color='%s'>Play at least one battle on this tank to populate the stats.</font>" % muted,
                'targetsHtml': "<font face='$FieldFont' size='12' color='%s'>MoE data will appear here once available.</font>" % muted,
                'masteryHtml': self._build_chip_html('Mastery', '--', title),
                'wn8Html': self._build_chip_html('WN8', '--', title),
                'winrateHtml': self._build_chip_html('Winrate', '--', title),
                'battlesHtml': "<font face='$FieldFont' size='11' color='%s'>No dossier data</font>" % muted,
                'damageRating': 0.0
            }

        if data.get('hasMoE'):
            percent_html = "<font face='$TitleFont' size='31' color='%s'><b>%s%%</b></font>" % (title, self._format_float(data['damageRating']))
            next_html = "<font face='$FieldFont' size='12' color='%s'>Next breakpoint: <font color='%s'><b>%s%%</b></font></font>" % (
                muted, accent, data['nextPercent'])
            stats_html = (
                "<font face='$FieldFont' size='12' color='%s'>Current</font> "
                "<font face='$FieldFont' size='14' color='%s'><b>%s</b></font>"
                "<font face='$FieldFont' size='12' color='%s'>   EMA</font> "
                "<font face='$FieldFont' size='14' color='%s'><b>%s</b></font>"
                "<font face='$FieldFont' size='12' color='%s'>   Need</font> "
                "<font face='$FieldFont' size='14' color='%s'><b>%s</b></font>" % (
                    muted,
                    data['currentDamageColor'], self._format_int(data['currentDamage']),
                    muted,
                    data['movingAvgDamageColor'], self._format_int(data['movingAvgDamage']),
                    muted,
                    data['needDamageColor'], self._format_int(data['needDamage'])
                )
            )
            targets_html = (
                "<font face='$FieldFont' size='11' color='%s'>Marks</font> "
                "<font face='$FieldFont' size='11' color='%s'><b>65%%</b></font>  "
                "<font face='$FieldFont' size='11' color='%s'><b>85%%</b></font>  "
                "<font face='$FieldFont' size='11' color='%s'><b>95%%</b></font>" % (
                    muted,
                    c65,
                    c85,
                    c95
                )
            )
        else:
            percent_html = "<font face='$TitleFont' size='31' color='%s'><b>--</b></font>" % title
            next_html = "<font face='$FieldFont' size='12' color='%s'>No valid MoE data yet for this tank</font>" % muted
            stats_html = "<font face='$FieldFont' size='13' color='%s'>Play more battles on this vehicle to unlock mark progress.</font>" % muted
            targets_html = "<font face='$FieldFont' size='11' color='%s'>Thresholds: 65%% / 85%% / 95%%</font>" % muted

        battles_label = '%s battles' % self._format_int(data['battles']) if data['battles'] else 'No battles'
        return {
            'state': 'data',
            'headerHtml': header_html,
            'vehicleHtml': "<font face='$TitleFont' size='19' color='%s'><b>%s</b></font>" % (title, self._escape_html(data['vehicleName'])),
            'percentHtml': percent_html,
            'nextHtml': next_html,
            'statsHtml': stats_html,
            'targetsHtml': targets_html,
            'masteryHtml': self._build_chip_html('Mastery', self._mastery_label(data['masteryValue']), accent, data['masteryIcon']),
            'wn8Html': self._build_chip_html('WN8', data['wn8'] if data['wn8'] else '--', data['wn8Color']),
            'winrateHtml': self._build_chip_html('Winrate', '%s%%' % self._format_float(data['winRate']) if data['battles'] else '--', data['winRateColor']),
            'battlesHtml': "<font face='$FieldFont' size='11' color='%s'>%s</font>" % (muted, battles_label),
            'damageRating': data['damageRating']
        }


g_data = MarksOnGunData()


class MarksOnGunHangarView(View):
    def _populate(self):
        super(MarksOnGunHangarView, self)._populate()
        if g_controller is not None:
            g_controller.attach(self)

    def _dispose(self):
        if g_controller is not None:
            g_controller.detach(self)
        super(MarksOnGunHangarView, self)._dispose()

    def py_savePosition(self, x, y):
        panel = dict(config.data['panel'])
        panel['x'] = float(x)
        panel['y'] = float(y)
        config.onApplySettings({'panel': panel})

    def py_log(self, text):
        logError(config.ID, '{}', text)

    def as_applyConfigS(self, data):
        if self._isDAAPIInited():
            self.flashObject.as_applyConfig(data)

    def as_updateDataS(self, data):
        if self._isDAAPIInited():
            try:
                self.flashObject.as_updateData(data)
            except Exception:
                # Flash side may still be initializing on first frame; next update will retry.
                logError(config.ID, '{}', 'Skipped early as_updateData call: flash view not ready yet')

    def as_setVisibleS(self, visible):
        if self._isDAAPIInited():
            self.flashObject.as_setVisible(visible)


class MarksOnGunHangarController(object):
    def __init__(self):
        self._view = None
        self._viewRequested = False
        g_entitiesFactories.addSettings(ViewSettings(AS_ALIAS, MarksOnGunHangarView, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
        g_eventBus.addListener(events.AppLifeCycleEvent.INITIALIZED, self._onAppInitialized, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED, self._onComponentRegistered, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_currentVehicle.onChanged += self.update
        self._loadView()

    def destroy(self):
        g_eventBus.removeListener(events.AppLifeCycleEvent.INITIALIZED, self._onAppInitialized, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.removeListener(events.ComponentEvent.COMPONENT_REGISTERED, self._onComponentRegistered, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_currentVehicle.onChanged -= self.update
        self._view = None

    def attach(self, view):
        self._view = view
        self._viewRequested = True
        self.onApplySettings()
        self.update()

    def detach(self, view):
        if self._view is view:
            self._view = None

    def _loadView(self):
        if self._viewRequested:
            return
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_LOBBY)
        if app is not None:
            self._viewRequested = True
            app.loadView(SFViewLoadParams(AS_ALIAS))

    def _onAppInitialized(self, event):
        if event.ns == APP_NAME_SPACE.SF_LOBBY:
            self._loadView()

    def _onComponentRegistered(self, event):
        if event.alias == HANGAR_ALIASES.AMMUNITION_PANEL:
            self.onApplySettings()
            self.update()

    def onApplySettings(self):
        if self._view is None:
            return
        self._view.as_applyConfigS(config.get_view_config())
        self._view.as_setVisibleS(config.data['enabled'] and config.data['showInHangar'])

    def update(self, *args):
        if self._view is None:
            return
        visible = config.data['enabled'] and config.data['showInHangar']
        self._view.as_setVisibleS(visible)
        if visible:
            self._view.as_updateDataS(g_data.build_panel_model())


worker = type('Worker', (object,), {'dossier': None})()


@override(MarkOnGunAchievement, '__init__')
@logException
def new__init(func, *args):
    func(*args)
    if len(args) > 1:
        worker.dossier = args[1]


@override(MarkOnGunAchievement, 'getUserCondition')
@logException
def new__getUserCondition(func, *args):
    if config.data['enabled'] and config.data['showInStatistic'] and worker.dossier is not None:
        tooltip = g_data.build_tooltip(worker.dossier)
        if tooltip:
            return tooltip
    return func(*args)


g_controller = MarksOnGunHangarController()
