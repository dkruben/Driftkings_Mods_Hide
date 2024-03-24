# -*- coding: utf-8 -*-
import math
import re
import traceback

from Avatar import PlayerAvatar
from constants import ARENA_BONUS_TYPE, ARENA_GUI_TYPE
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import DamageLogPanel
from gui.Scaleform.daapi.view.battle.shared.ribbons_aggregator import RibbonsAggregator
from gui.Scaleform.daapi.view.battle.shared.ribbons_panel import BattleRibbonsPanel
from gui.Scaleform.daapi.view.battle_results_window import BattleResultsWindow
from gui.Scaleform.genConsts.BATTLE_EFFICIENCY_TYPES import BATTLE_EFFICIENCY_TYPES
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE
from realm import CURRENT_REALM

from DriftkingsCore import SimpleConfigInterface, Analytics, override, logError, getPlayer, isDisabledByBattleType, getColor, COLOR_TABLES
from StatsCore import getVehicleInfoData, calculateXvmScale, calculateXTE

TEXT_LIST = ['format']
# BATTLE_RESULTS
DEF_RESULTS_LEN = 16
RANKED_OFFSET = 4
DATA_IDS = {'damageDealt': 3, 'spotted': 11, 'kills': 12, 'defAndCap_vehWOStun': 14, 'defAndCap_vehWStun': 17}


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        self.color = {}
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '2.4.5 %(file_compile_date)s'
        self.author = 'by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'colorRatting': 0,
            'format': 'WN8: <font color=\'{c_wn8}\'>{wn8}</font> EFF: <font color=\'{c_eff}\'>{eff}</font> DIFF: <font color=\'{c_diff}\'>{diff}</font>',
            'textStyle': {'font': '$TitleFont', 'color': '#FFFFFF', 'size': 16, 'align': 'center'},
            'textLock': False,
            # flash
            'position': {'x': 125, 'y': 36},
            'textShadow': {'enabled': True, 'distance': 0, 'angle': 90, 'color': '#000000', 'alpha': 0.8, 'blurX': 2, 'blurY': 2, 'strength': 2, 'quality': 4},
            # Battle result
            'battleResultsWindow': True,
            'battleResultsFormat': '<textformat leading=\'-2\' tabstops=\'[5, 250]\'>\t<font color=\'#FFFFFF\' size=\'15\'>{mapName} - {battleType}\tWN8: <font color=\'{c:wn8}\'>{wn8} ({xwn8})</font>  EFF: <font color=\'{c:eff}\'>{eff} ({xeff})</font></font></textformat>',
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_textLock_text': 'Text Lock',
            'UI_setting_textLock_tooltip': 'Drag Text in battle',
            'UI_setting_format_text': 'Text Format, Available Macros:',
            'UI_setting_format_tooltip': (
                ' • <b><font color=\'#FFFFFF\'>WN8:</font></b>  \'{wn8}\'   Color:\'{c:wn8}\''
                '\n • <b><font color=\'#FFFFFF\'>XWN8:</font></b> \'{xwn8}\'  Color:\'{c:xwn8}\''
                '\n • <b><font color=\'#FFFFFF\'>EFF:</font></b>  \'{eff}\'   Color:\'{c:eff}\''
                '\n • <b><font color=\'#FFFFFF\'>XEFF:</font></b> \'{xeff}}\' Color:\'{c:xeff}\''
                '\n • <b><font color=\'#FFFFFF\'>DIFF:</font></b> \'{diff}}\' Color:\'{c:dif}\''
                '\n • <b><font color=\'#FFFFFF\'>DIFF:</font></b> \'{dmg}}\' Color:\'{c:dmg}\''
                '\n • <b><font color=\'#FFFFFF\'>XTE:</font><b>   \'{xte}\'   Color:\'{c:xte}\''
            ),
            'UI_setting_battleResultsWindow_text': 'Battle Results Window',
            'UI_setting_battleResultsWindow_tooltip': 'Enable battle Results Window.',
            'UI_setting_battleResultsFormat_text': 'Battle results window modifying',
            'UI_setting_battleResultsFormat_tooltip': (
                '<b><font color=\'#FFD47F\'>Macros:</b>'
                '\n  • <b><font color=\'#FFFFFF\'>WN8:</font></b>  \'{wn8}\'  Color: \'{c:wn8}\''
                '\n  • <b><font color=\'#FFFFFF\'>XWN8:</font></b>  \'{xwn8}\'  Color: \'{c:xwn8}\''
                '\n  • <b><font color=\'#FFFFFF\'>EFF:</font></b>  \'{eff}\'  Color: \'{c:eff}\''
                '\n  • <b><font color=\'#FFFFFF\'>XEFF:</font></b>  \'{xeff}\'  Color: \'{c:xeff}\''
                '\n  • <b><font color=\'#FFFFFF\'>DIFF:</font></b>  \'{diff}\'  Color: \'{c:dif}\''
                '\n  • <b><font color=\'#FFFFFF\'>DMG:</font></b>  \'{dmg}\'  Color: \'{c:dmg}\''
                '\n  • <b><font color=\'#FFFFFF\'>XTE:</font><b>  \'{xte}\'  Color: \'{c:xte}\''
            ),
            'UI_setting_colorRatting_text': 'Choose Color Ratting',
            'UI_setting_colorRatting_tooltip': '',
            'UI_setting_colorRatting_NoobMeter': 'NoobMeter',
            'UI_setting_colorRatting_XVM': 'XVM',
            'UI_setting_colorRatting_WotLabs': 'WotLabs'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        xColorKey = 'UI_setting_colorRatting_'
        xColorList = ('NoobMeter', 'XVM', 'WotLabs')
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('textLock'),
                self.tb.createOptions('colorRatting', [self.i18n[xColorKey + x] for x in xColorList]),
                self.tb.createControl('format', 'TextInput', 400)
            ],
            'column2': [
                self.tb.createControl('battleResultsWindow'),
                self.tb.createControl('battleResultsFormat', 'TextInput', 400),
            ]
        }

    def isEnabled(self):
        return self.data['enabled'] and not isDisabledByBattleType(include=(ARENA_GUI_TYPE.EPIC_RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING, ARENA_GUI_TYPE.EPIC_TRAINING))


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
        textStyle = g_config.data['textStyle']
        text = '<font size=\'%s\' face=\'%s\' color=\'%s\'><p align=\'%s\'>%s</p></font>' % (textStyle['size'], textStyle['font'], textStyle['color'], textStyle['align'], text)
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
    logError('[%s] Loading mod: Not found \'gambiter.flash\' module, loading stop!' % g_config.ID)
