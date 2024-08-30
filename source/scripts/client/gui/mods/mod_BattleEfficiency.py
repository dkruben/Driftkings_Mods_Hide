# -*- coding: utf-8 -*-
import math
import re
import traceback
from collections import namedtuple

from Avatar import PlayerAvatar
from constants import ARENA_BONUS_TYPE
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import DamageLogPanel
from gui.Scaleform.daapi.view.battle.shared.ribbons_aggregator import RibbonsAggregator
from gui.Scaleform.daapi.view.battle.shared.ribbons_panel import BattleRibbonsPanel
from gui.Scaleform.daapi.view.battle_results_window import BattleResultsWindow
from gui.Scaleform.genConsts.BATTLE_EFFICIENCY_TYPES import BATTLE_EFFICIENCY_TYPES
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE
from realm import CURRENT_REALM

from DriftkingsCore import SimpleConfigInterface, Analytics, override, logError, getPlayer, get_color, color_tables, replace_macros, calculate_version
from DriftkingsStats import getVehicleInfoData, calculateXvmScale, calculateXTE

DEF_RESULTS_LEN = 16
RANKED_OFFSET = 4
DataIDs = namedtuple('DataIDs', ('damageDealt', 'spotted', 'kills', 'defAndCap_vehWOStun', 'defAndCap_vehWStun'))
data_ids = DataIDs(3, 11, 12, 14, 17)


class ConfigInterface(SimpleConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.6.0 %(file_compile_date)s'
        self.author = 'by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'colorRatting': 0,
            'format': 'WN8: <font color=\'{c:wn8}\'>{wn8}</font> EFF: <font color=\'{c:eff}\'>{eff}</font> DIFF: <font color=\'{c:diff}\'>{diff}</font>',
            'textStyle': {'font': '$TitleFont', 'color': '#FFFFFF', 'size': 16, 'align': 'center'},
            'textLock': False,
            # flash
            'position': {'x': 125, 'y': 36},
            'textShadow': {'enabled': True, 'distance': 0, 'angle': 90, 'color': '#000000', 'alpha': 0.8, 'blurX': 2, 'blurY': 2, 'strength': 2, 'quality': 4},
            # Battle result
            'battleResultsWindow': True,
            'battleResultsFormat': '<textformat leading=\'-2\' tabstops=\'[0, 300]\'>\t<font color=\'#FFFFFF\' size=\'15\'>{mapName} - {battleType}    WN8:<font color=\'{c:wn8}\'>{wn8}</font>|=|EFF:<font color=\'{c:eff}\'>{eff}</font>|=|Xte:<font color=\'{c:xte}\'>{xte}</font></font></textformat>'
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_textLock_text': 'Text Lock',
            'UI_setting_textLock_tooltip': 'Drag Text in battle',
            'UI_setting_format_text': 'Text Format, Available Macros:',
            'UI_setting_format_tooltip': (
                'Available Macros:'
                '\n WN8:\'{wn8}\', Color:\'{c:wn8}\''
                '\nXWN8:\'{xwn8}\', Color:\'{c:x}\''
                '\nEFF:\'{eff}\', Color:\'{c:eff}\''
                '\nXEFF:\'{xeff}}\', Color:\'{c:x}\''
                '\nDIFF:\'{diff}}\', Color:\'{c:dif}\''
                '\nDMG:\'{dmg}}\', Color:\'{c:dmg}\''
                '\nXTE:\'{xte}\',   Color:\'{c:x}\''
            ),
            'UI_setting_battleResultsWindow_text': 'Battle Results Window',
            'UI_setting_battleResultsWindow_tooltip': 'Enable battle Results Window.',
            'UI_setting_battleResultsFormat_text': 'Battle results window modifying',
            'UI_setting_battleResultsFormat_tooltip': (
                'Available Macros:'
                '\nWN8:\'{wn8}\', Color: \'{c:wn8}\''
                '\nXWN8:\'{xwn8}\', Color: \'{c:x}\''
                '\nEFF:\'{eff}\', Color: \'{c:eff}\''
                '\nXEFF:\'{xeff}\', Color: \'{c:x}\''
                '\nDIFF:\'{diff}\', Color: \'{c:dif}\''
                '\nDMG:\'{dmg}\', Color: \'{c:dmg}\''
                '\nXTE:\'{xte}\', Color: \'{c:x}\''
            ),
            'UI_setting_colorRatting_text': 'Choose Color Ratting',
            'UI_setting_colorRatting_tooltip': '',
            'UI_setting_colorRatting_NoobMeter': 'NoobMeter',
            'UI_setting_colorRatting_XVM': 'XVM',
            'UI_setting_colorRatting_WotLabs': 'WotLabs'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        x_color_key = 'UI_setting_colorRatting_'
        x_color_list = ('NoobMeter', 'XVM', 'WotLabs')
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('textLock'),
                self.tb.createOptions('colorRatting', [self.i18n[x_color_key + x] for x in x_color_list]),
                self.tb.createControl('format', self.tb.types.TextInput, 400)
            ],
            'column2': [
                self.tb.createControl('battleResultsWindow'),
                self.tb.createControl('battleResultsFormat', self.tb.types.TextInput, 400)
            ]
        }

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)
        if g_flash is not None:
            g_flash.onApplySettings()


