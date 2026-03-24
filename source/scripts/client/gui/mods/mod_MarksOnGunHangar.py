# -*- coding: utf-8 -*-
import math
from collections import OrderedDict

from CurrentVehicle import g_currentVehicle
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, logException, logError, calculate_version

_gui_flash_import_error = None
try:
    from gambiter import g_guiFlash
    from gambiter.flash import COMPONENT_TYPE, COMPONENT_EVENT
except ImportError as error:
    _gui_flash_import_error = error
    g_guiFlash = COMPONENT_TYPE = COMPONENT_EVENT = None


g_controller = None


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        self.ratings = OrderedDict([
            ('very_bad', '#FF6347'),
            ('bad', '#FE7903'),
            ('normal', '#F8F400'),
            ('good', '#60FF00'),
            ('very_good', '#02C9B3'),
            ('unique', '#D042F3')
        ])
        self.levels = [20.0, 40.0, 55.0, 65.0, 85.0, 95.0, 100.0]
        self.battleDamageRating = [
            self.ratings['very_bad'],
            self.ratings['very_bad'],
            self.ratings['bad'],
            self.ratings['normal'],
            self.ratings['good'],
            self.ratings['very_good'],
            self.ratings['unique']
        ]
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (lobby only, GambitER GUIFlash)'
        self.data = {
            'enabled': True,
            'showInHangar': True,
            'showInStatistic': True,
            'textLock': False,
            'showTooltipTargets': True,
            'panel': {
                'x': 215.0,
                'y': -228.0,
                'width': 300.0,
                'height': 132.0,
                'alignX': 'left',
                'alignY': 'bottom'
            },
            'card': {
                'backgroundColor': 0x0E0E0F,
                'backgroundAlpha': 0.64,
                'headerColor': '#B9A27A',
                'titleColor': '#F3EEE3',
                'mutedColor': '#9B978C',
                'lineColor': '#2A2723',
                'accentColor': '#E3C07B'
            },
            'shadow': {
                'distance': 0,
                'angle': 0,
                'color': 0x000000,
                'alpha': 0.9,
                'blurX': 4,
                'blurY': 4,
                'strength': 2,
                'quality': 2
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
            'UI_tooltips': (
                '<font color="#FFFFFF" size="12">{currentMovingAvgDamage} current moving average damage</font>\n'
                '<font color="#FFFFFF" size="12">{currentDamage} current summary damage</font>\n'
                'To <font color="#FFFFFF" size="12">{nextPercent}% </font> need '
                '<font color="#FFFFFF" size="12">{needDamage}</font> moving average damage'
            ),
            'UI_tooltipsFull': (
                '<font color="#FFFFFF" size="12">{currentMovingAvgDamage} current moving average damage</font>\n'
                '<font color="#FFFFFF" size="12">{currentDamage} current summary damage</font>\n'
                'To <font color="#FFFFFF" size="12">{nextPercent}% </font> need '
                '<font color="#FFFFFF" size="12">{needDamage}</font> moving average damage\n'
                'This statistic is available from the last battle on this vehicle\n'
                'To <font color="#FFFFFF" size="12">20% </font> need <font color="#FF6347" size="12">~{_20}</font>\n'
                'To <font color="#FFFFFF" size="12">40% </font> need <font color="#FE7903" size="12">~{_40}</font>\n'
                'To <font color="#FFFFFF" size="12">55% </font> need <font color="#F8F400" size="12">~{_55}</font>\n'
                'To <font color="#FFFFFF" size="12">65% </font> need <font color="#60FF00" size="12">~{_65}</font>\n'
                'To <font color="#FFFFFF" size="12">85% </font> need <font color="#02C9B3" size="12">~{_85}</font>\n'
                'To <font color="#FFFFFF" size="12">95% </font> need <font color="#D042F3" size="12">~{_95}</font>\n'
                'To <font color="#FFFFFF" size="12">100% </font> need <font color="#D042F3" size="12">~{_100}</font>'
            )
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showInHangar'),
                self.tb.createControl('showInStatistic')
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


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


class MarksOnGunData(object):
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
    def _normalize_digits(value):
        return int(math.ceil(value))

    @staticmethod
    def _normalize_digits_coeff(value):
        return int(math.ceil(math.ceil(value / 10.0)) * 10)

    @staticmethod
    def _calc_percent(ema, start, end, damage, percent):
        if not damage or not percent:
            return 0.0
        while start <= end < 100.001 and ema < 30000:
            ema += 0.1
            start = ema / damage * percent
        return ema

    def calc_statistics(self, percent, damage):
        percent = self._safe(percent, 0.0)
        damage = self._safe(damage, 0.0)
        if damage <= 0.0:
            damage = 1.0
        next_percent = math.floor(percent) + 1
        next_damage = self._calc_percent(damage, percent, next_percent, damage, percent)
        p20 = self._calc_percent(0.0, 0.0, 20.0, damage, percent)
        p40 = self._calc_percent(0.0, 0.0, 40.0, damage, percent)
        p55 = self._calc_percent(0.0, 0.0, 55.0, damage, percent)
        p65 = self._calc_percent(0.0, 0.0, 65.0, damage, percent)
        p85 = self._calc_percent(0.0, 0.0, 85.0, damage, percent)
        p95 = self._calc_percent(0.0, 0.0, 95.0, damage, percent)
        p100 = self._calc_percent(0.0, 0.0, 100.0, damage, percent)
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
                data[value] = self._normalize_digits_coeff(data[value] + delta)
        if next_percent == 101:
            next_percent = 100
            next_damage = data[7]
        return (
            next_percent,
            next_damage,
            data[1],
            data[2],
            data[3],
            data[4],
            data[5],
            data[6],
            data[7]
        )

    def collect(self, dossier=None):
        if dossier is None:
            if not g_currentVehicle.item:
                return None
            dossier = g_currentVehicle.getDossier()
        if dossier is None:
            return None
        damage_rating = self._safe(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0, 0.0)
        if damage_rating <= 0.0:
            return None
        random_stats = dossier.getRandomStats()
        avg_damage = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgDamage()))
        track = self._safe(ProfileUtils.getValueOrUnavailable(random_stats._getAvgValue(random_stats.getBattlesCountVer2, random_stats.getDamageAssistedTrack)))
        radio = self._safe(ProfileUtils.getValueOrUnavailable(random_stats._getAvgValue(random_stats.getBattlesCountVer2, random_stats.getDamageAssistedRadio)))
        stun = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgDamageAssistedStun()))
        current_damage = int(avg_damage + max(track, radio, stun))
        moving_avg_damage = self._safe(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage'), 0.0)
        stats = self.calc_statistics(damage_rating, moving_avg_damage)
        next_percent, need_damage, p20, p40, p55, p65, p85, p95, p100 = stats
        levels = [p55, p65, p85, p95, p100, 10000000]
        return {
            'damageRating': damage_rating,
            'currentDamage': current_damage,
            'movingAvgDamage': moving_avg_damage,
            'nextPercent': int(next_percent),
            'needDamage': int(need_damage),
            'p20': self._normalize_digits(p20),
            'p40': self._normalize_digits(p40),
            'p55': self._normalize_digits(p55),
            'p65': self._normalize_digits(p65),
            'p85': self._normalize_digits(p85),
            'p95': self._normalize_digits(p95),
            'p100': self._normalize_digits(p100),
            'currentDamageColor': self._pick_color(current_damage, levels),
            'movingAvgDamageColor': self._pick_color(moving_avg_damage, levels),
            'needDamageColor': self._pick_color(int(need_damage), levels)
        }

    @staticmethod
    def _pick_color(value, levels):
        colors = [
            config.ratings['normal'],
            config.ratings['normal'],
            config.ratings['good'],
            config.ratings['very_good'],
            config.ratings['unique'],
            config.ratings['unique']
        ]
        for level in levels:
            if value <= level:
                return colors[levels.index(level)]
        return colors[-1]

    def build_tooltip(self, dossier):
        data = self.collect(dossier)
        if data is None:
            return None
        ctx = {
            'nextPercent': data['nextPercent'],
            'needDamage': '<font color="%s">%s</font>' % (data['needDamageColor'], data['needDamage']),
            'currentMovingAvgDamage': '<font color="%s">%s</font>' % (data['movingAvgDamageColor'], int(data['movingAvgDamage'])),
            'currentDamage': '<font color="%s">%s</font>' % (data['currentDamageColor'], data['currentDamage']),
            '_20': data['p20'],
            '_40': data['p40'],
            '_55': data['p55'],
            '_65': data['p65'],
            '_85': data['p85'],
            '_95': data['p95'],
            '_100': data['p100']
        }
        template = config.i18n['UI_tooltipsFull'] if config.data['showTooltipTargets'] else config.i18n['UI_tooltips']
        return template.format(**ctx)

    def build_panel_text(self):
        if not g_currentVehicle.item:
            return {
                'header': "<font face='$FieldFont' size='11' color='%s' letterSpacing='0.6'><b>MARKS ON GUN</b></font>" % config.data['card']['headerColor'],
                'hero': "<font face='$TitleFont' size='22' color='%s'><b>No vehicle</b></font>" % config.data['card']['titleColor'],
                'meta': "<font face='$FieldFont' size='13' color='%s'>Select a vehicle to show lobby stats.</font>" % config.data['card']['mutedColor'],
                'targets': "<font face='$FieldFont' size='12' color='%s'>The panel updates automatically in the hangar.</font>" % config.data['card']['mutedColor']
            }
        data = self.collect()
        if data is None:
            return {
                'header': "<font face='$FieldFont' size='11' color='%s' letterSpacing='0.6'><b>MARKS ON GUN</b></font>" % config.data['card']['headerColor'],
                'hero': "<font face='$TitleFont' size='22' color='%s'><b>No MoE data</b></font>" % config.data['card']['titleColor'],
                'meta': "<font face='$FieldFont' size='13' color='%s'>This vehicle has no valid mark statistics yet.</font>" % config.data['card']['mutedColor'],
                'targets': "<font face='$FieldFont' size='12' color='%s'>Play more battles on this tank to populate MoE progress.</font>" % config.data['card']['mutedColor']
            }
        vehicle = g_currentVehicle.item
        current_damage_color = data['currentDamageColor']
        moving_avg_color = data['movingAvgDamageColor']
        need_damage_color = data['needDamageColor']
        return {
            'header': (
                "<font face='$FieldFont' size='11' color='%s' letterSpacing='0.6'><b>MARKS ON GUN</b></font>"
                "<font face='$FieldFont' size='11' color='%s'>  %s</font>" % (
                    config.data['card']['headerColor'],
                    config.data['card']['mutedColor'],
                    vehicle.shortUserName
                )
            ),
            'hero': (
                "<font face='$TitleFont' size='28' color='%s'><b>%.2f%%</b></font>"
                "<font face='$FieldFont' size='13' color='%s'>   next %s%%</font>" % (
                    config.data['card']['titleColor'],
                    data['damageRating'],
                    config.data['card']['accentColor'],
                    data['nextPercent']
                )
            ),
            'meta': (
                "<font face='$FieldFont' size='13' color='%s'>Current</font> "
                "<font face='$FieldFont' size='14' color='%s'><b>%s</b></font>"
                "<font face='$FieldFont' size='13' color='%s'>   EMA</font> "
                "<font face='$FieldFont' size='14' color='%s'><b>%s</b></font>"
                "<font face='$FieldFont' size='13' color='%s'>   Need</font> "
                "<font face='$FieldFont' size='14' color='%s'><b>%s</b></font>" % (
                    config.data['card']['mutedColor'],
                    current_damage_color, data['currentDamage'],
                    config.data['card']['mutedColor'],
                    moving_avg_color, int(data['movingAvgDamage']),
                    config.data['card']['mutedColor'],
                    need_damage_color, data['needDamage']
                )
            ),
            'targets': (
                "<font face='$FieldFont' size='12' color='%s'>65</font> <font color='#60FF00'><b>%s</b></font>"
                "<font face='$FieldFont' size='12' color='%s'>   |   </font>"
                "<font face='$FieldFont' size='12' color='%s'>85</font> <font color='#02C9B3'><b>%s</b></font>"
                "<font face='$FieldFont' size='12' color='%s'>   |   </font>"
                "<font face='$FieldFont' size='12' color='%s'>95</font> <font color='#D042F3'><b>%s</b></font>"
                "<font face='$FieldFont' size='12' color='%s'>   |   </font>"
                "<font face='$FieldFont' size='12' color='%s'>100</font> <font color='#D042F3'><b>%s</b></font>" % (
                    config.data['card']['mutedColor'],
                    data['p65'],
                    config.data['card']['lineColor'],
                    config.data['card']['mutedColor'],
                    data['p85'],
                    config.data['card']['lineColor'],
                    config.data['card']['mutedColor'],
                    data['p95'],
                    config.data['card']['lineColor'],
                    config.data['card']['mutedColor'],
                    data['p100']
                )
            )
        }


g_data = MarksOnGunData()


class MarksOnGunHangarController(object):
    def __init__(self):
        self._alias = config.ID
        self._children = (
            self._alias + '.bg',
            self._alias + '.header',
            self._alias + '.hero',
            self._alias + '.meta',
            self._alias + '.targets'
        )
        self._create()
        g_currentVehicle.onChanged += self.update
        self.update()

    def _create(self):
        panel_cfg = dict(config.data['panel'])
        panel_cfg['drag'] = not config.data['textLock']
        panel_cfg['border'] = not config.data['textLock']
        panel_cfg['limit'] = False
        g_guiFlash.createComponent(self._alias, COMPONENT_TYPE.PANEL, panel_cfg, battle=False, lobby=True)
        g_guiFlash.createComponent(self._alias + '.bg', COMPONENT_TYPE.LABEL, {
            'x': 0,
            'y': 0,
            'width': panel_cfg['width'],
            'height': panel_cfg['height'],
            'multiline': True,
            'wordWrap': True,
            'autoSize': False,
            'text': ' ',
            'background': True,
            'backgroundColor': config.data['card']['backgroundColor'],
            'alpha': config.data['card']['backgroundAlpha'],
            'shadow': config.data['shadow']
        }, battle=False, lobby=True)
        g_guiFlash.createComponent(self._alias + '.header', COMPONENT_TYPE.LABEL, {
            'x': 14,
            'y': 10,
            'width': panel_cfg['width'] - 28,
            'height': 18,
            'multiline': False,
            'autoSize': False,
            'text': ''
        }, battle=False, lobby=True)
        g_guiFlash.createComponent(self._alias + '.hero', COMPONENT_TYPE.LABEL, {
            'x': 14,
            'y': 34,
            'width': panel_cfg['width'] - 28,
            'height': 34,
            'multiline': False,
            'autoSize': False,
            'text': ''
        }, battle=False, lobby=True)
        g_guiFlash.createComponent(self._alias + '.meta', COMPONENT_TYPE.LABEL, {
            'x': 14,
            'y': 76,
            'width': panel_cfg['width'] - 28,
            'height': 22,
            'multiline': False,
            'autoSize': False,
            'text': ''
        }, battle=False, lobby=True)
        g_guiFlash.createComponent(self._alias + '.targets', COMPONENT_TYPE.LABEL, {
            'x': 14,
            'y': 104,
            'width': panel_cfg['width'] - 28,
            'height': 18,
            'multiline': False,
            'autoSize': False,
            'text': ''
        }, battle=False, lobby=True)
        COMPONENT_EVENT.UPDATED += self._updatePosition

    def onApplySettings(self):
        panel_cfg = dict(config.data['panel'])
        panel_cfg['drag'] = not config.data['textLock']
        panel_cfg['border'] = not config.data['textLock']
        g_guiFlash.updateComponent(self._alias, panel_cfg)
        g_guiFlash.updateComponent(self._alias + '.bg', {
            'width': panel_cfg['width'],
            'height': panel_cfg['height'],
            'backgroundColor': config.data['card']['backgroundColor'],
            'alpha': config.data['card']['backgroundAlpha'],
            'shadow': config.data['shadow']
        })
        for child_alias in (self._alias + '.header', self._alias + '.hero', self._alias + '.meta', self._alias + '.targets'):
            g_guiFlash.updateComponent(child_alias, {'width': panel_cfg['width'] - 28})
        self.update()

    def destroy(self):
        COMPONENT_EVENT.UPDATED -= self._updatePosition
        g_currentVehicle.onChanged -= self.update
        for child_alias in reversed(self._children):
            g_guiFlash.deleteComponent(child_alias)
        g_guiFlash.deleteComponent(self._alias)

    def _updatePosition(self, alias, data):
        if alias != self._alias:
            return
        config.onApplySettings({'panel': data})

    def update(self, *args):
        visible = config.data['enabled'] and config.data['showInHangar']
        view_data = g_data.build_panel_text()
        g_guiFlash.updateComponent(self._alias, {'visible': visible})
        g_guiFlash.updateComponent(self._alias + '.bg', {'visible': visible})
        g_guiFlash.updateComponent(self._alias + '.header', {'visible': visible, 'text': view_data['header']})
        g_guiFlash.updateComponent(self._alias + '.hero', {'visible': visible, 'text': view_data['hero']})
        g_guiFlash.updateComponent(self._alias + '.meta', {'visible': visible, 'text': view_data['meta']})
        g_guiFlash.updateComponent(self._alias + '.targets', {'visible': visible, 'text': view_data['targets']})


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

if g_guiFlash is not None and COMPONENT_TYPE is not None and COMPONENT_EVENT is not None:
    g_controller = MarksOnGunHangarController()
elif _gui_flash_import_error is not None:
    logError(config.ID, 'gambiter.GUIFlash not found. {}', _gui_flash_import_error)
