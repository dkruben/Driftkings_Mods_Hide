# -*- coding: utf-8 -*-
import json
import math
import ssl
import threading
import time
import urllib
import urllib2

from Avatar import PlayerAvatar
from frameworks.wulf import WindowLayer
from gui.battle_control.arena_info.arena_dp import ArenaDataProvider
from gui.shared.gui_items.Vehicle import getVehicleClassTag
from gui.shared.personality import ServicesLocator
from helpers import dependency
from helpers.CallbackDelayer import CallbackDelayer
from messenger import g_settings
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import DriftkingsConfigInterface, ConfigNoInterface, Analytics, override, getPlayer, logWarning, logError, logInfo
from DriftkingsStats import calculateXvmScale, getVehicleInfoData, scaleValuesInstance


class ConfigInterface(ConfigNoInterface, DriftkingsConfigInterface):
    def __init__(self):
        self.internal_conf = {
            'performance': {
                'cacheEnabled': True,
                'cacheExpiry': 3600,
                'minBattlesToShow': 10,
                'requestTimeout': 5
            }
        }
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.6 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'global': {
                'anonymizer': {
                    'textColor': 'FFFFFF',
                    'textPrefix': '<b>**</b>'
                }
            },
            'playersPanel': {
                'playerNameCut': {
                    'left': '<font color=\'#{c_wn8}\'>{nick}</font>',
                    'right': '<font color=\'#{c_wn8}\'>{nick}</font>',
                    'width': 160
                },
                'playerNameFull': {
                    'left': '<font color=\'#{c_wn8}\'>{wn8}</font> <font color=\'#{c_wn8}\'>{nick}</font>',
                    'right': '<font color=\'#{c_wn8}\'>{wn8}</font> <font color=\'#{c_wn8}\'>{nick}</font>',
                    'width': 150
                },
                'vehicleName': {
                    'left': '<font color=\'#{c_wn8}\'>{vehicle}</font>',
                    'right': '<font color=\'#{c_wn8}\'>{vehicle}</font>',
                    'width': 75
                }
            },
            'colorRating': {
                'average': 'F8F400',
                'b_average': 'FF6600',
                'bad': 'FF0000',
                'good': '99CC00',
                'great': '66BBFF',
                'normal': 'F8F400',
                'not_available': 'E8E8E8',
                's_unique': 'FF00FF',
                'unique': 'CC66CC',
                'very_bad': 'BB0000',
                'very_good': '00CC00'
            },
            'colors': {
                'wn8': [
                    {'value': 300, 'color': 'color:very_bad'},
                    {'value': 600, 'color': 'color:bad'},
                    {'value': 900, 'color': 'color:b_average'},
                    {'value': 1200, 'color': 'color:normal'},
                    {'value': 1500, 'color': 'color:good'},
                    {'value': 1750, 'color': 'color:very_good'},
                    {'value': 2300, 'color': 'color:great'},
                    {'value': 2900, 'color': 'color:unique'},
                    {'value': 9999, 'color': 'color:s_unique'}
                ],
                'eff': [
                    {'value': 615, 'color': 'color:very_bad'},
                    {'value': 870, 'color': 'color:bad'},
                    {'value': 1175, 'color': 'color:normal'},
                    {'value': 1525, 'color': 'color:good'},
                    {'value': 1850, 'color': 'color:very_good'},
                    {'value': 9999, 'color': 'color:unique'}
                ],
                'winrate': [
                    {'value': 43, 'color': 'color:very_bad'},
                    {'value': 45, 'color': 'color:bad'},
                    {'value': 47, 'color': 'color:b_average'},
                    {'value': 51, 'color': 'color:normal'},
                    {'value': 53, 'color': 'color:good'},
                    {'value': 55, 'color': 'color:very_good'},
                    {'value': 59, 'color': 'color:great'},
                    {'value': 93, 'color': 'color:unique'},
                    {'value': 101, 'color': 'color:s_unique'}
                ],
                't_winrate': [
                    {'value': 46.5, 'color': 'color:very_bad'},
                    {'value': 48.5, 'color': 'color:bad'},
                    {'value': 52.5, 'color': 'color:normal'},
                    {'value': 57.5, 'color': 'color:good'},
                    {'value': 64.5, 'color': 'color:very_good'},
                    {'value': 101, 'color': 'color:unique'}
                ],
                'battles': [
                    {'value': 2000, 'color': 'color:very_bad'},
                    {'value': 6000, 'color': 'color:bad'},
                    {'value': 16000, 'color': 'color:normal'},
                    {'value': 30000, 'color': 'color:good'},
                    {'value': 43000, 'color': 'color:very_good'},
                    {'value': 900000, 'color': 'color:unique'}
                ],
                't_battles': [
                    {'value': 100, 'color': 'color:very_bad'},
                    {'value': 250, 'color': 'color:bad'},
                    {'value': 500, 'color': 'color:normal'},
                    {'value': 1000, 'color': 'color:good'},
                    {'value': 1800, 'color': 'color:very_good'},
                    {'value': 900000, 'color': 'color:unique'}
                ]
            }
        }
        self.i18n = {}
        super(ConfigInterface, self).init()