class Flash(object):
    def __init__(self, ID):
        self.ID = ID
        self.setup()
        COMPONENT_EVENT.UPDATED += self.__updatePosition

    def setup(self):
        g_guiFlash.createComponent(self.ID, COMPONENT_TYPE.LABEL, dict(g_config.data['position'], drag=not g_config.data['textLock'], border=not g_config.data['textLock'], limit=True))
        self.createBox()

    def onApplySettings(self):
        g_guiFlash.updateComponent(self.ID, dict(g_config.data['position'], drag=not g_config.data['textLock'], border=not g_config.data['textLock']))

    def createBox(self):
        shadow = g_config.data['textShadow']
        if shadow['enabled']:
            g_guiFlash.updateComponent(self.ID, {'shadow': shadow})

    def destroy(self):
        COMPONENT_EVENT.UPDATED -= self.__updatePosition
        g_guiFlash.deleteComponent(self.ID)

    def __updatePosition(self, alias, data):
        if alias != self.ID:
            return
        g_config.onApplySettings({'textPosition': data})

    def addText(self, text):
        text_style = g_config.data['textStyle']
        text = '<font size=\'%s\' face=\'%s\' color=\'%s\'><p align=\'%s\'>%s</p></font>' % (text_style['size'], text_style['font'], text_style['color'], text_style['align'], text)
        self.createBox()
        g_guiFlash.updateComponent(self.ID, {'text': text})


g_flash = None
g_config = ConfigInterface()
statistic_mod = Analytics(g_config.ID, g_config.version, 'UA-121940539-1')
try:
    from gambiter import g_guiFlash
    from gambiter.flash import COMPONENT_TYPE, COMPONENT_ALIGN, COMPONENT_EVENT
    g_flash = Flash(g_config.ID)
except ImportError:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    logError(g_config.ID, 'Loading mod: Not found \'gambiter.flash\' module, loading stop!')
except StandardError:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    traceback.print_exc()


def set_text(text):
    text_style = g_config.data['textStyle']
    styled_text = '<font size=\'%s\' color=\'%s\' face=\'%s\'><p align=\'%s\'>%s</p></font>' % (text_style['size'], text_style['color'], text_style['font'], text_style['align'], text)
    return styled_text


def get_data_ids(offset):
    if not offset:
        return data_ids
    else:
        return DataIDs(*(value + offset for value in data_ids))