except StandardError:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    traceback.print_exc()


def set_text(text):
    textStyle = g_config.data['textStyle']
    return '<font size=\'%s\' color=\'%s\' face=\'%s\'><p align=\'%s\'>%s</p></font>' % (textStyle['size'], textStyle['color'], textStyle['font'], textStyle['align'], text)


def getDataIDs(offset):
    if not offset:
        return DATA_IDS
    else:
        return {key: value + offset for key, value in DATA_IDS.iteritems()}


class EfficiencyCalculator(object):
    avgTier = 5

    def __init__(self):
        self.expectedValues = {}
        self.damage = 0
        self.vehCD = None
        self.vInfoOK = False

    def stopBattle(self):
        self.__init__()

    def registerVInfoData(self, vehCD):
        self.vehCD = vehCD
        vInfoData = getVehicleInfoData(vehCD)

        for item in ('wn8expDamage', 'wn8expSpot', 'wn8expFrag', 'wn8expDef', 'wn8expWinRate'):
            self.expectedValues[item] = vInfoData.get(item, None)

        self.vInfoOK = None not in self.expectedValues.values()

    def calc(self, damage, spotted, frags, defence, capture, isWin=False):
        if self.vInfoOK:
            rDAMAGE = float(damage) / float(self.expectedValues['wn8expDamage'])
            rSPOT = float(spotted) / float(self.expectedValues['wn8expSpot'])
            rFRAG = float(frags) / float(self.expectedValues['wn8expFrag'])
            rDEF = float(defence) / float(self.expectedValues['wn8expDef'])
            rWIN = (100.0 if isWin else 0) / float(self.expectedValues['wn8expWinRate'])

            rWINc = max(0.0, (rWIN - 0.71) / (1 - 0.71))
            rDAMAGEc = max(0.0, (rDAMAGE - 0.22) / (1 - 0.22))
            rSPOTc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rSPOT - 0.38) / (1 - 0.38))))
            rFRAGc = max(0.0, min(rDAMAGEc + 0.2, max(0.0, (rFRAG - 0.12) / (1 - 0.12))))
            rDEFc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rDEF - 0.10) / (1 - 0.10))))

            WN8 = int(980 * rDAMAGEc + 210 * rDAMAGEc * rFRAGc + 155 * rFRAGc * rSPOTc + 75 * rDEFc * rFRAGc + 145 * min(1.8, rWINc))
            XWN8 = calculateXvmScale('xwn8', WN8)
            DIFF = int(damage - self.expectedValues['wn8expDamage'])
            DMG = int(damage - self.damage)
        else:
            WN8 = 0
            XWN8 = 0
            DIFF = 0
            DMG = 0

        EFF = int(max(0, int(damage * (10.0 / (self.avgTier + 2)) * (0.23 + 2 * self.avgTier / 100.0) + frags * 250 + spotted * 150 + math.log(capture + 1, 1.732) * 150 + defence * 150)))
        XEFF = calculateXvmScale('xeff', EFF)

        if self.vehCD is not None:
            XTE = calculateXTE(self.vehCD, damage, frags)
        else:
            XTE = 0

        return WN8, XWN8, EFF, XEFF, XTE, DMG, DIFF


