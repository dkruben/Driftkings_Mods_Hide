# -*- coding: utf-8 -*-
import math
import json
import logging
import weakref
import BigWorld

from CurrentVehicle import g_currentVehicle
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_OF_MASTERY_RECORD
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement
from gui.shared.personality import ServicesLocator

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, logException, calculate_version, color_tables, getColor
from DriftkingsCore.utils.achievement_dossiers import getAchievementDossier
from DriftkingsCore import loadJson
from DriftkingsStats import getVehicleInfoData


LOG = logging.getLogger('Driftkings.MarksOnGunHangar')
FEATURE = 'DriftkingsMarksOnGunHangar'
RESOURCE = 'mods/Driftkings/MarksOnGunHangar/model'
ASSETS = 'coui://gui/gameface/mods/Driftkings/MarksOnGunHangar/'

g_controller = None


THRESHOLDS = (65, 85, 95)


def finite(value, default=0.0):
    try:
        value = float(value)
        return default if math.isnan(value) or math.isinf(value) else value
    except (ValueError, TypeError, OverflowError):
        return default


def goal(percent, moving_average, tier, selection=0, earned_marks=0):
    percent = max(0.0, min(100.0, finite(percent)))
    earned_marks = max(0, min(3, int(finite(earned_marks))))
    selection = max(0, min(3, int(finite(selection))))
    # Awarded marks are retained even if the current percentage later falls.
    progress_marks = max(earned_marks, sum(percent >= limit for limit in THRESHOLDS))
    mark = selection or min(3, progress_marks + 1)
    threshold = THRESHOLDS[mark - 1]
    eligible = finite(tier) >= 5
    achieved = eligible and (earned_marks >= mark or percent >= threshold)
    estimate = None
    average = finite(moving_average)
    if eligible and percent > 0 and average > 0:
        # Local proportional approximation, NOT a server threshold or a forecast
        # of the damage needed in the next single battle.
        estimate = int(math.ceil(average * threshold / percent / 10.0) * 10)
    return {'eligible': eligible, 'mark': mark, 'threshold': threshold,
            'achieved': achieved, 'gap': max(0.0, threshold - percent),
            'estimate': estimate, 'percent': percent}


def record_snapshot(history, vehicle_id, battles, percent, average):
    """Store one snapshot per observed battle counter, not per panel repaint."""
    vehicles = history.setdefault('vehicles', {})
    key = str(vehicle_id)
    points = vehicles.setdefault(key, [])
    sample = {'battles': max(0, int(finite(battles))),
              'percent': max(0.0, min(100.0, finite(percent))),
              'average': max(0.0, finite(average))}
    if points and sample['battles'] < points[-1]['battles']:
        # Reset/replaced dossier: do not turn a decreasing counter into a battle.
        points[:] = []
    if points and sample['battles'] == points[-1]['battles']:
        if points[-1] == sample:
            return False
        points[-1] = sample
    else:
        points.append(sample)
    del points[:-21]
    return True