class EfficiencyCalculator(object):
    avgTier = 5

    def __init__(self):
        self.expectedValues = {}
        self.vehCD = None
        self.vInfoOK = False

    def stopBattle(self):
        self.__init__()

    def registerVInfoData(self, veh_cd):
        self.vehCD = veh_cd
        v_info_data = getVehicleInfoData(veh_cd)
        for item in ('wn8expDamage', 'wn8expSpot', 'wn8expFrag', 'wn8expDef', 'wn8expWinRate'):
            self.expectedValues[item] = v_info_data.get(item, None)
        self.vInfoOK = None not in self.expectedValues.values()

    def calc(self, damage, spotted, frags, defence, capture, isWin=False):
        if not self.vInfoOK:
            return 0, 0, 0, 0, 0, 0, 0
        try:
            rDAMAGE, rSPOT, rFRAG, rDEF, rWIN = self.calculate_ratios(damage, spotted, frags, defence, isWin)
            WN8, XWN8 = self.calculate_wN8(rDAMAGE, rSPOT, rFRAG, rDEF, rWIN)
            DIFF = int(damage - self.expectedValues['wn8expDamage'])
            DMG = int(damage)
            EFF, XEFF = self.calculate_efficiency(damage, frags, spotted, capture, defence)
            XTE = self.calculate_XTE(damage, frags)

            return WN8, XWN8, EFF, XEFF, XTE, DMG, DIFF
        except (ZeroDivisionError, ValueError) as err:
            logError(g_config.ID, "Error calculating metrics:", err)
            return 0, 0, 0, 0, 0, 0, 0

    def calculate_ratios(self, damage, spotted, frags, defence, isWin):
        rDAMAGE = float(damage) / float(self.expectedValues['wn8expDamage'])
        rSPOT = float(spotted) / float(self.expectedValues['wn8expSpot'])
        rFRAG = float(frags) / float(self.expectedValues['wn8expFrag'])
        rDEF = float(defence) / float(self.expectedValues['wn8expDef'])
        rWIN = (100.0 if isWin else 0) / float(self.expectedValues['wn8expWinRate'])
        return rDAMAGE, rSPOT, rFRAG, rDEF, rWIN

    @staticmethod
    def calculate_wN8(rDAMAGE, rSPOT, rFRAG, rDEF, rWIN):
        rWINc = max(0.0, (rWIN - 0.71) / (1 - 0.71))
        rDAMAGEc = max(0.0, (rDAMAGE - 0.22) / (1 - 0.22))
        rSPOTc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rSPOT - 0.38) / (1 - 0.38))))
        rFRAGc = max(0.0, min(rDAMAGEc + 0.2, max(0.0, (rFRAG - 0.12) / (1 - 0.12))))
        rDEFc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rDEF - 0.10) / (1 - 0.10))))
        WN8 = int(980 * rDAMAGEc + 210 * rDAMAGEc * rFRAGc + 155 * rFRAGc * rSPOTc + 75 * rDEFc * rFRAGc + 145 * min(1.8, rWINc))
        XWN8 = calculateXvmScale('xwn8', WN8)
        return WN8, XWN8

    def calculate_efficiency(self, damage, frags, spotted, capture, defence):
        EFF = int(max(0, int(damage * (10.0 / (self.avgTier + 2)) * (0.23 + 2 * self.avgTier / 100.0) + frags * 250 + spotted * 150 + math.log(capture + 1, 1.732) * 150 + defence * 150)))
        XEFF = calculateXvmScale('xeff', EFF)
        return EFF, XEFF

    def calculate_XTE(self, damage, frags):
        return calculateXTE(self.vehCD, damage, frags) if self.vehCD is not None else 0