class Events(object):
    SUPPORTED_REGIONS = ('eu', 'com', 'asia')

    @staticmethod
    def containerManager(components):
        app = ServicesLocator.appLoader.getDefBattleApp()
        if app:
            container = app.containerManager.getContainer(WindowLayer.VIEW).getView().components[components]
            return container, container.flashObject
        return None, None

    @staticmethod
    def request(region, request, **kwargs):
        if region not in Events.SUPPORTED_REGIONS:
            logWarning(config.ID, 'Unsupported region for stats request: {}', region)
            return None
        kwargs['application_id'] = '14f9ad61272e03b7a446433e732d6b7f'
        api = 'api.worldoftanks.%s' % region
        url = 'https://%s/%s/?%s' % (api, request, urllib.urlencode(kwargs))
        try:
            return json.loads(urllib2.urlopen(url).read().decode('utf-8-sig')).get('data', None)
        except:
            return json.loads(urllib2.urlopen(urllib2.Request(url, headers={'User-Agent': 'python2.7/urllib'}), context=ssl._create_unverified_context()).read().decode('utf-8-sig')).get('data', None)

    @staticmethod
    def userRegion(databaseID):
        databaseID = int(databaseID)
        if 500000000 <= databaseID < 1000000000:
            return 'eu'
        elif 1000000000 <= databaseID < 2000000000:
            return 'com'
        elif databaseID >= 2000000000:
            return 'asia'
        return 'eu'


