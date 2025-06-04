# -*- coding: utf-8 -*-
import codecs
import json
import math
import os
import ssl
import threading
import time
import urllib
import urllib2

from Avatar import PlayerAvatar
from frameworks.wulf import WindowLayer
from gui.battle_control.arena_info.arena_dp import ArenaDataProvider
from gui.battle_results.reusable.players import PlayerInfo
from gui.shared.gui_items.Vehicle import getVehicleClassTag
from gui.shared.personality import ServicesLocator
from helpers import dependency
from helpers.CallbackDelayer import CallbackDelayer
from items import vehicles
from messenger import g_settings
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import DriftkingsConfigInterface, ConfigNoInterface, Analytics, override, getPlayer, logWarning, logError, logInfo


_FLAVOR = 'wg'
HOST = 'https://static.modxvm.com/'
URL_WN8 = HOST + 'wn8-data-exp/json/%s/wn8exp.json' % _FLAVOR
URL_XVM_SCALE = HOST + '/xvmscales-%s.json' % _FLAVOR
CONFIG_DIR = os.path.join('.', 'mods', 'configs', 'Driftkings', '%(mod_ID)s',)
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)


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
        self.version = '1.0.0 (%(file_compile_date)s)'
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
    @staticmethod
    def containerManager(components):
        app = ServicesLocator.appLoader.getDefBattleApp()
        if app:
            container = app.containerManager.getContainer(WindowLayer.VIEW).getView().components[components]
            return container, container.flashObject
        return None, None

    @staticmethod
    def request(region, request, **kwargs):
        kwargs['application_id'] = '53352ebb7cd87e994157d0d1e9f360b1' if region == 'ru' else '14f9ad61272e03b7a446433e732d6b7f'
        api = 'api.tanki.su' if region == 'ru' else 'api.worldoftanks.%s' % region
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


class ScaleRating(object):
    def __init__(self):
        self.expFilePath = None
        self.scales = {}
        self.color = [[] for _ in range(7)]
        self.colors = [
            (config.data['colorRating']['very_bad'], 0),
            (config.data['colorRating']['bad'], 17),
            (config.data['colorRating']['b_average'], 34),
            (config.data['colorRating']['normal'], 53),
            (config.data['colorRating']['good'], 76),
            (config.data['colorRating']['very_good'], 93)
        ]
        self.scales, self.color = self.data()
        self.stat = [
            1.2, 1.5, 1.9, 2.5, 3.1, 3.8, 4.6, 5.5, 6.6, 7.7, 9.0, 10, 12, 14, 15, 17, 19, 21, 24, 26, 28, 31, 33,
            36, 38, 41, 43, 46, 48, 51, 53, 56, 58, 60, 63, 65, 67, 69, 71, 73, 74, 76, 78, 79, 80.8, 82.2, 83.6,
            84.8, 86.0, 87.1, 88.1, 89.0, 89.9, 90.8, 91.6, 92.3, 92.9, 93.6, 94.1, 94.7, 95.1, 95.6, 96.0, 96.4,
            96.7, 97.0, 97.3, 97.6, 97.8, 98.0, 98.2, 98.4, 98.6, 98.7, 98.9, 99.0, 99.1, 99.2, 99.3, 99.37, 99.44,
            99.51, 99.57, 99.62, 99.67, 99.71, 99.75, 99.78, 99.81, 99.84, 99.86, 99.88, 99.9, 99.92, 99.93, 99.95,
            99.96, 99.97, 99.98, 99.99
        ]

    @staticmethod
    def loadJsonData(url, local_path):
        if not os.path.exists(local_path):
            with open(local_path, 'w') as f:
                json.dump({'key': 'value'}, f)
        try:
            # Fix: Pass timeout as a keyword argument
            response = urllib2.urlopen(url, timeout=config.internal_conf['performance']['requestTimeout'])
            with open(local_path, 'wb') as f:
                f.write(response.read())
            logInfo(config.ID, 'Successfully downloaded data from {}', url)
        except Exception as e:
            logError(config.ID, 'Error retrieving data from {}: {}', url, e)

    def data(self):
        for color, _ in self.colors:
            self.color[6].append(color)
        self.expFilePath = os.path.join(CONFIG_DIR, 'xvmscales.json')
        self.loadJsonData(URL_XVM_SCALE, self.expFilePath)
        data = None
        if os.path.isfile(self.expFilePath):
            try:
                with codecs.open(self.expFilePath, 'r', encoding='utf-8-sig') as dataCache:
                    data = json.loads(dataCache.read())
            except Exception as e:
                logError(config.ID, 'Error loading xvmscales.json: {}', e)
        if data:
            for key in ['xeff', 'xwn8']:
                if key in data:
                    self.scales[key] = data[key]
            if all(k in data for k in ['xwn8', 'xeff', 'xwgr', 'xwin', 'xwtr']):
                for color, value in self.colors:
                    self.color[0].append((data['xwn8'][value], color))
                    self.color[1].append((data['xeff'][value], color))
                    self.color[3].append((data['xwgr'][value], color))
                    self.color[4].append((data['xwin'][value], color))
                    self.color[5].append((data['xwtr'][value], color))
        return self.scales, self.color

    def getColor(self, value, rating):
        defaultColor = self.color[6][0] if self.color[6] else '#FFFFFF'
        if value is None:
            return defaultColor
        color_map = {'wn8': self.color[0], 'eff': self.color[1], 'tEFF': self.color[2], 'wgr': self.color[3], 'win': self.color[4], 'wtr': self.color[5]}
        if rating in color_map and color_map[rating]:
            for values, colors in color_map[rating]:
                if value >= values:
                    return colors
        elif rating in ('xwn8', 'xeff', 'xTE', 'xTdb'):
            for colors, values in self.colors:
                if value >= values:
                    return colors
        return defaultColor