class BattleEfficiency(object):

    def __init__(self):
        self.frags = 0
        self.damage = 0
        self.spotted = 0
        self.defence = 0
        self.capture = 0
        self.wn8 = 0
        self.c_wn8 = '#FFFFFF'
        self.xwn8 = 0
        self.c_xwn8 = '#FFFFFF'
        self.eff = 0
        self.c_eff = '#FFFFFF'
        self.xeff = 0
        self.c_xeff = '#FFFFFF'
        self.xte = 0
        self.c_xte = '#FFFFFF'
        self.diff = 0
        self.c_diff = '#FFFFFF'
        self.dmg = 0
        self.c_dmg = '#FFFFFF'
        self.format_string = {}
        self.format_recreate()

    def stopBattle(self):
        self.__init__()

    @staticmethod
    def readColors(*args, **kwargs):
        return getColor(COLOR_TABLES[g_config.data['colorRatting']].get('colors'), *args, **kwargs)

    @staticmethod
    def check_macros(macros):
        for i in TEXT_LIST:
            if macros in g_config.data[i]:
                return True

    def format_recreate(self):
        self.format_string = {
            'wn8': self.wn8,
            'c_wn8': '',
            'xwn8': self.xwn8,
            'c_xwn8': '',
            'eff': self.eff,
            'c_eff': '',
            'xeff': self.xeff,
            'c_xeff': '',
            'xte': self.xte,
            'c_xte': '',
            'diff': self.diff,
            'c_diff': '',
            'dmg': self.dmg,
            'c_dmg': ''
        }

    def textGenerator(self):
        return g_config.data['format'].format(**self.format_string)

    def startBattle(self):
        if not g_config.isEnabled:
            return
        result = g_calculator.calc(self.damage, self.spotted, self.frags, self.defence, self.capture)
        self.wn8, self.xwn8, self.eff, self.xeff, self.xte, self.dmg, self.diff = result
        #
        self.format_recreate()
        # wn8 / c_wn8
        if self.check_macros('{wm8}'):
            self.format_string['wn8'] = self.wn8
        if self.check_macros('{c_wn8}'):
            self.format_string['c_wn8'] += self.readColors('wn8', self.wn8)
        # xwn8 / c_xwn8
        if self.check_macros('{xwn8}'):
            self.format_string['xwn8'] = self.xwn8
        if self.check_macros('{c_xwn8}'):
            self.format_string['c_wn8'] += self.readColors('x', self.xwn8)
        # eff / c_eff
        if self.check_macros('{eff}'):
            self.format_string['eff'] = self.eff
        if self.check_macros('{c_eff}'):
            self.format_string['c_eff'] += self.readColors('eff', self.eff)
        # xeff / c_xeff
        if self.check_macros('{xeff}'):
            self.format_string['xeff'] = self.xeff
        if self.check_macros('{c_xeff}'):
            self.format_string['c_xeff'] += self.readColors('x', self.xeff)
        # xte / c_xte
        if self.check_macros('{xte}'):
            self.format_string['xte'] = ''
        if self.check_macros('{c_xte}'):
            self.format_string['c_xte'] += self.readColors('x', self.xte)
        # diff / c_diff
        if self.check_macros('{diff}'):
            self.format_string['diff'] = self.diff
        if self.check_macros('{c_diff}'):
            self.format_string['c_diff'] += self.readColors('diff', self.diff)
        # dmg / c_dmg
        if self.check_macros('{dmg}'):
            self.format_string['dmg'] = self.dmg
        if self.check_macros('{c_dmg}'):
            self.format_string['c_dmg'] += self.readColors('tdb', self.dmg)

        if not getPlayer().arena:
            return

        if getPlayer().arena.bonusType != ARENA_BONUS_TYPE.REGULAR:
            return

        g_flash.addText(set_text(self.textGenerator()))