def trend(history, vehicle_id, last_battles=10):
    points = history.get('vehicles', {}).get(str(vehicle_id), [])
    if len(points) < 2:
        return {'battles': 0, 'delta': None, 'points': [p['percent'] for p in points]}
    last_battles = max(1, min(20, int(finite(last_battles, 10))))
    start = len(points) - 2
    while start > 0 and points[-1]['battles'] - points[start]['battles'] < last_battles:
        start -= 1
    selected = points[start:]
    return {'battles': selected[-1]['battles'] - selected[0]['battles'],
            'delta': round(selected[-1]['percent'] - selected[0]['percent'], 2),
            'points': [p['percent'] for p in selected]}


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
        self.ID = 'MarksOnGunHangar'
        self.version = '1.2.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (Gameface hangar UI)'
        self.data = {
            'enabled': True,
            'showInHangar': True,
            'showInStatistic': True,
            'textLock': False,
            'goalSelection': 0,
            'compactMode': False,
            'historyBattles': 10,
            'showTooltipTargets': True,
            'colorRating': 0,
            'starAnimationWindow': 5.0,
            'panel': {
                'x': 215.0,
                'y': -246.0,
                'width': 362.0,
                'height': 186.0,
                'alignX': 'left',
                'alignY': 'bottom'
            },
            'card': {
                'backgroundColor': 0x0C0F14,
                'backgroundAlpha': 0.88,
                'outlineColor': 0x6E7783,
                'headerColor': '#C7A86A',
                'titleColor': '#F5F1E8',
                'mutedColor': '#8C919A',
                'lineColor': '#4B515B',
                'accentColor': '#E2C07A',
                'accentSoftColor': '#4A3319',
                'warningColor': '#F3B14B'
            }
        }
        self.i18n = {
            'UI_panel_header': 'MARKS OF EXCELLENCE',
            'UI_panel_drag': 'DRAG',
            'UI_panel_locked': 'LOCKED',
            'UI_panel_chooseVehicle': 'Choose a tank',
            'UI_panel_selectVehicle': 'Select a vehicle in the hangar.',
            'UI_panel_noDossier': 'Vehicle dossier not available.',
            'UI_panel_tierLimit': 'Marks available from tier V',
            'UI_panel_mark': 'Mark',
            'UI_panel_achieved': 'Achieved',
            'UI_panel_remaining': 'pp remaining',
            'UI_panel_average': 'Combined EMA',
            'UI_panel_estimate': 'Goal estimate',
            'UI_panel_historyWaiting': 'History: waiting for the next battle',
            'UI_panel_observedBattles': 'battles observed',
            'UI_panel_estimateNote': 'Estimate only; not the damage required next battle.',
            'UI_panel_noStats': 'No statistics loaded',
            'UI_panel_battles': 'battles',
            'UI_panel_winRate': 'WIN RATE',
            'UI_panel_mastery0': 'No mastery',
            'UI_panel_mastery1': '3rd class',
            'UI_panel_mastery2': '2nd class',
            'UI_panel_mastery3': '1st class',
            'UI_panel_mastery4': 'Ace Tanker',
            'UI_panel_automatic': 'Automatic',
            'UI_panel_goal1': '1st mark (65%)',
            'UI_panel_goal2': '2nd mark (85%)',
            'UI_panel_goal3': '3rd mark (95%)',
            'UI_description': self.ID,
            'UI_setting_goalSelection_text': 'Mark objective',
            'UI_setting_goalSelection_tooltip': 'Automatic selects the next unearned mark. Damage is a proportional estimate, not a server threshold or next-battle prediction.',
            'UI_setting_compactMode_text': 'Compact panel',
            'UI_setting_compactMode_tooltip': 'Hide secondary vehicle statistics.',
            'UI_setting_historyBattles_text': 'Recent battles in history',
            'UI_setting_historyBattles_tooltip': 'Updates may group several battles. History starts when this version is installed.',
            'UI_setting_positionX_text': 'Horizontal position (X)',
            'UI_setting_positionX_tooltip': 'Smaller: left. Larger: right.',
            'UI_setting_positionY_text': 'Vertical position (Y)',
            'UI_setting_positionY_tooltip': 'Smaller: up. Larger: down.',
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
                self.tb.createOptions('goalSelection', [self.i18n['UI_panel_' + key] for key in ('automatic', 'goal1', 'goal2', 'goal3')]),
                self.tb.createControl('compactMode'),
                self.tb.createOptions('colorRating', [self.i18n[x_color_key + x] for x in x_color_list])
            ],
            'column2': [
                self.tb.createControl('showTooltipTargets'),
                self.tb.createControl('textLock'),
                self.tb.createStepper('historyBattles', 1, 20, 1, manual=True),
                self.tb.createStepper('positionX', -7680, 7680, 1, manual=True, value=self.data['panel']['x']),
                self.tb.createStepper('positionY', -4320, 4320, 1, manual=True, value=self.data['panel']['y'])
            ]
        }

    def getData(self):
        # MSA resolves every template varName from this flat settings mapping.
        # Keep the persisted position in panel.x/y, shared with Gameface dragging.
        settings = dict(self.data)
        settings['positionX'] = self.data['panel']['x']
        settings['positionY'] = self.data['panel']['y']
        return settings

    def onApplySettings(self, settings):
        settings = dict(settings)
        panel = dict(settings.get('panel', self.data['panel']))
        for setting, axis in (('positionX', 'x'), ('positionY', 'y')):
            if setting in settings:
                panel[axis] = float(settings.pop(setting))
        settings['panel'] = panel
        super(ConfigInterface, self).onApplySettings(settings)
        if g_controller is not None:
            g_controller.onApplySettings()

    def get_view_config(self):
        panel = dict(self.data['panel'])
        panel['compactMode'] = bool(self.data['compactMode'])
        panel['height'] = 194.0 if panel['compactMode'] else max(260.0, panel['height'])
        panel['locked'] = bool(self.data['textLock'])
        panel['visible'] = bool(self.data['enabled'] and self.data['showInHangar'])
        panel['starAnimationWindow'] = float(self.data.get('starAnimationWindow', 5.0))
        panel['headerColor'] = self.data['card']['headerColor']
        panel['titleColor'] = self.data['card']['titleColor']
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

    def get_rating_color(self, rating_color, rating_value, fallback_key):
        return self.getRatingColor(rating_color, rating_value, fallback_key)


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

    def _mastery_compact_label(self, value):
        labels = {
            1: '3rd',
            2: '2nd',
            3: '1st',
            4: 'Ace'
        }
        return labels.get(int(value or 0), '--')

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
        else:
            vehicle = ServicesLocator.itemsCache.items.getItemByCD(dossier.getCompactDescriptor())
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
            'vehicleID': vehicle.intCD,
            'tier': vehicle.level,
            'earnedMarks': dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'marksOnGun'),
            'randomBattles': int(self._safe(random_stats.getBattlesCount(), 0)),
            'battles': battles,
            'wins': wins,
            'winRate': winrate,
            'winRateColor': self._color_by_winrate(winrate),
            'wn8': wn8,
            'wn8Color': self._color_by_wn8(wn8) if wn8 else config.data['card']['mutedColor'],
            'masteryValue': mastery['value'],
            'masteryIcon': mastery['icon'],
            'hasMoE': vehicle.level >= 5 and damage_rating > 0.0
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

    def build_panel_model(self):
        result = {'config': config.get_view_config(), 'state': 'empty',
                  'vehicle': config.i18n['UI_panel_chooseVehicle'], 'message': config.i18n['UI_panel_selectVehicle'],
                  'labels': {key[9:]: value for key, value in config.i18n.items() if key.startswith('UI_panel_')}}
        if not g_currentVehicle.isPresent():
            return result
        data = self.collect()
        if data is None:
            result.update(vehicle=unicode(g_currentVehicle.item.shortUserName),
                          message=config.i18n['UI_panel_noDossier'])
            return result
        target = goal(data['damageRating'], data['movingAvgDamage'], data['tier'],
                      config.data['goalSelection'], data['earnedMarks'])
        recent = g_history.observe(data) if target['eligible'] else {'delta': None, 'battles': 0}
        mastery = max(0, min(4, int(finite(data['masteryValue']))))
        icon = ('gui/maps/icons/achievement/32x32/markOfMastery%s.png' % mastery
                if mastery else 'gui/maps/icons/achievements/summary/mastery/mastery_empty_small.png')
        result.update({
            'state': 'data', 'vehicle': unicode(data['vehicleName']), 'tier': data['tier'],
            'target': target, 'recent': recent,
            'earnedMarks': max(0, min(3, int(finite(data['earnedMarks'])))),
            'average': self._format_int(data['movingAvgDamage']),
            'estimate': '~' + self._format_int(target['estimate']) if target['estimate'] is not None else '--',
            'mastery': config.i18n['UI_panel_mastery%s' % mastery],
            'masteryIcon': 'coui://' + icon,
            'wn8': self._format_int(data['wn8']) if data['wn8'] else '--',
            'wn8Color': data['wn8Color'], 'winRateColor': data['winRateColor'],
            'winRate': ('%.2f%%' % data['winRate']) if data['battles'] else '--',
            'battles': self._format_int(data['battles'])
        })
        return result