class BattleEfficiency(object):
    def __init__(self):
        self._stats = {
            'frags': 0, 'damage': 0, 'spotted': 0, 'defence': 0, 'capture': 0,
            'wn8': 0, 'xwn8': 0, 'eff': 0, 'xeff': 0, 'xte': 0, 'diff': 0, 'dmg': 0
        }
        self._colors = {key: '#FFFFFF' for key in ['wn8', 'xwn8', 'eff', 'xeff', 'xte', 'diff', 'dmg']}

    def stopBattle(self):
        self.__init__()

    @property
    def stats(self):
        return self._stats

    @property
    def colors(self):
        return self._colors

    def update_stat(self, key, value):
        if key in self._stats:
            self._stats[key] = value

    @staticmethod
    def read_colors(rating_color, rating_value):
        colors = color_tables[g_config.data['colorRatting']].get('colors')
        return get_color(colors, rating_color, rating_value)

    def startBattle(self):
        if not g_config.data['enabled']:
            return
        try:
            result = g_calculator.calc(self._stats['damage'], self._stats['spotted'], self._stats['frags'], self._stats['defence'], self._stats['capture'])
            self._stats.update(dict(zip(['wn8', 'xwn8', 'eff', 'xeff', 'xte', 'dmg', 'diff'], result)))
            self.update_format_string()
        except Exception as err:
            logError(g_config.ID, "Error in startBattle: {}", err)

    def update_format_string(self):
        macro_data = {}
        for key, value in self._stats.iteritems():
            macro_data['{%s}' % key] = str(value)
            if key in self._colors:
                color_key = 'x' + key if key.startswith('x') else key
                color_value = self.read_colors(color_key, value)
                macro_data['{c:%s}' % key] = str(color_value) if color_value is not None else ''
        if not getPlayer().arena:
            return
        if getPlayer().arena.bonusType != ARENA_BONUS_TYPE.REGULAR:
            return
        format_text = replace_macros(g_config.data['format'], macro_data)
        g_flash.addText(set_text(format_text))

g_battleEfficiency = BattleEfficiency()
g_calculator = EfficiencyCalculator()


@override(PlayerAvatar, 'vehicle_onAppearanceReady')
def new_onAppearanceReady(func, self, vehicle):
    func(self, vehicle)
    if not g_config.data['enabled']:
        return
    if vehicle.id == self.playerVehicleID:
        g_calculator.registerVInfoData(vehicle.typeDescriptor.type.compactDescr)
        g_battleEfficiency.startBattle()


@override(RibbonsAggregator, 'suspend')
def new_suspend(func, self):
    if not g_config.data['enabled']:
        func(self)
        return
    self.resume()


def new_addRibbon(func, self, ribbonID, ribbonType='', leftFieldStr='', **kwargs):
    func(self, ribbonID, ribbonType, leftFieldStr, **kwargs)
    if not g_config.data['enabled']:
        return
    if ribbonType not in (BATTLE_EFFICIENCY_TYPES.DETECTION, BATTLE_EFFICIENCY_TYPES.DESTRUCTION, BATTLE_EFFICIENCY_TYPES.DEFENCE, BATTLE_EFFICIENCY_TYPES.CAPTURE):
        return
    if ribbonType == BATTLE_EFFICIENCY_TYPES.DETECTION:
        g_battleEfficiency.stats['spotted'] += 1 if (len(leftFieldStr.strip()) == 0) else int(leftFieldStr[1:])
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.DESTRUCTION:
        g_battleEfficiency.stats['frags'] += 1
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.DEFENCE:
        g_battleEfficiency.stats['defence'] = min(100, g_battleEfficiency.stats['defence'] + int(leftFieldStr))
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.CAPTURE:
        g_battleEfficiency.stats['capture'] = int(leftFieldStr)
    g_battleEfficiency.startBattle()


@override(DamageLogPanel, '_onTotalEfficiencyUpdated')
def new_onTotalEfficiencyUpdated(func, self, diff):
    func(self, diff)
    if not g_config.data['enabled']:
        return
    if PERSONAL_EFFICIENCY_TYPE.DAMAGE in diff:
        g_battleEfficiency.stats['damage'] = diff[PERSONAL_EFFICIENCY_TYPE.DAMAGE]
        g_battleEfficiency.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    if not g_config.data['enabled']:
        return
    g_battleEfficiency.stopBattle()
    g_calculator.stopBattle()