class StatRating(object):
    def __init__(self):
        self.expFilePath = None
        self.wn8exp = None
        self.xte = None
        self.xtdb = None
        self.wn8exp, self.xte, self.xtdb = self.data()
        self.cache = {}

    @staticmethod
    def loadJsonData(url, local_path):
        if not os.path.exists(local_path):
            with open(local_path, 'w') as f:
                json.dump({'key': 'value'}, f)
        try:
            # Fix: Pass timeout as a keyword argument
            response = urllib2.urlopen(url, timeout=config.internal_conf['performance']['requestTimeout'])
            with open(local_path, 'wb') as f:
                f.write(response.read())
            logInfo(config.ID, 'Successfully downloaded data from {}', url)
        except Exception as e:
            logError(config.ID,'Error retrieving data from {}: {}', url, e)

    def data(self):
        self.wn8exp = {}
        self.expFilePath = os.path.join(CONFIG_DIR, 'wn8exp.json')
        self.loadJsonData(URL_WN8, self.expFilePath)
        data = None
        if os.path.isfile(self.expFilePath):
            try:
                with codecs.open(self.expFilePath, 'r', encoding='utf-8-sig') as dataCache:
                    data = json.loads(dataCache.read())
            except Exception as e:
                logError(config.ID, 'Error loading wn8exp.json: {}', e)
        if data and 'data' in data:
            for value in data['data']:
                idNum = int(value.pop('IDNum'))
                self.wn8exp[idNum] = {}
                for key in ['expDamage', 'expFrag', 'expSpot', 'expDef', 'expWinRate']:
                    self.wn8exp[idNum][key] = float(value[key])
        return self.wn8exp, self.xte, self.xtdb