class ProgressHistory(object):
    def __init__(self):
        self.account = None
        self.data = {'vehicles': {}}

    def observe(self, data):
        account = getattr(BigWorld.player(), 'databaseID', None)
        if not account:
            return {'delta': None, 'battles': 0}
        name = 'progress_%s' % int(account)
        if account != self.account:
            self.account = account
            loaded = loadJson(config.ID, name, {'vehicles': {}}, config.configPath)
            self.data = {'vehicles': {}}
            if isinstance(loaded, dict) and isinstance(loaded.get('vehicles'), dict):
                for vehicle, points in loaded['vehicles'].items():
                    if isinstance(points, list):
                        for point in points[-21:]:
                            if isinstance(point, dict) and all(k in point for k in ('battles', 'percent', 'average')):
                                record_snapshot(self.data, vehicle, point['battles'], point['percent'], point['average'])
        if record_snapshot(self.data, data['vehicleID'], data['randomBattles'], data['damageRating'], data['movingAvgDamage']):
            loadJson(config.ID, name, self.data, config.configPath, True, quiet=True)
        return trend(self.data, data['vehicleID'], config.data['historyBattles'])


g_history = ProgressHistory()

g_data = MarksOnGunData()


class MarksOnGunHangarController(object):
    def __init__(self):
        self.views = weakref.WeakKeyDictionary()
        self.visible = weakref.WeakKeyDictionary()

    def onApplySettings(self):
        for child in list(self.views.values()):
            child.refresh()

    def setVisible(self, parent, visible):
        self.visible[parent] = visible
        child = self.views.get(parent)
        if child is not None:
            child.refresh()