@override(BattleResultsWindow, 'as_setDataS')
def new_setDataS(func, self, data):
    if g_config.data['enabled'] and not g_config.data['battleResultsWindow']:
        return func(self, data)

    def _normalizeString(s):
        return re.sub('<.*?>', '', s.replace('\xc2\xa0', '').replace('.', '').replace(',', ''))

    def _splitArenaStr(s):
        _s = s.replace(u'\xa0\u2014', '-').replace(u'\u2013', '-')
        _s = _s.split('-')
        return _s if (len(_s) == 2) else (s, '')

    try:
        common = data['common']
        if common['bonusType'] in (ARENA_BONUS_TYPE.EVENT_BATTLES, ARENA_BONUS_TYPE.EPIC_RANDOM, ARENA_BONUS_TYPE.EPIC_RANDOM_TRAINING, ARENA_BONUS_TYPE.EPIC_BATTLE):
            return func(self, data)
        offset = 0 if common['bonusType'] != ARENA_BONUS_TYPE.RANKED else RANKED_OFFSET

        teamDict = data['team1']
        statValues = data['personal']['statValues'][0]
        stunStatus = 'vehWStun' if (len(statValues) > (DEF_RESULTS_LEN + offset)) else 'vehWOStun'
        isWin = common['resultShortStr'] == 'win'
        arenaStr = _splitArenaStr(common['arenaStr'])
        mapName = arenaStr[0].strip()
        battleType = arenaStr[1].strip()

        for playerDict in teamDict:
            if playerDict['isSelf']:
                g_calculator.registerVInfoData(playerDict['vehicleCD'])
                break

        dataIDs = get_data_ids(offset)
        damageDealt = _normalizeString(statValues[dataIDs.damageDealt]['value'])
        spotted = _normalizeString(statValues[dataIDs.spotted]['value'])
        kills = _normalizeString(statValues[dataIDs.kills]['value']).split('/')
        kills = kills[1]
        defAndCap_key = 'defAndCap_' + stunStatus
        defAndCap = _normalizeString(statValues[getattr(dataIDs, defAndCap_key)]['value']).split('/')
        capture = defAndCap[0]
        defence = defAndCap[1]

        result = g_calculator.calc(int(damageDealt), int(spotted), int(kills), int(defence), int(capture), isWin)
        wn8, xwn8, eff, xeff, xte, dmg, _ = result
        macro_data = {
            '{mapName}': mapName,
            '{battleType}': battleType,
            '{wn8}': str(wn8),
            '{xwn8}': str(xwn8),
            '{eff}': str(eff),
            '{xeff}': str(xeff),
            '{xte}': str(xte),
            '{dmg}': str(dmg),
            '{c:wn8}': g_battleEfficiency.read_colors('wn8', wn8),
            '{c:xwn8}': g_battleEfficiency.read_colors('x', xwn8),
            '{c:eff}': g_battleEfficiency.read_colors('eff', eff),
            '{c:xeff}': g_battleEfficiency.read_colors('x', xeff),
            '{c:xte}': g_battleEfficiency.read_colors('x', xte),
            '{c:dmg}': g_battleEfficiency.read_colors('tdb', dmg)
        }

        msg = g_config.data['battleResultsFormat']
        msg = replace_macros(msg, macro_data)

        data['common']['arenaStr'] = msg
    except StandardError:
        traceback.print_exc()
        data['common']['arenaStr'] += '  <font color="#FE0E00">Efficiency Error!</font>'

    g_calculator.stopBattle()
    return func(self, data)


if CURRENT_REALM == 'RU':
    override(BattleRibbonsPanel, '_addRibbon', new_addRibbon)
else:
    override(BattleRibbonsPanel, '_BattleRibbonsPanel__addRibbon', new_addRibbon)