class CalculatorRating(object):
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
        if not eff or 'xeff' not in g_scale.scales:
            return 0
        return next((i for i, v in enumerate(g_scale.scales['xeff']) if v > eff), 100)

    @staticmethod
    def xwn8(wn8):
        if not wn8 or 'xwn8' not in g_scale.scales:
            return 0
        return next((i for i, v in enumerate(g_scale.scales['xwn8']) if v > wn8), 100)

    @staticmethod
    def calcWn8(tankId):
        values = [{}, {}, 0, 0]
        level = vehicles.getVehicleType(tankId).level
        level = 10 if level < 1 or level > 10 else level
        for tank_id in g_statR.wn8exp:
            tank_level = vehicles.getVehicleType(tank_id).level
            if tank_level == level:
                values[2] += 1
                tank_class_tag = getVehicleClassTag(vehicles.getVehicleType(tank_id).tags)
                target_class_tag = getVehicleClassTag(vehicles.getVehicleType(tankId).tags)
                if tank_class_tag == target_class_tag:
                    values[3] += 1
                for key in g_statR.wn8exp[tank_id]:
                    values[0][key] = values[0].get(key, 0) + g_statR.wn8exp[tank_id].get(key, 0)
                    if tank_class_tag == target_class_tag:
                        values[1][key] = values[1].get(key, 0) + g_statR.wn8exp[tank_id].get(key, 0)
            continue
        if values[3] > 0:
            for key in values[1]:
                values[1][key] /= values[3]
            g_statR.wn8exp[tankId] = values[1].copy()
            return
        if values[2] > 0:
            for key in values[0]:
                values[0][key] /= values[2]
            g_statR.wn8exp[tankId] = values[0].copy()


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
            self.playersInfo[0][dbID]['c_wn8'] = g_scale.getColor(self.playersInfo[0][dbID]['wn8'], 'wn8')
            self.playersInfo[0][dbID]['c_battles'] = self.getColor('battles', self.playersInfo[0][dbID]['battles'])
            self.playersInfo[0][dbID]['c_winrate'] = self.getColor('winrate', self.playersInfo[0][dbID]['winrate'])
            self.playersInfo[0][dbID]['c_tBattles'] = self.getColor('t_battles', self.playersInfo[0][dbID]['t_battles'])
            cachedData = self.statsCache.get(dbID, None) if config.data['performance']['cacheEnabled'] else None
            if cachedData:
                cacheAge = time.time() - self.cacheTimestamp.get(dbID, 0)
                if cacheAge < config.internal_conf['performance']['cacheExpiry']:
                    dataInfo[dbID] = cachedData['info']
                    if dbID not in dataTanks and cachedData['tanks'] is not None:
                        dataTanks[dbID] = cachedData['tanks']
            if self.loadStat and dbID in dataInfo and dbID in dataTanks and dataInfo[dbID] is not None and dataTanks[
                dbID] is not None:
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
            if tankID not in g_statR.wn8exp:
                g_calRating.calcWn8(tankID)
            if tankID in g_statR.wn8exp:
                expVal = g_statR.wn8exp[tankID]
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
            if value < threshold['value']:
                colorKey = threshold['color'].split(':')[1] if ':' in threshold['color'] else threshold['color']
                return config.data['colorRating'].get(colorKey, '#FFFFFF')
        if thresholds:
            lastThreshold = thresholds[-1]
            colorKey = lastThreshold['color'].split(':')[1] if ':' in lastThreshold['color'] else lastThreshold['color']
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
        g_driftkingsPlayersPanels.updateMode -= self.updateMode
        self.clearCallbacks()

    def new__startGUI(self, func, *args, **kwargs):
        func(*args, **kwargs)
        if not config.data['enabled']:
            return
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


config = ConfigInterface()
statistic_mod = Analytics(config.ID, config.version)
g_event = Events()
g_scale = ScaleRating()
g_statR = StatRating()
g_calRating = CalculatorRating()
g_stats = Statistics()
g_panels = PlayersPanels()
try:
    from DriftkingsPlayersPanelAPI import g_driftkingsPlayersPanels
except ImportError:
    logWarning(config.ID, 'Battle Flash API not found.')
except StandardError:
    logWarning(config.ID, 'Battle Flash API not found.')
