# -*- coding: utf-8 -*-
import json
import os
import urllib2

import ResMgr
import nations
from items import vehicles

from DriftkingsCore import callback, logError, getRegion
from DriftkingsStats import __CORE_NAME__


_FLAVOR = 'wg' if getRegion() != 'RU' else 'lesta'
HOST = 'https://static.modxvm.com/'
URL_WN8 = HOST + 'wn8-data-exp/json/%s/wn8exp.json' % _FLAVOR
URL_XTE = HOST + 'xte.json'
URL_XTDB = HOST + 'xtdb.json'
URL_XVM_SCALE = HOST + '/xvmscales-%s.json' % _FLAVOR
VEHICLE_TYPE_XML_PATH = 'scripts/item_defs/vehicles/'
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

VEHICLE_CLASS_TAGS = frozenset(('lightTank', 'mediumTank', 'heavyTank', 'SPG', 'AT-SPG'))

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
            os.makedirs(self.config_path)
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
        for nation in nations.NAMES:
            nationID = nations.INDICES[nation]
            vehicle_list = vehicles.g_list.getList(nationID)
            for ids, descr in vehicle_list.items():
                if descr.name.endswith('training'):
                    continue
                data = self.createVehicleData(descr, nation)
                res.append(data)
            ResMgr.purge(os.path.join(VEHICLE_TYPE_XML_PATH, nation, 'components', 'guns.xml'), True)
        self.vehicleInfoData = {x['vehCD']:x for x in res}

    @staticmethod
    def createVehicleData(descr, nation):
        return {
            'vehCD': descr.compactDescr,
            'key': descr.name,
            'nation': nation,
            'level': descr.level,
            'vClass': tuple(VEHICLE_CLASS_TAGS & descr.tags)[0],
            'localizedName': descr.shortUserString,
            'localizedShortName': descr.shortUserString,
            'localizedFullName': descr.userString,
            'premium': 'premium' in descr.tags and 'special' not in descr.tags,
            'special': 'special' in descr.tags,
            'isReserved': False
        }

    @staticmethod
    def XvmScaleToSup(x=None):
        xvm2sup = [str(i) for i in xrange(1, 100)]
        if x is None:
            return None
        return xvm2sup[min(100, x) - 1] if x > 0 else 0.0

    @staticmethod
    def loadJsonData(url, local_path):
        if not os.path.exists(local_path):
            with open(local_path, 'w') as f:
                json.dump({'key': 'value'}, f)
        try:
            response = urllib2.urlopen(url)
            with open(local_path, 'wb') as f:
                f.write(response.read())
        except (urllib2.URLError, urllib2.HTTPError) as e:
            logError(__CORE_NAME__, 'Error retrieving data: {}', e)

    def _loadXvmScaleData(self):
        xvmScales_path = os.path.join(self.config_path, 'xvmScales.json')
        self.loadJsonData(URL_XVM_SCALE, xvmScales_path)
        try:
            with open(xvmScales_path, 'r') as xvm_scale:
                self.xvmScale_data = json.load(xvm_scale)
        except (IOError, ValueError) as e:
            logError(__CORE_NAME__, 'Error loading XVM scale data: {}', e)

    def _loadWn8Data(self):
        wn8_cache = os.path.join(self.config_path, 'wn8exp.json')
        if self.settings.get('onlineUpdateData', True):
            self.loadJsonData(URL_WN8, wn8_cache)
            with open(wn8_cache) as origExpectedValuesJson:
                origExpectedValues = json.load(origExpectedValuesJson)
                self.wn8_data = origExpectedValues
                for x in origExpectedValues['data']:
                    vinfo = self.getVehicleInfoData(int(x['IDNum']))
                    if vinfo is not None:
                        vinfo.update({
                            'wn8expDamage': float(x['expDamage']),
                            'wn8expSpot': float(x['expSpot']),
                            'wn8expWinRate': float(x['expWinRate']),
                            'wn8expDef': float(x['expDef']),
                            'wn8expFrag': float(x['expFrag'])
                        })

    def _loadXteData(self):
        xte_path = os.path.join(self.config_path, 'xte.json')
        self.loadJsonData(URL_XTE, xte_path)
        with open(xte_path) as xte_scale:
            self.xte_data = json.load(xte_scale)
            for key, values in self.xte_data.items():
                vinfo = self.getVehicleInfoData(int(key))
                if vinfo is not None:
                    vinfo.update({
                        'avgdmg': float(values.get('ad', 0)),
                        'topdmg': float(values.get('td', 0)),
                        'avgfrg': float(values.get('af', 0)),
                        'topfrg': float(values.get('tf', 0))
                    })

    def _loadXtdbData(self):
        xtdb_path = os.path.join(self.config_path, 'xtdb.json')
        self.loadJsonData(URL_XTDB, xtdb_path)
        with open(xtdb_path) as xtdb_scale:
            self.xtdb_data = json.load(xtdb_scale)

    def getVehicleInfoData(self, vehCD):
        if not isinstance(vehCD, (int, long)):
            return None
        return self.vehicleInfoData.get(vehCD, None) if self.vehicleInfoData is not None else None

    def getVehicleInfoDataArray(self):
        return self.vehicleInfoData.values() if self.vehicleInfoData is not None else None

    def resetReserve(self):
        for vinfo in self.vehicleInfoData.values():
            vinfo['isReserved'] = False

    def updateReserve(self, vehCD, isReserved):
        if self.vehicleInfoData is not None and vehCD in self.vehicleInfoData:
            self.vehicleInfoData[vehCD]['isReserved'] = isReserved
        return

    def getXvmScaleData(self, rating):
        return self.xvmScale_data.get('x{}'.format(rating), None) if self.xvmScale_data is not None else None

    def getXteData(self, vehCD):
        return self.xte_data.get(str(vehCD), None) if self.xte_data is not None else None

    def getXtdbData(self, vehCD):
        return self.xtdb_data.get(str(vehCD), None) if self.xtdb_data is not None else None

    def calculateXvmScale(self, rating, value):
        data = self.getXvmScaleData(rating)
        return -1 if data is None else next((i for i, v in enumerate(data) if v > value), 100)

    def calculateXTE(self, vehCD, dmg_per_battle, frg_per_battle):
        data = self.getXteData(vehCD)
        if data is None or data['td'] == data['ad'] or data['tf'] == data['af']:
            return -1
        else:
            CD = 3.0
            CF = 1.0
            avgD = float(data['ad'])
            topD = float(data['td'])
            avgF = float(data['af'])
            topF = float(data['tf'])
            dD = dmg_per_battle - avgD
            dF = frg_per_battle - avgF
            minD = avgD * 0.4
            minF = avgF * 0.4
            d = max(0, 1 + dD / (topD - avgD) if dmg_per_battle >= avgD else 1 + dD / (avgD - minD))
            f = max(0, 1 + dF / (topF - avgF) if frg_per_battle >= avgF else 1 + dF / (avgF - minF))
            t = (d * CD + f * CF) / (CD + CF) * 1000.0
            return next((i for i, v in enumerate(data['x']) if v > t), 100)

    def calculateXTDB(self, vehCD, dmg_per_battle):
        data = self.getXtdbData(vehCD)
        return -1 if data is None else next((i for i, v in enumerate(data['x']) if v > dmg_per_battle), 100)

    def getXtdbDataArray(self, vehCD):
        data = self.getXtdbData(vehCD)
        return data['x'] if data is not None else []


try:
    scale_values_instance = ScaleValues()
    getVehicleInfoData = scale_values_instance.getVehicleInfoData
    calculateXvmScale = scale_values_instance.calculateXvmScale
    calculateXTDB = scale_values_instance.calculateXTDB
    calculateXTE = scale_values_instance.calculateXTE
except ImportError as error:
    logError(__CORE_NAME__, 'Scale not imported {}', error)
