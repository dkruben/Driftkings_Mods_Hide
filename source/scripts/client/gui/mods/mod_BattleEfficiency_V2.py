# -*- coding: utf-8 -*-
import math
import re
import traceback

from Avatar import PlayerAvatar
from constants import ARENA_BONUS_TYPE, ARENA_GUI_TYPE
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import DamageLogPanel
from gui.Scaleform.daapi.view.battle.shared.ribbons_aggregator import RibbonsAggregator
from gui.Scaleform.daapi.view.battle.shared.ribbons_panel import BattleRibbonsPanel
from gui.Scaleform.daapi.view.battle_results_window import BattleResultsWindow
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.DisposableEntity import EntityState
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.BATTLE_EFFICIENCY_TYPES import BATTLE_EFFICIENCY_TYPES
from gui.app_loader.settings import APP_NAME_SPACE
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE
from gui.shared.personality import ServicesLocator
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import SimpleConfigInterface, Analytics, override, logDebug, getPlayer, isDisabledByBattleType, getColor, loadJson, COLOR_TABLES, g_events
from StatsCore import getVehicleInfoData, calculateXvmScale, calculateXTE

AS_INJECTOR = 'BattleEfficiencyInjector'
AS_BATTLE = 'BattleEfficiencyView'
AS_SWF = 'BattleEfficiency.swf'

DATA_IDS = {'damageDealt': 3, 'spotted': 11, 'kills': 12, 'defAndCap_vehWOStun': 14, 'defAndCap_vehWStun': 17}


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        g_events.onBattleLoaded += self.onBattleLoaded
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
            'position': {'x': 125, 'y': 36},
            'textShadow': {'distance': 0, 'angle': 90, 'color': '#000000', 'alpha': 0.8, 'blurX': 2, 'blurY': 2, 'strength': 2, 'quality': 4},
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

    def readCurrentSettings(self, quiet=True):
        self.color = loadJson(self.ID, 'colorRatting', self.color, self.configPath)
        loadJson(self.ID, 'colorRatting', self.color, self.configPath, True, quiet=True)

    def createTable(self):
        self.color = COLOR_TABLES[self.data['colorRatting']]
        if self.data['colorRatting'] == 0:
            self.color = loadJson(self.ID, 'colorRatting', self.color, self.configPath, True, quiet=False)
        if self.data['colorRatting'] == 1:
            self.color = loadJson(self.ID, 'colorRatting', self.color, self.configPath, True, quiet=False)
        if self.data['colorRatting'] == 2:
            self.color = loadJson(self.ID, 'colorRatting', self.color, self.configPath, True, quiet=False)

    @staticmethod
    def onBattleLoaded():
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_BATTLE)
        if app is None:
            return
        app.loadView(SFViewLoadParams(AS_INJECTOR))


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


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


g_calculator = EfficiencyCalculator()


class BattleEfficiencyInjector(View):

    def _populate(self):
        # noinspection PyProtectedMember
        super(BattleEfficiencyInjector, self)._populate()
        g_events.onBattleClosed += self.destroy

    def _dispose(self):
        g_events.onBattleClosed -= self.destroy
        # noinspection PyProtectedMember
        super(BattleEfficiencyInjector, self)._dispose()

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            return
        super(BattleEfficiencyInjector, self).destroy()


class BattleEfficiencyMeta(BaseDAAPIComponent):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        super(BattleEfficiencyMeta, self).__init__()
        self._arenaDP = self.sessionProvider.getArenaDP()
        self._arenaVisitor = self.sessionProvider.arenaVisitor

    def _populate(self):
        # noinspection PyProtectedMember
        super(BattleEfficiencyMeta, self)._populate()
        logDebug('\'%s\' is loaded', config.ID)

    def _dispose(self):
        # noinspection PyProtectedMember
        super(BattleEfficiencyMeta, self)._dispose()
        logDebug('\'%s\' is destroyed', config.ID)

    @staticmethod
    def getShadowSettings():
        return config.data['textShadow']

    def as_startUpdateS(self, *args):
        return self.flashObject.as_startUpdate(*args) if self._isDAAPIInited() else None

    def as_battleEffS(self, text):
        return self.flashObject.as_battleEff(text) if self._isDAAPIInited() else None


