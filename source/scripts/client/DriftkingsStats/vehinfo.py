# -*- coding: utf-8 -*-
"""
Vehicle information and statistics module for Driftkings.
Handles loading, processing and calculation of various tank statistics.
"""
import json
import os
import urllib2
from contextlib import closing

import ResMgr
import nations
from items import vehicles

from DriftkingsCore import callback, logError
from DriftkingsStats import __CORE_NAME__


_FLAVOR = 'wg'
HOST = 'https://static.modxvm.com/'
URL_WN8 = HOST + 'wn8-data-exp/json/%s/wn8exp.json' % _FLAVOR
URL_XTE = HOST + 'xte.json'
URL_XTDB = HOST + 'xtdb.json'
URL_XVM_SCALE = HOST + '/xvmscales-%s.json' % _FLAVOR
VEHICLE_TYPE_XML_PATH = 'scripts/item_defs/vehicles/'
VEHICLE_CLASS_TAGS = frozenset(('lightTank', 'mediumTank', 'heavyTank', 'SPG', 'AT-SPG'))


UNKNOWN_VEHICLE_DATA = {
    'vehCD': 0,
    'key': 'unknown',
    'nation': '',
    'level': 0,
    'vClass': '',
    'localizedName': 'unknown',
    'localizedShortName': 'unknown',
    'localizedFullName': 'unknown',
    'premium': False,
    'special': False,
    'tierLo': 0,
    'tierHi': 0,
    'shortName': 'unknown',
    'isReserved': False
}

XVM_SCALE_TO_SUP_CACHE = [str(i) for i in xrange(1, 100)]