class CalculatorRating(object):
    _wn8Cache = {}

    @staticmethod
    def _expectedFromVehicleData(vehicleData):
        if vehicleData is None:
            return None
        if not all(vehicleData.get(key) is not None for key in ('wn8expDamage', 'wn8expFrag', 'wn8expSpot', 'wn8expDef', 'wn8expWinRate')):
            return None
        return {
            'expDamage': float(vehicleData['wn8expDamage']),
            'expFrag': float(vehicleData['wn8expFrag']),
            'expSpot': float(vehicleData['wn8expSpot']),
            'expDef': float(vehicleData['wn8expDef']),
            'expWinRate': float(vehicleData['wn8expWinRate'])
        }

    @staticmethod
    def wn8(avgDmg, avgDef, avgSpot, avgFrag, avgWin, expDmg, expSpot, expFrag, expDef, expWin):
        if not all([expDmg, expSpot, expFrag, expDef, expWin]):
            return 0
        rWin = max((avgWin / expWin - 0.71) / 0.29000000000000004, 0)
        rDmg = max((avgDmg / expDmg - 0.22) / 0.78, 0)
        rFrag = max(min(rDmg + 0.2, (avgFrag / expFrag - 0.12) / 0.88), 0)
        rSpot = max(min(rDmg + 0.1, (avgSpot / expSpot - 0.38) / 0.62), 0)
        rDef = max(min(rDmg + 0.1, (avgDef / expDef - 0.1) / 0.9), 0)
        return max(0, int(980 * rDmg + 210 * rDmg * rFrag + 155 * rFrag * rSpot + 75 * rDef * rFrag + 145 * min(1.8, rWin)))

    @staticmethod
    def eff(avgDmg, avgDef, avgCap, avgSpot, avgTier, avgFrag):
        if avgTier <= 0:
            avgTier = 1
        return int(round(avgDmg * (10 / (avgTier + 2)) * (0.23 + 2 * avgTier / 100) + avgFrag * 250 + avgSpot * 150 + math.log(avgCap + 1, 1.732) * 150 + avgDef * 150))

    @staticmethod
    def xeff(eff):
        if not eff:
            return 0
        value = calculateXvmScale('eff', eff)
        return value if value >= 0 else 0

    @staticmethod
    def xwn8(wn8):
        if not wn8:
            return 0
        value = calculateXvmScale('wn8', wn8)
        return value if value >= 0 else 0

    @staticmethod
    def getExpectedWn8(tankId):
        expected = CalculatorRating._wn8Cache.get(tankId)
        if expected is not None:
            return expected
        vehicleData = getVehicleInfoData(tankId)
        if vehicleData is None:
            return None
        expected = CalculatorRating._expectedFromVehicleData(vehicleData)
        if expected is not None:
            CalculatorRating._wn8Cache[tankId] = expected
            return expected

        values = [{}, {}, 0, 0]
        level = vehicleData.get('level', 0)
        level = 10 if level < 1 or level > 10 else level
        target_class_tag = vehicleData.get('vClass', '')
        for vData in scaleValuesInstance.getVehicleInfoDataArray():
            tank_level = vData.get('level', 0)
            if tank_level == level:
                values[2] += 1
                tank_class_tag = vData.get('vClass', '')
                if tank_class_tag == target_class_tag:
                    values[3] += 1
                expected = CalculatorRating._expectedFromVehicleData(vData)
                if expected is None:
                    continue
                for key in expected:
                    values[0][key] = values[0].get(key, 0) + expected.get(key, 0)
                    if tank_class_tag == target_class_tag:
                        values[1][key] = values[1].get(key, 0) + expected.get(key, 0)
        if values[3] > 0:
            for key in values[1]:
                values[1][key] /= values[3]
            CalculatorRating._wn8Cache[tankId] = values[1].copy()
            return CalculatorRating._wn8Cache[tankId]
        if values[2] > 0:
            for key in values[0]:
                values[0][key] /= values[2]
            CalculatorRating._wn8Cache[tankId] = values[0].copy()
            return CalculatorRating._wn8Cache[tankId]
        return None


