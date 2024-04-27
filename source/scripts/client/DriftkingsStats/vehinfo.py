# -*- coding: utf-8 -*-
import json
import urllib

import ResMgr
import nations
from gui import SystemMessages
from items import vehicles

from DriftkingsCore import callback, logError
from DriftkingsStats import __CORE_NAME__

# URL
HOST = 'https://static.modxvm.com/'
URL_WN8 = HOST + 'wn8-data-exp/json/wn8exp.json'
URL_XTE = HOST + 'xte.json'
URL_XTDB = HOST + 'xtdb.json'
URL_XVMSCALE = HOST + 'xvmscales.json'

VEHICLE_TYPE_XML_PATH = 'scripts/item_defs/vehicles/'
UNKNOWN_VEHICLE_DATA = {
    'vehCD': 0,
    'key': 'unknown',
    'nation': '',
    'level': 0,
    'v_class': '',
    'localizedName': 'unknown',
    'localizedShortName': 'unknown',
    'localizedFullName': 'unknown',
    'premium': False,
    'special': False,
    'tierLo': 0,
    'tierHi': 0,
    'shortName': 'unknown',
    'isReserved': False,
}

VEHICLE_CLASS_TAGS = frozenset(('lightTank', 'mediumTank', 'heavyTank', 'SPG', 'AT-SPG'))

updateExpectedOK = None
newVersionExpectedTankValues = None
localVersionExpectedTankValues = None