class ScaleValues(object):

    def __init__(self):
        self.ID = 'DriftkingsStats'
        self.modsGroup = 'Driftkings'
        self.vehicleInfoData = None
        self.wn8_data = {}
        self.xte_data = {}
        self.xvmScale_data = {}
        self.xtdb_data = {}
        self.config_path = os.path.join('.', 'mods', 'configs', self.modsGroup, self.ID, 'cache')
        if not os.path.exists(self.config_path):
            try:
                os.makedirs(self.config_path)
            except OSError as e:
                logError(__CORE_NAME__, 'Failed to create cache directory: {}', e)
        self.settings = {'onlineUpdateData': True, 'showExpectedTankValuesMessage': True}
        self._initialize_callbacks()
        self.init()

    def _initialize_callbacks(self):
        callback(0, self._loadXvmScaleData)
        callback(0, self._loadWn8Data)
        callback(0, self._loadXteData)
        callback(0, self._loadXtdbData)

    def init(self):
        res = [UNKNOWN_VEHICLE_DATA]
        try:
            for nation in nations.NAMES:
                nationID = nations.INDICES[nation]
                vehicle_list = vehicles.g_list.getList(nationID)

                for ids, descr in vehicle_list.items():
                    if descr.name.endswith('training'):
                        continue
                    try:
                        data = self.createVehicleData(descr, nation)
                        res.append(data)
                    except Exception as e:
                        logError(__CORE_NAME__, 'Error creating vehicle data for {}: {}', descr.name, e)
                ResMgr.purge(os.path.join(VEHICLE_TYPE_XML_PATH, nation, 'components', 'guns.xml'), True)
            self.vehicleInfoData = {x['vehCD']: x for x in res}
        except Exception as e:
            logError(__CORE_NAME__, 'Failed to initialize vehicle data: {}', e)
            self.vehicleInfoData = {UNKNOWN_VEHICLE_DATA['vehCD']: UNKNOWN_VEHICLE_DATA}

    @staticmethod
    def createVehicleData(descr, nation):
        vClass = next(iter(VEHICLE_CLASS_TAGS & descr.tags), '')
        return {
            'vehCD': descr.compactDescr,
            'key': descr.name,
            'nation': nation,
            'level': descr.level,
            'vClass': vClass,
            'localizedName': descr.shortUserString,
            'localizedShortName': descr.shortUserString,
            'localizedFullName': descr.userString,
            'premium': 'premium' in descr.tags and 'special' not in descr.tags,
            'special': 'special' in descr.tags,
            'isReserved': False
        }

    @staticmethod
    def XvmScaleToSup(x=None):
        if x is None:
            return None
        return XVM_SCALE_TO_SUP_CACHE[min(100, x) - 1] if x > 0 else 0.0

    @staticmethod
    def loadJsonData(url, local_path):
        if not os.path.exists(local_path):
            try:
                with open(local_path, 'w') as f:
                    json.dump({'key': 'value'}, f)
            except IOError as e:
                logError(__CORE_NAME__, 'Error creating initial JSON file {}: {}', local_path, e)
                return
        try:
            with closing(urllib2.urlopen(url, timeout=10)) as response:
                data = response.read()
                with open(local_path, 'wb') as f:
                    f.write(data)
        except (urllib2.URLError, urllib2.HTTPError) as e:
            logError(__CORE_NAME__, 'Error retrieving data from {}: {}', url, e)
        except IOError as e:
            logError(__CORE_NAME__, 'Error writing data to {}: {}', local_path, e)

    def _loadXvmScaleData(self):
        xvmScales_path = os.path.join(self.config_path, 'xvmScales.json')
        if self.settings.get('onlineUpdateData', True):
            self.loadJsonData(URL_XVM_SCALE, xvmScales_path)
        try:
            with open(xvmScales_path, 'r') as xvm_scale:
                self.xvmScale_data = json.load(xvm_scale)
        except (IOError, ValueError) as e:
            logError(__CORE_NAME__, 'Error loading XVM scale data: {}', e)
            self.xvmScale_data = {}

    def _loadWn8Data(self):
        wn8_cache = os.path.join(self.config_path, 'wn8exp.json')
        if self.settings.get('onlineUpdateData', True):
            self.loadJsonData(URL_WN8, wn8_cache)
        try:
            with open(wn8_cache) as origExpectedValuesJson:
                origExpectedValues = json.load(origExpectedValuesJson)
                self.wn8_data = origExpectedValues
                for x in origExpectedValues.get('data', []):
                    try:
                        vehCD = int(x['IDNum'])
                        vinfo = self.getVehicleInfoData(vehCD)
                        if vinfo is not None:
                            vinfo.update({'wn8expDamage': float(x['expDamage']), 'wn8expSpot': float(x['expSpot']), 'wn8expWinRate': float(x['expWinRate']), 'wn8expDef': float(x['expDef']), 'wn8expFrag': float(x['expFrag'])})
                    except (KeyError, ValueError) as e:
                        logError(__CORE_NAME__, 'Error processing WN8 data for vehicle: {}', e)
        except (IOError, ValueError) as e:
            logError(__CORE_NAME__, 'Error loading WN8 data: {}', e)

    def _loadXteData(self):
        xte_path = os.path.join(self.config_path, 'xte.json')
        if self.settings.get('onlineUpdateData', True):
            self.loadJsonData(URL_XTE, xte_path)
        try:
            with open(xte_path) as xte_scale:
                self.xte_data = json.load(xte_scale)
                for key, values in self.xte_data.items():
                    try:
                        vinfo = self.getVehicleInfoData(int(key))
                        if vinfo is not None:
                            vinfo.update({'avgdmg': float(values.get('ad', 0)), 'topdmg': float(values.get('td', 0)), 'avgfrg': float(values.get('af', 0)), 'topfrg': float(values.get('tf', 0))})
                    except (ValueError, KeyError) as e:
                        logError(__CORE_NAME__, 'Error processing XTE data for vehicle {}: {}', key, e)
        except (IOError, ValueError) as e:
            logError(__CORE_NAME__, 'Error loading XTE data: {}', e)
            self.xte_data = {}

    def _loadXtdbData(self):
        xtdb_path = os.path.join(self.config_path, 'xtdb.json')
        if self.settings.get('onlineUpdateData', True):
            self.loadJsonData(URL_XTDB, xtdb_path)
        try:
            with open(xtdb_path) as xtdb_scale:
                self.xtdb_data = json.load(xtdb_scale)
        except (IOError, ValueError) as e:
            logError(__CORE_NAME__, 'Error loading XTDB data: {}', e)
            self.xtdb_data = {}

    def getVehicleInfoData(self, vehCD):
        if not isinstance(vehCD, (int, long)):
            return None
        return self.vehicleInfoData.get(vehCD) if self.vehicleInfoData is not None else None

    def getVehicleInfoDataArray(self):
        return list(self.vehicleInfoData.values()) if self.vehicleInfoData is not None else []

    def resetReserve(self):
        if self.vehicleInfoData is not None:
            for vinfo in self.vehicleInfoData.values():
                vinfo['isReserved'] = False

    def updateReserve(self, vehCD, isReserved):
        if self.vehicleInfoData is not None and vehCD in self.vehicleInfoData:
            self.vehicleInfoData[vehCD]['isReserved'] = isReserved

    def getXvmScaleData(self, rating):
        if self.xvmScale_data is None:
            return None
        return self.xvmScale_data.get('x{}'.format(rating))

    def getXteData(self, vehCD):
        if self.xte_data is None:
            return None
        return self.xte_data.get(str(vehCD))

    def getXtdbData(self, vehCD):
        if self.xtdb_data is None:
            return None
        return self.xtdb_data.get(str(vehCD))

    def calculateXvmScale(self, rating, value):
        data = self.getXvmScaleData(rating)
        if data is None:
            return -1
        for i, v in enumerate(data):
            if v > value:
                return i
        return 100

    def calculateXTE(self, vehCD, dmg_per_battle, frg_per_battle):
        data = self.getXteData(vehCD)
        if data is None:
            return -1
        if data['td'] == data['ad'] or data['tf'] == data['af']:
            return -1
        CD = 3.0  # Damage coefficient
        CF = 1.0  # Frag coefficient
        avgD = float(data['ad'])  # Average damage
        topD = float(data['td'])  # Top damage
        avgF = float(data['af'])  # Average frags
        topF = float(data['tf'])  # Top frags
        dD = dmg_per_battle - avgD
        dF = frg_per_battle - avgF
        minD = avgD * 0.4
        minF = avgF * 0.4
        if dmg_per_battle >= avgD:
            d = 1 + dD / (topD - avgD)
        else:
            d = 1 + dD / (avgD - minD)

        if frg_per_battle >= avgF:
            f = 1 + dF / (topF - avgF)
        else:
            f = 1 + dF / (avgF - minF)
        d = max(0, d)
        f = max(0, f)
        t = (d * CD + f * CF) / (CD + CF) * 1000.0
        for i, v in enumerate(data['x']):
            if v > t:
                return i
        return 100

    def calculateXTDB(self, vehCD, dmg_per_battle):
        data = self.getXtdbData(vehCD)
        if data is None:
            return -1
        for i, v in enumerate(data['x']):
            if v > dmg_per_battle:
                return i
        return 100

    def getXtdbDataArray(self, vehCD):
        data = self.getXtdbData(vehCD)
        return data['x'] if data is not None else []


try:
    scaleValuesInstance = ScaleValues()
    getVehicleInfoData = scaleValuesInstance.getVehicleInfoData
    calculateXvmScale = scaleValuesInstance.calculateXvmScale
    calculateXTDB = scaleValuesInstance.calculateXTDB
    calculateXTE = scaleValuesInstance.calculateXTE
except ImportError as error:
    logError(__CORE_NAME__, 'Scale not imported: {}', error)