class Statistics(object):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.loadStat = False
        self.playersInfo = [{}, {}]
        self.statsCache = {}
        self.cacheTimestamp = {}
        override(ArenaDataProvider, 'buildVehiclesData', self.new__buildVehiclesData)

    def loadPlayerStats(self, databaseIDs):
        regions = {}
        for databaseID in databaseIDs:
            regions.setdefault(g_event.userRegion(int(databaseID)), []).append(databaseID)
        dataInfo, dataTanks = {}, {}
        for region in regions:
            accountFields = ['client_language', 'global_rating', 'statistics.all.battles', 'statistics.all.wins', 'statistics.all.damage_dealt', 'statistics.all.frags', 'statistics.all.spotted', 'statistics.all.capture_points', 'statistics.all.dropped_capture_points']
            tankFields = ['statistics.battles', 'mark_of_mastery', 'statistics.wins', 'tank_id']
            regionAccounts = ','.join(regions[region])
            infoResponse = g_event.request(region,'wot/account/info', account_id=regionAccounts, fields=','.join(accountFields))
            if infoResponse:
                dataInfo.update(infoResponse)
            tanks_response = g_event.request(region,'wot/account/tanks', account_id=regionAccounts, fields=','.join(tankFields))
            if tanks_response:
                dataTanks.update(tanks_response)
        if config.internal_conf['performance']['cacheEnabled']:
            currentTime = time.time()
            for dbID in dataInfo:
                if dataInfo[dbID] is not None:
                    self.statsCache[dbID] = {'info': dataInfo[dbID], 'tanks': dataTanks.get(dbID, None)}
                    self.cacheTimestamp[dbID] = currentTime
        self.loadStat = bool(dataInfo and dataTanks)
        pColorScheme = g_settings.getColorScheme('battle/player')
        for vehicleID, value in getPlayer().arena.vehicles.items():
            dbID = str(value['accountDBID'])
            self.playersInfo[0][dbID] = {}
            team = self.sessionProvider.getArenaDP().getPlayerGuiProps(vehicleID, value['team']).name().replace('ally', 'teammate')
            self.playersInfo[0][dbID]['name'] = value['name']
            self.playersInfo[0][dbID]['team'] = value['team']
            self.playersInfo[0][dbID]['isAlive'] = value['isAlive']
            self.playersInfo[0][dbID]['level'] = value['vehicleType'].level if hasattr(value['vehicleType'], 'level') else 0
            self.playersInfo[0][dbID]['tank_id'] = value['vehicleType'].type.compactDescr if hasattr(value['vehicleType'], 'type') else 0
            self.playersInfo[0][dbID]['type'] = getVehicleClassTag(value['vehicleType'].type.tags) if hasattr(value['vehicleType'], 'type') else ''
            self.playersInfo[0][dbID]['vehicle'] = value['vehicleType'].type.shortUserString if hasattr(value['vehicleType'], 'type') else ''
            self.playersInfo[0][dbID]['clan'] = '[%s]' % value['clanAbbrev'] if value['clanAbbrev'] else ''
            self.playersInfo[0][dbID]['deadPlayerName'] = ''
            self.playersInfo[0][dbID]['deadPlayerVehicle'] = ''
            self.playersInfo[0][dbID]['c_team'] = '#' + pColorScheme.getHexStr(team)
            self.playersInfo[0][dbID]['t_battles'] = 0
            self.playersInfo[0][dbID]['t_winrate'] = 0
            self.playersInfo[0][dbID]['wn8'] = 0
            self.playersInfo[0][dbID]['eff'] = 0
            self.playersInfo[0][dbID]['xwn8'] = 0
            self.playersInfo[0][dbID]['xeff'] = 0
            self.playersInfo[0][dbID]['spg_battles'] = 0
            self.playersInfo[0][dbID]['mark_of_mastery'] = 0
            self.playersInfo[0][dbID]['wgr'] = 0
            self.playersInfo[0][dbID]['battles'] = 0
            self.playersInfo[0][dbID]['winrate'] = 0
            self.playersInfo[0][dbID]['kb'] = 0
            self.playersInfo[0][dbID]['spg_percent'] = 0
            self.playersInfo[0][dbID]['lang'] = 'en'
            self.playersInfo[0][dbID]['nick'] = self.playersInfo[0][dbID]['name'] + self.playersInfo[0][dbID]['clan']
            self.playersInfo[0][dbID]['short_nick'] = self.playersInfo[0][dbID]['name']
            self.playersInfo[0][dbID]['c_wn8'] = self.getColor('wn8', self.playersInfo[0][dbID]['wn8'])
            self.playersInfo[0][dbID]['c_battles'] = self.getColor('battles', self.playersInfo[0][dbID]['battles'])
            self.playersInfo[0][dbID]['c_winrate'] = self.getColor('winrate', self.playersInfo[0][dbID]['winrate'])
            self.playersInfo[0][dbID]['c_tBattles'] = self.getColor('t_battles', self.playersInfo[0][dbID]['t_battles'])
            cachedData = self.statsCache.get(dbID, None) if config.internal_conf['performance']['cacheEnabled'] else None
            if cachedData:
                cacheAge = time.time() - self.cacheTimestamp.get(dbID, 0)
                if cacheAge < config.internal_conf['performance']['cacheExpiry']:
                    dataInfo[dbID] = cachedData['info']
                    if dbID not in dataTanks and cachedData['tanks'] is not None:
                        dataTanks[dbID] = cachedData['tanks']
            if self.loadStat and dbID in dataInfo and dbID in dataTanks and dataInfo[dbID] is not None and dataTanks[dbID] is not None:
                battles = dataInfo[dbID]['statistics']['all']['battles']
                if battles >= config.internal_conf['performance']['minBattlesToShow']:
                    wins = dataInfo[dbID]['statistics']['all']['wins']
                    avgDmg = dataInfo[dbID]['statistics']['all']['damage_dealt'] / float(battles)
                    avgFrags = dataInfo[dbID]['statistics']['all']['frags'] / float(battles)
                    avgSpot = dataInfo[dbID]['statistics']['all']['spotted'] / float(battles)
                    avgCap = dataInfo[dbID]['statistics']['all']['capture_points'] / float(battles)
                    avgDef = dataInfo[dbID]['statistics']['all']['dropped_capture_points'] / float(battles)
                    winrate = wins * 100.0 / float(battles)
                    self.playersInfo[0][dbID]['wgr'] = dataInfo[dbID]['global_rating']
                    self.playersInfo[0][dbID]['battles'] = battles
                    self.playersInfo[0][dbID]['winrate'] = int(round(winrate, 0))
                    self.playersInfo[0][dbID]['kb'] = "{0}k".format(int(round(battles / 1000.0))) if battles >= 1000 else str(battles)
                    self.playersInfo[0][dbID]['lang'] = dataInfo[dbID]['client_language']
                    for tank in dataTanks[dbID]:
                        if tank['tank_id'] == self.playersInfo[0][dbID]['tank_id'] and tank['statistics']['battles'] != 0:
                            self.playersInfo[0][dbID]['t_battles'] = tank['statistics']['battles']
                            self.playersInfo[0][dbID]['mark_of_mastery'] = tank['mark_of_mastery']
                            if self.playersInfo[0][dbID]['type'] == 'SPG':
                                self.playersInfo[0][dbID]['spg_battles'] += tank['statistics']['battles']
                            self.playersInfo[0][dbID]['t_winrate'] = int(round(tank['statistics']['wins'] * 100.0 / tank['statistics']['battles'], 0))
                    self.playersInfo[0][dbID]['wn8'] = self.wn8(dataTanks[dbID], winrate, avgDmg, avgFrags, avgSpot, avgDef)
                    self.playersInfo[0][dbID]['xwn8'] = g_calRating.xwn8(self.playersInfo[0][dbID]['wn8'])
                    self.playersInfo[0][dbID]['eff'] = g_calRating.eff(avgDmg, avgDef, avgCap, avgSpot, self.playersInfo[0][dbID]['level'], avgFrags)
                    self.playersInfo[0][dbID]['xeff'] = g_calRating.xeff(self.playersInfo[0][dbID]['eff'])
                    self.playersInfo[0][dbID]['c_wn8'] = self.getColor('wn8', self.playersInfo[0][dbID]['wn8'])
                    self.playersInfo[0][dbID]['c_winrate'] = self.getColor('winrate',  self.playersInfo[0][dbID]['winrate'])
                    self.playersInfo[0][dbID]['c_battles'] = self.getColor('battles', self.playersInfo[0][dbID]['battles'])
                    self.playersInfo[0][dbID]['c_tBattles'] = self.getColor('t_battles', self.playersInfo[0][dbID]['t_battles'])

    def getPlayersInfo(self, accountDBID):
        return self.playersInfo[0].get(str(accountDBID), None)

    def getPlayersInfoNone(self, dbID, vInfo):
        dbID = str(dbID)
        self.playersInfo[1][dbID] = {}
        vType = vInfo.vehicleType
        pColorScheme = g_settings.getColorScheme('battle/player')
        self.playersInfo[1][dbID]['t_battles'] = 0
        self.playersInfo[1][dbID]['t_winrate'] = 0
        self.playersInfo[1][dbID]['wn8'] = 0
        self.playersInfo[1][dbID]['eff'] = 0
        self.playersInfo[1][dbID]['xwn8'] = 0
        self.playersInfo[1][dbID]['xeff'] = 0
        self.playersInfo[1][dbID]['spg_battles'] = 0
        self.playersInfo[1][dbID]['mark_of_mastery'] = 0
        self.playersInfo[1][dbID]['name'] = vInfo.player.name
        self.playersInfo[1][dbID]['team'] = vInfo.team
        self.playersInfo[1][dbID]['isAlive'] = vInfo.isAlive()
        self.playersInfo[1][dbID]['level'] = vType.level if hasattr(vType, 'level') else 0
        self.playersInfo[1][dbID]['wgr'] = 0
        self.playersInfo[1][dbID]['battles'] = 0
        self.playersInfo[1][dbID]['winrate'] = 0
        self.playersInfo[1][dbID]['kb'] = 0
        self.playersInfo[1][dbID]['spg_percent'] = 0
        self.playersInfo[1][dbID]['tank_id'] = vType.compactDescr if hasattr(vType, 'compactDescr') else 0
        self.playersInfo[1][dbID]['type'] = vType.classTag if hasattr(vType, 'classTag') else ''
        self.playersInfo[1][dbID]['vehicle'] = vType.shortName if hasattr(vType, 'shortName') else ''
        self.playersInfo[1][dbID]['clan'] = '[%s]' % vInfo.player.clanAbbrev if vInfo.player.clanAbbrev else ''
        self.playersInfo[1][dbID]['lang'] = 'en'
        self.playersInfo[1][dbID]['nick'] = self.playersInfo[1][dbID]['name'] + self.playersInfo[1][dbID]['clan']
        self.playersInfo[1][dbID]['short_nick'] = self.playersInfo[1][dbID]['name']
        team = self.sessionProvider.getCtx().getPlayerGuiProps(vInfo.vehicleID, vInfo.team).name().replace('ally', 'teammate')
        self.playersInfo[1][dbID]['c_team'] = '#' + pColorScheme.getHexStr(team)
        self.playersInfo[1][dbID]['c_wn8'] = self.getColor('wn8', self.playersInfo[1][dbID]['wn8'])
        self.playersInfo[1][dbID]['c_winrate'] = self.getColor('winrate', self.playersInfo[1][dbID]['winrate'])
        self.playersInfo[1][dbID]['c_battles'] = self.getColor('battles', self.playersInfo[1][dbID]['battles'])
        self.playersInfo[1][dbID]['c_tBattles'] = self.getColor('t_battles', self.playersInfo[1][dbID]['t_battles'])
        return self.playersInfo[1][dbID]

    @staticmethod
    def wn8(dossier, winrate, avgDmg, avgFrags, avgSpot, avgDef):
        eFrags = eDmg = eSpot = eDef = eWinrate = eBattles = 0
        for i in range(len(dossier)):
            tankID = dossier[i]['tank_id']
            expVal = g_calRating.getExpectedWn8(tankID)
            if expVal is not None:
                battles = dossier[i]['statistics']['battles']
                eFrags += battles * expVal['expFrag']
                eDmg += battles * expVal['expDamage']
                eSpot += battles * expVal['expSpot']
                eDef += battles * expVal['expDef']
                eWinrate += battles * expVal['expWinRate']
                eBattles += battles
        if eBattles == 0:
            return 0
        rWin = max((winrate * eBattles / eWinrate - 0.71) / 0.29000000000000004, 0)
        rDmg = max((avgDmg * eBattles / eDmg - 0.22) / 0.78, 0)
        rFrag = max(min(rDmg + 0.2, (avgFrags * eBattles / eFrags - 0.12) / 0.88), 0)
        rSpot = max(min(rDmg + 0.1, (avgSpot * eBattles / eSpot - 0.38) / 0.62), 0)
        rDef = max(min(rDmg + 0.1, (avgDef * eBattles / eDef - 0.1) / 0.9), 0)
        return int(round(980 * rDmg + 210 * rDmg * rFrag + 155 * rFrag * rSpot + 75 * rDef * rFrag + 145 * min(1.8, rWin)))

    @staticmethod
    def getColor(rating, value):
        if value is None:
            return config.data['colorRating']['not_available']
        thresholds = config.data['colors'].get(rating, [])
        if not thresholds:
            return config.data['colorRating']['not_available']
        for threshold in thresholds:
            if value < threshold.get('value', 0):
                color = threshold.get('color', '')
                colorKey = color.split(':')[1] if ':' in color else color
                return config.data['colorRating'].get(colorKey, '#FFFFFF')
        if thresholds:
            lastThreshold = thresholds[-1]
            color = lastThreshold.get('color', '')
            colorKey = color.split(':')[1] if ':' in color else color
            return config.data['colorRating'].get(colorKey, '#FFFFFF')
        return config.data['colorRating']['not_available']

    def thread(self, databaseIDs):
        thread = threading.Thread(target=self.loadPlayerStats, args=(databaseIDs,))
        thread.setDaemon(True)
        thread.start()

    def loadStats(self):
        arena = getPlayer().arena
        if arena is not None and arena.bonusType != 6:
            self.thread([str(pl['accountDBID']) for pl in arena.vehicles.values()])

    def reset(self):
        self.__init__()

    def new__buildVehiclesData(self, func, orig, vehicles):
        if not config.data['enabled']:
            return func(orig, vehicles)
        self.loadStats()
        return func(orig, vehicles)