class ScaleValues(object):

    def __init__(self):
        # ID
        self.ID = 'DriftkingsStats'
        # Vehicle
        self.vehicleInfoData = None
        # dicts
        self.wn8_data = {}
        self.xte_data = {}
        self.xvmScale_data = {}
        self.xtdb_data = {}
        # path
        self.config_path = '/'.join(['.', 'mods', 'configs', 'Driftkings', '%s', 'cache']) % self.ID
        self.settings = {
            'onlineUpdateData': True,
            'showExpectedTankValuesMessage': True
        }
        # CALLBACKS
        callback(0, self._loadXvmScaleData)
        callback(0, self._loadWn8Data)
        callback(0, self._loadXteData)
        callback(0, self._loadXtdbData)
        self.init()

    def init(self):
        res = [UNKNOWN_VEHICLE_DATA]
        for nation in nations.NAMES:
            nationID = nations.INDICES[nation]
            for (ids, descr) in vehicles.g_list.getList(nationID).iteritems():
                if descr.name.endswith('training'):
                    continue

                data = dict()
                data['vehCD'] = descr.compactDescr
                data['key'] = descr.name
                data['nation'] = nation
                data['level'] = descr.level
                data['v_class'] = tuple(VEHICLE_CLASS_TAGS & descr.tags)[0]
                data['localizedName'] = descr.shortUserString
                data['localizedShortName'] = descr.shortUserString
                data['localizedFullName'] = descr.userString
                data['premium'] = 'premium' in descr.tags
                data['premium'] = 'premium' in descr.tags and 'special' not in descr.tags
                data['special'] = 'special' in descr.tags
                data['isReserved'] = False
                res.append(data)

            ResMgr.purge(VEHICLE_TYPE_XML_PATH + nation + '/components/guns.xml', True)

        self.vehicleInfoData = {x['vehCD']: x for x in res}

    @staticmethod
    def XvmScaleToSup(x=None):
        xvm2sup = ['1.2', '1.5', '1.9', '2.5', '3.1', '3.8', '4.6', '5.5', '6.6', '7.7', '9.0', '10', '12', '14',
                   '15', '17', '19', '21', '24', '26', '28', '31', '33', '36', '38', '41', '43', '46', '48', '51',
                   '53', '56', '58', '60', '63', '65', '67', '69', '71', '73', '74', '76', '78', '79', '80.8', '82.2',
                   '83.6', '84.8', '86.0', '87.1', '88.1', '89.0', '89.9', '90.8', '91.6', '92.3', '92.9', '93.6',
                   '94.1', '94.7', '95.1', '95.6', '96.0', '96.4', '96.7', '97.0', '97.3', '97.6', '97.8', '98.0',
                   '98.2', '98.4', '98.6', '98.7', '98.9', '99.0', '99.1', '99.2', '99.3', '99.37', '99.44', '99.51',
                   '99.57', '99.62', '99.67', '99.71', '99.75', '99.78', '99.81', '99.84', '99.86', '99.88', '99.90',
                   '99.92', '99.93', '99.95', '99.96', '99.97', '99.98', '99.99']
        if x is None:
            return None
        return xvm2sup[min(100, x) - 1] if x > 0 else 0.0

    def _loadXvmScaleData(self):
        xvmScales_path = '/'.join([self.config_path, 'xvmScales.json'])
        try:
            urllib.urlretrieve(URL_XVMSCALE, xvmScales_path)
        except StandardError:
            pass

        with open(xvmScales_path) as xvm_scale:
            xvm_scale_value = json.load(xvm_scale)
            self.xvmScale_data = xvm_scale_value

    def _loadWn8Data(self):
        global updateExpectedOK, newVersionExpectedTankValues, localVersionExpectedTankValues
        wn8_cache = '/'.join([self.config_path, 'wn8exp.json'])
        if self.settings.get('onlineUpdateData', True):
            expectedTankValuesURL = URL_WN8
            localExpectedTankValues = json.load(open(wn8_cache))
            localVersionExpectedTankValues = json.dumps(localExpectedTankValues['header']['version'])
            updateExpectedOK = False
            try:
                newExpectedValuesPath = urllib.urlopen(expectedTankValuesURL).read()
                newExpectedTankValues = json.loads(newExpectedValuesPath)
                newVersionExpectedTankValues = json.dumps(newExpectedTankValues['header']['version'])
                if newVersionExpectedTankValues != localVersionExpectedTankValues:
                    urllib.urlretrieve(expectedTankValuesURL, wn8_cache)
                    updateExpectedOK = True
            except StandardError:
                pass

        if self.settings['showExpectedTankValuesMessage']:
            if updateExpectedOK:
                SystemMessages.pushMessage('<font color=\'#FFE6B3\'>[DriftkingsStats]</font>\nExpected Tank Values updated to version: ' + newVersionExpectedTankValues, type=SystemMessages.SM_TYPE.Information)
            else:
                SystemMessages.pushMessage('<font color=\'#FFE6B3\'>[DriftkingsStats]</font>\nExpected Tank Values\nversion: ' + localVersionExpectedTankValues, type=SystemMessages.SM_TYPE.Information)

        with open(wn8_cache) as origExpectedValuesJson:
            origExpectedValues = json.load(origExpectedValuesJson)
            self.wn8_data = origExpectedValues
            for x in origExpectedValues['data']:
                vinfo = self.getVehicleInfoData(int(x['IDNum']))
                if vinfo is not None:
                    vinfo['wn8expDamage'] = float(x['expDamage'])
                    vinfo['wn8expSpot'] = float(x['expSpot'])
                    vinfo['wn8expWinRate'] = float(x['expWinRate'])
                    vinfo['wn8expDef'] = float(x['expDef'])
                    vinfo['wn8expFrag'] = float(x['expFrag'])

    def _loadXteData(self):
        xte_path = '/'.join([self.config_path, 'xte.json'])
        try:
            urllib.urlretrieve(URL_XTE, xte_path)
        except StandardError:
            pass

        with open(xte_path) as xte_scale:
            xte_value = json.load(xte_scale)
            self.xte_data = xte_value
            for key, values in self.xte_data.iteritems():
                vinfo = self.getVehicleInfoData(int(key))
                if vinfo is not None:
                    vinfo['avgdmg'] = float(values['ad'])
                    vinfo['topdmg'] = float(values['td'])
                    vinfo['avgfrg'] = float(values['af'])
                    vinfo['topfrg'] = float(values['tf'])

    def _loadXtdbData(self):
        xtdb_path = '/'.join([self.config_path, 'xtdb.json'])
        try:
            urllib.urlretrieve(URL_XTDB, xtdb_path)
        except StandardError:
            pass

        with open(xtdb_path) as xtdb_scale:
            xtdb_value = json.load(xtdb_scale)
            self.xtdb_data = xtdb_value

    def getVehicleInfoData(self, vehCD):
        return self.vehicleInfoData.get(vehCD, None) if self.vehicleInfoData is not None else None

    def getVehicleInfoDataArray(self):
        return self.vehicleInfoData.values() if self.vehicleInfoData is not None else None

    def resetReserve(self):
        for vinfo in self.vehicleInfoData.itervalues():
            vinfo['isReserved'] = False

    def updateReserve(self, vehCD, isReserved):
        if self.vehicleInfoData is not None:
            if vehCD in self.vehicleInfoData:
                self.vehicleInfoData[vehCD]['isReserved'] = isReserved

    def getXvmScaleData(self, rating):
        return self.xvmScale_data.get('x%s' % rating, None) if self.xvmScale_data is not None else None

    def getXteData(self, vehCD):
        return self.xte_data.get(str(vehCD), None) if self.xte_data is not None else None

    def getXtdbData(self, vehCD):
        return self.xtdb_data.get(str(vehCD), None) if self.xtdb_data is not None else None

    # XVM scale for global ratings
    def calculateXvmScale(self, rating, value):
        data = self.getXvmScaleData(rating)
        if data is None:
            return -1
        # calculate XVM Scale
        return next((i for i, v in enumerate(data) if v > value), 100)

    # xte
    def calculateXTE(self, vehCD, dmg_per_battle, frg_per_battle):
        data = self.getXteData(vehCD)
        if data is None or data['td'] == data['ad'] or data['tf'] == data['af']:
            return -1

        # constants
        CD = 3.0
        CF = 1.0

        # input
        avgD = float(data['ad'])
        topD = float(data['td'])
        avgF = float(data['af'])
        topF = float(data['tf'])

        # calculation
        dD = dmg_per_battle - avgD
        dF = frg_per_battle - avgF
        minD = avgD * 0.4
        minF = avgF * 0.4
        d = max(0, 1 + dD / (topD - avgD) if dmg_per_battle >= avgD else 1 + dD / (avgD - minD))
        f = max(0, 1 + dF / (topF - avgF) if frg_per_battle >= avgF else 1 + dF / (avgF - minF))

        t = (d * CD + f * CF) / (CD + CF) * 1000.0

        # calculate XVM Scale
        return next((i for i, v in enumerate(data['x']) if v > t), 100)

    # x_tdb
    def calculateXTDB(self, vehCD, dmg_per_battle):
        data = self.getXtdbData(vehCD)
        if data is None:
            return -1
        # calculate XVM Scale
        return next((i for i, v in enumerate(data['x']) if v > dmg_per_battle), 100)

    def getXtdbDataArray(self, vehCD):
        data = self.getXtdbData(vehCD)
        return data['x'] if data is not None else []


try:
    getVehicleInfoData = ScaleValues().getVehicleInfoData
    calculateXvmScale = ScaleValues().calculateXvmScale
    calculateXTDB = ScaleValues().calculateXTDB
    calculateXTE = ScaleValues().calculateXTE
except ImportError as error:
    logError(__CORE_NAME__, 'Scale not imported {}', error)