def install_gameface():
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent
    from gui.impl.gen_utils import INVALID_RES_ID
    from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
    from openwg_gameface import gf_mod_inject, res_id_by_key

    class MarksModel(ViewModel):
        def __init__(self):
            super(MarksModel, self).__init__(properties=2, commands=1)

        def _initialize(self):
            super(MarksModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            self.onSavePosition = self._addCommand('onSavePosition')
            gf_mod_inject(self, FEATURE, styles=[ASSETS + 'marks.css'], scripts=[ASSETS + 'marks.js'])

    class MarksView(ViewComponent):
        def __init__(self, parent, resource_id):
            self._hangarRef = weakref.ref(parent)
            self._marksActive = False
            super(MarksView, self).__init__(layoutID=resource_id, model=MarksModel)
            g_controller.views[parent] = self

        def _getEvents(self):
            return ((g_currentVehicle.onChanged, self.refresh),
                    (ServicesLocator.itemsCache.onSyncCompleted, self.refresh),
                    (self.getViewModel().onSavePosition, self.savePosition))

        def _onLoading(self, *args, **kwargs):
            super(MarksView, self)._onLoading(*args, **kwargs)
            self._marksActive = True
            self.refresh()

        def _finalize(self):
            self._marksActive = False
            parent = self._hangarRef()
            if parent is not None and g_controller.views.get(parent) is self:
                g_controller.views.pop(parent, None)
            super(MarksView, self)._finalize()

        def refresh(self, *args):
            if not self._marksActive:
                return
            try:
                parent = self._hangarRef()
                visible = bool(parent is not None and g_controller.visible.get(parent, False)
                               and config.data['enabled'] and config.data['showInHangar'])
                payload = g_data.build_panel_model() if visible else {'config': config.get_view_config()}
                payload['config']['visible'] = visible
                with self.getViewModel().transaction() as model:
                    model._setString(0, json.dumps(payload, separators=(',', ':'), allow_nan=False))
            except Exception:
                LOG.exception('Could not update Gameface hangar card')
                with self.getViewModel().transaction() as model:
                    model._setString(0, '{"config":{"visible":false}}')

        def savePosition(self, args):
            if config.data['textLock'] or not isinstance(args, dict):
                return
            panel = dict(config.data['panel'])
            panel['x'] = max(-7680, min(7680, finite(args.get('x'), panel['x'])))
            panel['y'] = max(-4320, min(4320, finite(args.get('y'), panel['y'])))
            config.onApplySettings({'panel': panel})

    @override(RandomHangar, '_getChildComponents')
    def get_children(original, parent, *args, **kwargs):
        children = dict(original(parent, *args, **kwargs))
        try:
            resource_id = res_id_by_key(RESOURCE)
            if resource_id == INVALID_RES_ID:
                LOG.warning('Missing Gameface resource: %s. Check OpenWG 1.1.6 and the resource map.', RESOURCE)
            else:
                children[resource_id] = lambda: MarksView(parent, resource_id)
        except Exception:
            LOG.exception('Could not attach Gameface hangar card')
        return children

    @override(RandomHangar, '_onShown')
    def on_shown(original, parent, *args, **kwargs):
        result = original(parent, *args, **kwargs)
        g_controller.setVisible(parent, True)
        return result

    @override(RandomHangar, '_onHidden')
    def on_hidden(original, parent, *args, **kwargs):
        g_controller.setVisible(parent, False)
        return original(parent, *args, **kwargs)


@override(MarkOnGunAchievement, 'getUserCondition')
@logException
def new__getUserCondition(func, *args):
    dossier = getAchievementDossier(args[0])
    if config.data['enabled'] and config.data['showInStatistic'] and dossier is not None:
        tooltip = g_data.build_tooltip(dossier)
        if tooltip:
            return tooltip
    return func(*args)


g_controller = MarksOnGunHangarController()
try:
    install_gameface()
except Exception:
    LOG.exception('Gameface hangar integration unavailable')