class PlayersPanels(CallbackDelayer):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self):
        self._mode = ''
        self.panels = dict()
        self.container = False
        CallbackDelayer.__init__(self)
        override(PlayerAvatar, '_PlayerAvatar__startGUI', self.new__startGUI)
        override(PlayerAvatar, '_PlayerAvatar__destroyGUI', self.new__destroyGUI)

    def new__destroyGUI(self, func, *args, **kwargs):
        func(*args, **kwargs)
        self._mode = ''
        self.panels = dict()
        self.container = False
        g_stats.reset()
        if g_driftkingsPlayersPanels:
            g_driftkingsPlayersPanels.updateMode -= self.updateMode
        self.clearCallbacks()

    def new__startGUI(self, func, *args, **kwargs):
        func(*args, **kwargs)
        if not config.data['enabled']:
            return
        if g_driftkingsPlayersPanels:
            g_driftkingsPlayersPanels.updateMode += self.updateMode
            self.delayCallback(0, self.playersPanel)

    def updateMode(self):
        self.delayCallback(0.1, self.playersPanel)

    @staticmethod
    def getFakePlayerName(vehicleID=None):
        player = getPlayer()
        arena = player.arena
        if vehicleID and vehicleID in arena.vehicles:
            return arena.vehicles[vehicleID]['name']
        return "Anonymous"

    def playersPanel(self):
        if not g_driftkingsPlayersPanels or not g_driftkingsPlayersPanels.viewLoad:
            return 0
        if not self.container:
            self.container = True
        for vehicleID, info in getPlayer().arena.vehicles.items():
            item = g_driftkingsPlayersPanels.getPPListItem(vehicleID)
            if not item:
                continue
            playerInfo = g_stats.getPlayersInfo(info['accountDBID'])
            vInfo = g_stats.sessionProvider.getArenaDP().getVehicleInfo(vehicleID)
            if playerInfo is None:
                playerInfo = g_stats.getPlayersInfoNone(info['accountDBID'], vInfo)
            team = 'left' if g_stats.sessionProvider.getArenaDP().isAllyTeam(info['team']) else 'right'
            if not info['accountDBID']:
                settings = config.data['global']['anonymizer']
                item.playerNameFullTF.htmlText = '<font color=\'#%s\'>%s %s</font>' % (settings['textColor'], settings['textPrefix'], self.getFakePlayerName(vehicleID))
                item.playerNameCutTF.htmlText = '<font color=\'#%s\'>%s %s</font>' % (settings['textColor'], settings['textPrefix'], self.getFakePlayerName(vehicleID))
                continue
            if playerInfo['battles'] > 0:
                item.playerNameFullTF.htmlText = config.data['playersPanel']['playerNameFull'][team].format(**playerInfo)
                item.playerNameCutTF.htmlText = config.data['playersPanel']['playerNameCut'][team].format(**playerInfo)
            if playerInfo['t_battles'] > 0:
                item.vehicleTF.htmlText = config.data['playersPanel']['vehicleName'][team].format(**playerInfo)
        return 1

config = None
try:
    from DriftkingsPlayersPanelAPI import g_driftkingsPlayersPanels
    config = ConfigInterface()
    statistic_mod = Analytics(config.ID, config.version)
    g_event = Events()
    g_calRating = CalculatorRating()
    g_stats = Statistics()
    g_panels = PlayersPanels()
except ImportError:
    g_driftkingsPlayersPanels = None
    logWarning(config.ID, 'Battle Flash API not found.')