g_battleEfficiency = BattleEfficiency()
g_calculator = EfficiencyCalculator()


@override(PlayerAvatar, 'vehicle_onAppearanceReady')
def new_onAppearanceReady(func, self, vehicle):
    func(self, vehicle)
    if g_config.isEnabled:
        if vehicle.id == self.playerVehicleID:
            g_calculator.registerVInfoData(vehicle.typeDescriptor.type.compactDescr)
            g_battleEfficiency.startBattle()


@override(RibbonsAggregator, 'suspend')
def new_suspend(func, self):
    if not g_config.data['enabled']:
        func(self)
        return


def new_addRibbon(func, self, ribbonID, ribbonType='', leftFieldStr='', **kwargs):
    func(self, ribbonID, ribbonType, leftFieldStr, **kwargs)
    if not g_config.isEnabled:
        return

    if ribbonType not in (BATTLE_EFFICIENCY_TYPES.DETECTION, BATTLE_EFFICIENCY_TYPES.DESTRUCTION, BATTLE_EFFICIENCY_TYPES.DEFENCE, BATTLE_EFFICIENCY_TYPES.CAPTURE):
        return

    if ribbonType == BATTLE_EFFICIENCY_TYPES.DETECTION:
        g_battleEfficiency.spotted += 1 if (len(leftFieldStr.strip()) == 0) else int(leftFieldStr[1:])
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.DESTRUCTION:
        g_battleEfficiency.frags += 1
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.DEFENCE:
        g_battleEfficiency.defence = min(100, g_battleEfficiency.defence + int(leftFieldStr))
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.CAPTURE:
        g_battleEfficiency.capture = int(leftFieldStr)

    g_battleEfficiency.startBattle()


@override(DamageLogPanel, '_onTotalEfficiencyUpdated')
def new_onTotalEfficiencyUpdated(func, self, diff):
    func(self, diff)
    if g_config.isEnabled:

        if PERSONAL_EFFICIENCY_TYPE.DAMAGE in diff:
            g_battleEfficiency.damage = diff[PERSONAL_EFFICIENCY_TYPE.DAMAGE]
            g_battleEfficiency.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    if g_config.isEnabled:
        g_battleEfficiency.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    g_battleEfficiency.stopBattle()
    g_calculator.stopBattle()


@override(BattleResultsWindow, 'as_setDataS')
def new_setDataS(func, self, data):
    if g_config.isEnabled and not g_config.data['battleResultsWindow']:
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

        dataIDs = getDataIDs(offset)
        damageDealt = _normalizeString(statValues[dataIDs['damageDealt']]['value'])
        spotted = _normalizeString(statValues[dataIDs['spotted']]['value'])
        kills = _normalizeString(statValues[dataIDs['kills']]['value']).split('/')
        kills = kills[1]
        defAndCap = _normalizeString(statValues[dataIDs['defAndCap_' + stunStatus]]['value']).split('/')
        capture = defAndCap[0]
        defence = defAndCap[1]

        result = g_calculator.calc(int(damageDealt), int(spotted), int(kills), int(defence), int(capture), isWin)
        wn8, xwn8, eff, xeff, xte, dmg, _ = result

        msg = g_config.data['battleResultsFormat']
        msg = msg.replace('{mapName}', mapName)
        msg = msg.replace('{battleType}', battleType)
        msg = msg.replace('{wn8}', str(wn8))
        msg = msg.replace('{xwn8}', str(xwn8))
        msg = msg.replace('{eff}', str(eff))
        msg = msg.replace('{xeff}', str(xeff))
        msg = msg.replace('{xte}', str(xte))
        msg = msg.replace('{dmg}', str(dmg))
        msg = msg.replace('{c:wn8}', g_battleEfficiency.readColors('wn8', wn8))
        msg = msg.replace('{c:xwn8}', g_battleEfficiency.readColors('x', xwn8))
        msg = msg.replace('{c:eff}', g_battleEfficiency.readColors('eff', eff))
        msg = msg.replace('{c:xeff}', g_battleEfficiency.readColors('x', xeff))
        msg = msg.replace('{c:xte}', g_battleEfficiency.readColors('x', xte))
        msg = msg.replace('{c:dmg}', g_battleEfficiency.readColors('tdb', dmg))

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