class BattleEfficiency(BattleEfficiencyMeta):

    def __init__(self):
        super(BattleEfficiency, self).__init__()
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
        override(PlayerAvatar, 'vehicle_onAppearanceReady', self.new_onAppearanceReady)
        override(RibbonsAggregator, 'suspend', self.new_suspend)
        override(BattleRibbonsPanel, '_BattleRibbonsPanel__addRibbon', self.new_addRibbon)
        override(DamageLogPanel, '_onTotalEfficiencyUpdated', self.new_onTotalEfficiencyUpdated)
        override(PlayerAvatar, '_PlayerAvatar__startGUI', self.new_startGUI)
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.new_destroyGUI)
        override(BattleResultsWindow, 'as_setDataS', self.new_setDataS)

    def _populate(self):
        super(BattleEfficiency, self)._populate()
        self.as_startUpdateS(config.data)

    def _dispose(self):
        self.destroyTimer()
        super(BattleEfficiency, self)._dispose()

    def stopBattle(self):
        self.__init__()

    @staticmethod
    def readColors(*args, **kwargs):
        return getColor(config.color['colors'], *args, **kwargs)

    @staticmethod
    def check_macros(macros):
        for i in 'format':
            if macros in config.data[i]:
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
        return config.data['format'].format(**self.format_string)

    def startBattle(self):
        if not config.isEnabled:
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

        self.as_battleEffS(self.textGenerator())

    def new_onAppearanceReady(self, func, b_self, vehicle):
        func(b_self, vehicle)
        if config.isEnabled:
            if vehicle.id == self.playerVehicleID:
                g_calculator.registerVInfoData(vehicle.typeDescriptor.type.compactDescr)
                self.startBattle()

    @staticmethod
    def new_suspend(func, b_self):
        if not config.data['enabled']:
            func(b_self)
            return

    def new_addRibbon(self, func, b_self, ribbonID, ribbonType='', leftFieldStr='', **kwargs):
        func(b_self, ribbonID, ribbonType, leftFieldStr, **kwargs)
        if not config.isEnabled:
            return

        if ribbonType not in (BATTLE_EFFICIENCY_TYPES.DETECTION, BATTLE_EFFICIENCY_TYPES.DESTRUCTION, BATTLE_EFFICIENCY_TYPES.DEFENCE, BATTLE_EFFICIENCY_TYPES.CAPTURE):
            return

        if ribbonType == BATTLE_EFFICIENCY_TYPES.DETECTION:
            self.spotted += 1 if (len(leftFieldStr.strip()) == 0) else int(leftFieldStr[1:])
        elif ribbonType == BATTLE_EFFICIENCY_TYPES.DESTRUCTION:
            self.frags += 1
        elif ribbonType == BATTLE_EFFICIENCY_TYPES.DEFENCE:
            self.defence = min(100, self.defence + int(leftFieldStr))
        elif ribbonType == BATTLE_EFFICIENCY_TYPES.CAPTURE:
            self.capture = int(leftFieldStr)

        self.startBattle()

    def new_onTotalEfficiencyUpdated(self, func, b_self, diff):
        func(b_self, diff)
        if config.isEnabled:

            if PERSONAL_EFFICIENCY_TYPE.DAMAGE in diff:
                self.damage = diff[PERSONAL_EFFICIENCY_TYPE.DAMAGE]
                self.startBattle()

    def new_startGUI(self, func, *args):
        func(*args)
        if config.isEnabled:
            self.startBattle()

    def new_destroyGUI(self, func, *args):
        func(*args)
        self.stopBattle()
        g_calculator.stopBattle()

    def new_setDataS(self, func, b_self, data):
        if config.isEnabled and not config.data['battleResultsWindow']:
            return func(b_self, data)

        def _normalizeString(s):
            return re.sub('<.*?>', '', s.replace('\xc2\xa0', '').replace('.', '').replace(',', ''))

        def _splitArenaStr(s):
            _s = s.replace(u'\xa0\u2014', '-').replace(u'\u2013', '-')
            _s = _s.split('-')
            return _s if (len(_s) == 2) else (s, '')

        try:
            common = data['common']
            if common['bonusType'] in (ARENA_BONUS_TYPE.EVENT_BATTLES, ARENA_BONUS_TYPE.EPIC_RANDOM, ARENA_BONUS_TYPE.EPIC_RANDOM_TRAINING, ARENA_BONUS_TYPE.EPIC_BATTLE):
                return func(b_self, data)
            offset = 0 if common['bonusType'] != ARENA_BONUS_TYPE.RANKED else 4

            teamDict = data['team1']
            statValues = data['personal']['statValues'][0]
            stunStatus = 'vehWStun' if (len(statValues) > (16 + offset)) else 'vehWOStun'
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

            msg = config.data['battleResultsFormat']
            msg = msg.replace('{mapName}', mapName)
            msg = msg.replace('{battleType}', battleType)
            msg = msg.replace('{wn8}', str(wn8))
            msg = msg.replace('{xwn8}', str(xwn8))
            msg = msg.replace('{eff}', str(eff))
            msg = msg.replace('{xeff}', str(xeff))
            msg = msg.replace('{xte}', str(xte))
            msg = msg.replace('{dmg}', str(dmg))
            msg = msg.replace('{c:wn8}', self.readColors('wn8', wn8))
            msg = msg.replace('{c:xwn8}', self.readColors('x', xwn8))
            msg = msg.replace('{c:eff}', self.readColors('eff', eff))
            msg = msg.replace('{c:xeff}', self.readColors('x', xeff))
            msg = msg.replace('{c:xte}', self.readColors('x', xte))
            msg = msg.replace('{c:dmg}', self.readColors('tdb', dmg))

            data['common']['arenaStr'] = msg
        except StandardError:
            traceback.print_exc()
            data['common']['arenaStr'] += '  <font color="#FE0E00">Efficiency Error!</font>'

        g_calculator.stopBattle()
        return func(b_self, data)


g_entitiesFactories.addSettings(ViewSettings(AS_INJECTOR, BattleEfficiencyInjector, AS_SWF, WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
g_entitiesFactories.addSettings(ViewSettings(AS_BATTLE, BattleEfficiency, None, WindowLayer.UNDEFINED, None, ScopeTemplates.DEFAULT_SCOPE))
