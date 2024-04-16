# -*- coding: utf-8 -*-
from vehinfo import calculateXTE, calculateXTDB, calculateXvmScale, getVehicleInfoData


class _Stat(object):
    def __init__(self):
        self.resp = None

    @staticmethod
    def _fix_common(value):
        if '_id' in value:
            value['player_id'] = value['_id']
            del value['_id']
        if 'nm' in value:
            value['name_db'] = value['nm']
            del value['nm']
        if 'cid' in value:
            value['clan_id'] = value['cid']
            del value['cid']
        if 'b' in value:
            value['battles'] = value['b']
            del value['b']
        if 'w' in value:
            value['wins'] = value['w']
            del value['w']
        if 'e' in value:
            value['eff'] = value['e']
            del value['e']
        if 'lvl' in value:
            value['avglvl'] = value['lvl']
            del value['lvl']
        if 'ver' in value:
            del value['ver']
        if 'st' in value:
            del value['st']
        if 'dt' in value:
            del value['dt']
        if 'cr' in value:
            del value['cr']
        if 'up' in value:
            del value['up']
        if 'rnd' in value:
            del value['rnd']
        if 'lang' in value:
            del value['lang']

        if 'v' not in value:
            value['v'] = {}
        if value.get('eff', 0) <= 0:
            value['eff'] = None
        if value.get('wn8', 0) <= 0:
            value['wn8'] = None
        if value.get('wgr', 0) <= 0:
            value['wgr'] = None
        if value.get('wtr', 0) <= 0:
            value['wtr'] = None

    def _fix_common2(self, stat, orig_name):
        if orig_name is not None:
            stat['name'] = orig_name
        if 'battles' in stat and 'wins' in stat and stat['battles'] > 0:
            self._calculateGWR(stat)
            self._calculateXvmScale(stat)
            if 'v' in stat:
                vData = stat['v']
                if 'id' in vData:
                    self._calculateVehicleValues(stat, vData)
                    self._calculateXTDB(vData)
                    self._calculateXTE(vData)
                    self._calculateVXWTR(vData)
            if 'vehicles' in stat:
                for vehicleID, vData in stat['vehicles'].iteritems():
                    vData['id'] = int(vehicleID)
                    self._calculateVehicleValues(stat, vData)
                    self._calculateXTDB(vData)
                    self._calculateXTE(vData)
                    self._calculateVXWTR(vData)

    # Global Win Rate (GWR)
    @staticmethod
    def _calculateGWR(stat):
        stat['winrate'] = float(stat['wins']) / float(stat['battles']) * 100.0

    # XVM Scale
    @staticmethod
    def _calculateXvmScale(stat):
        if 'wtr' in stat and stat['wtr'] > 0:
            stat['xwtr'] = calculateXvmScale('wtr', stat['wtr'])
        if 'wn8' in stat and stat['wn8'] > 0:
            stat['xwn8'] = calculateXvmScale('wn8', stat['wn8'])
        if 'eff' in stat and stat['eff'] > 0:
            stat['xeff'] = calculateXvmScale('eff', stat['eff'])
        if 'wgr' in stat and stat['wgr'] > 0:
            stat['xwgr'] = calculateXvmScale('wgr', stat['wgr'])
        if 'winrate' in stat and stat['winrate'] > 0:
            stat['xwr'] = calculateXvmScale('win', stat['winrate'])

    # calculate Vehicle values
    @staticmethod
    def _calculateVehicleValues(stat, value):
        vehicleID = value['id']
        vData = getVehicleInfoData(vehicleID)
        if vData is None:
            return

        # tank rating
        if 'b' not in value or 'w' not in value or value['b'] <= 0:
            value['winrate'] = stat['winrate']
        else:
            Tr = float(value['w']) / float(value['b']) * 100.0
            if value['b'] > 100:
                value['winrate'] = Tr
            else:
                Or = float(stat['winrate'])
                Tb = float(value['b']) / 100.0
                Tl = float(min(vData['level'], 4)) / 4.0
                value['winrate'] = Or - (Or - Tr) * Tb * Tl

        if 'b' not in value or value['b'] <= 0:
            return

        vb = float(value['b'])
        if 'dmg' in value and value['dmg'] > 0:
            value['db'] = float(value['dmg']) / vb
            value['dv'] = float(value['dmg']) / vb / vData['hpTop']
        if 'frg' in value and value['frg'] > 0:
            value['fb'] = float(value['frg']) / vb
        if 'spo' in value and value['spo'] > 0:
            value['sb'] = float(value['spo']) / vb

    # calculate xTDB
    @staticmethod
    def _calculateXTDB(value):
        if 'db' not in value or value['db'] < 0:
            return
        value['xtdb'] = calculateXTDB(value['id'], float(value['db']))

    # calculate xTE
    @staticmethod
    def _calculateXTE(value):
        if 'db' not in value or value['db'] < 0:
            return
        if 'fb' not in value or value['fb'] < 0:
            return
        value['xte'] = calculateXTE(value['id'], float(value['db']), float(value['fb']))

    # calculate per-vehicle xWTR
    @staticmethod
    def _calculateVXWTR(value):
        if 'wtr' in value and value['wtr'] > 0:
            value['xwtr'] = calculateXvmScale('wtr', value['wtr'])


xvm_stat = _Stat()
