# -*- coding: utf-8 -*-
import BigWorld
import Math
# noinspection PyUnresolvedReferences
from DriftkingsCore import SimpleConfigInterface, Analytics, override
from tutorial.control.battle.functional import _StaticObjectMarker3D as __StaticObjectMarker3D
try:
    from battle_royale.gui.Scaleform.daapi.view.battle.battle_upgrade_panel import BattleUpgradePanel
    from battle_royale.gui.Scaleform.daapi.view.battle.minimap import plugins
    from battle_royale.gui.Scaleform.daapi.view.battle.minimap.settings import MarkersAs3Descr
    from shared_utils import findFirst
    from battleground.loot_object import LootObject
except StandardError:
    BattleUpgradePanel = False


class ConfigInterface(SimpleConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.version = '1.3.5 (%(file_compile_date)s)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'autoUpgrade': True,
            'showLoot3D': True,

            'selected_Varyag': 4,
            'selected_Walkure': 4,
            'selected_Raven': 9,
            'selected_Arlequin': 8,
            'selected_Harbinger_Mk_IV': 7,

            'Varyag': [
                ['UI_Varyag_DPM_HP', 1, 1, 2, 2, 2, 1],  # DPM HP
                ['UI_Varyag_DPM_Armor', 1, 1, 2, 1, 1, 1],  # DPM Armor
                ['UI_Varyag_Double_Gun_HP', 1, 1, 1, 2, 2, 2],  # Double Gun HP
                ['UI_Varyag_Double_Gun_Armor', 1, 1, 1, 1, 1, 2],  # Double Gun Armor
                ['UI_Varyag_DPS_HP', 1, 1, 2, 2, 2, 3],  # DPS HP
                ['UI_Varyag_DPS_Armor', 1, 1, 2, 1, 2, 3],  # DPS Armor
            ],
            'Walkure': [
                ['UI_Walkure_Machine_Gun_HP', 1, 1, 1, 2, 2, 1],  # Machine Gun HP
                ['UI_Walkure_Machine_Gun_Armor', 1, 1, 1, 1, 1, 1],  # Machine Gun Armor
                ['UI_Walkure_DPM_HP', 1, 1, 1, 2, 2, 2],  # DPM HP
                ['UI_Walkure_DPM_Armor', 1, 1, 1, 1, 1, 2],  # DPM Armor
                ['UI_Walkure_DPS_HP', 1, 1, 1, 2, 2, 3],  # DPS HP
                ['UI_Walkure_DPS_Armor', 1, 1, 1, 1, 2, 3],  # DPS Armor
            ],
            'Raven': [
                ['UI_Raven_DPM_Rotation', 1, 2, 2, 2, 1, 1],  # DPM Rotation
                ['UI_Raven_DPM_Mobility', 1, 2, 2, 1, 1, 1],  # DPM Mobility
                ['UI_Raven_DPM_Armor', 1, 2, 2, 2, 2, 1],  # DPM Armor
                ['UI_Raven_Magazine_Rotation', 1, 2, 1, 2, 1, 2],  # Magazine Rotation
                ['UI_Raven_Magazine_Mobility', 1, 2, 1, 1, 1, 2],  # Magazine Mobility
                ['UI_Raven_Magazine_Speed_Mobility', 1, 1, 1, 1, 1, 2],  # Magazine Speed Mobility
                ['UI_Raven_Magazine_Armor', 1, 2, 1, 2, 2, 2],  # Magazine Armor
                ['UI_Raven_DPS_Mobility', 1, 2, 1, 1, 2, 3],  # DPS Mobility
                ['UI_Raven_DPS_Speed_Mobility', 1, 1, 1, 1, 2, 3],  # DPS Speed Mobility
                ['UI_Raven_DPS_Armor', 1, 2, 1, 2, 2, 3],  # DPS Armor
            ],
            'Arlequin': [
                ['UI_Arlequin_Machine_Gun_Dynamics', 1, 2, 2, 1, 1, 1],  # Dynamics Machine Gun
                ['UI_Arlequin_Machine_Gun_Speed_Mobility', 1, 1, 2, 1, 1, 1],  # Speed Mobility Machine Gun
                ['UI_Arlequin_Machine_Gun_HP', 1, 2, 2, 2, 2, 1],  # Machine Gun HP
                ['UI_Arlequin_Double_Gun_Dynamics', 1, 2, 1, 1, 1, 2],  # Double Gun Dynamics
                ['UI_Arlequin_Double_Gun_Speed_Mobility', 1, 1, 1, 1, 1, 2],  # Double Gun Speed Mobility
                ['UI_Arlequin_Double_Gun_HP', 1, 2, 1, 2, 2, 2],  # Double Gun HP
                ['UI_Arlequin_HE_Dynamics', 1, 2, 2, 1, 2, 3],  # HE Dynamics
                ['UI_Arlequin_HE_Speed_Mobility', 1, 1, 2, 1, 2, 3],  # HE Speed Mobility
                ['UI_Arlequin_HE_HP', 1, 2, 2, 2, 2, 3],  # HP HE
            ],
            'Harbinger_Mk_IV': [
                ['UI_Harbinger_Mk_IV_DPM_Rotation', 1, 2, 1, 2, 1, 1],  # DPM Rotation
                ['UI_Harbinger_Mk_IV_DPM_Mobility', 1, 2, 1, 1, 1, 1],  # DPM Mobility
                ['UI_Harbinger_Mk_IV_DPM_Armor', 1, 2, 1, 2, 2, 1],  # DPM Armor
                ['UI_Harbinger_Mk_IV_Autoreloader_Rotation', 1, 2, 1, 2, 1, 2],  # Rotation Autoreloader
                ['UI_Harbinger_Mk_IV_Autoreloader_Mobility', 1, 2, 1, 1, 1, 2],  # Mobility Autoreloader
                ['UI_Harbinger_Mk_IV_Autoreloader_Speed_Mobility', 1, 1, 1, 1, 1, 2],  # Speed Mobility Autoreloader
                ['UI_Harbinger_Mk_IV_Autoreloader_Armor', 1, 2, 1, 2, 2, 2],  # Armor Autoreloader
                ['UI_Harbinger_Mk_IV_DPS_Mobility', 1, 2, 1, 1, 2, 3],  # Mobility DPS
                ['UI_Harbinger_Mk_IV_DPS_Speed_Mobility', 1, 1, 1, 1, 2, 3],  # Speed Mobility DPS
                ['UI_Harbinger_Mk_IV_DPS_Armor', 1, 2, 1, 2, 2, 3],  # DPS Armor
            ]
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_battleMessage': 'Auto select %s Upgrade to level %s',
            #
            'UI_Varyag_description'                         : 'Varyag',
            'UI_Walkure_description'                        : 'Walkure',
            'UI_Raven_description'                          : 'Raven',
            'UI_Arlequin_description'                       : 'Arlequin',
            'UI_Harbinger_Mk_IV_description'                : 'Harbinger Mk. IV',
            #
            'UI_Varyag_DPM_HP'                              : 'DPM HP [1, 1, 2, 2, 2, 1]',
            'UI_Varyag_DPM_Armor'                           : 'DPM Armor [1, 1, 2, 1, 1, 1]',
            'UI_Varyag_Double_Gun_HP'                       : 'Double Gun HP [1, 1, 1, 2, 2, 2]',
            'UI_Varyag_Double_Gun_Armor'                    : 'Double Gun Armor [1, 1, 1, 1, 1, 2]',
            'UI_Varyag_DPS_HP'                              : 'DPS HP [1, 1, 2, 2, 2, 3]',
            'UI_Varyag_DPS_Armor'                           : 'DPS Armor [1, 1, 2, 1, 2, 3]',
            #
            'UI_Walkure_Machine_Gun_HP'                     : 'Machine Gun HP [1, 1, 1, 2, 2, 1]',
            'UI_Walkure_Machine_Gun_Armor'                  : 'Machine Gun Armor [1, 1, 1, 1, 1, 1]',
            'UI_Walkure_DPM_HP'                             : 'DPM HP [1, 1, 1, 2, 2, 2]',
            'UI_Walkure_DPM_Armor'                          : 'DPM Armor [1, 1, 1, 1, 1, 2]',
            'UI_Walkure_DPS_HP'                             : 'DPS HP [1, 1, 1, 2, 2, 3]',
            'UI_Walkure_DPS_Armor'                          : 'DPS Armor [1, 1, 1, 1, 2, 3]',
            #
            'UI_Raven_DPM_Rotation'                         : 'DPM Rotation [1, 2, 2, 2, 1, 1]',
            'UI_Raven_DPM_Mobility'                         : 'DPM Mobility [1, 2, 2, 1, 1, 1]',
            'UI_Raven_DPM_Armor'                            : 'DPM Armor [1, 2, 2, 2, 2, 1]',
            'UI_Raven_Magazine_Rotation'                    : 'Magazine Rotation [1, 2, 1, 2, 1, 2]',
            'UI_Raven_Magazine_Mobility'                    : 'Magazine Mobility [1, 2, 1, 1, 1, 2]',
            'UI_Raven_Magazine_Speed_Mobility'              : 'Magazine Speed Mobility [1, 1, 1, 1, 1, 2]',
            'UI_Raven_Magazine_Armor'                       : 'Magazine Armor [1, 2, 1, 2, 2, 2]',
            'UI_Raven_DPS_Mobility'                         : 'DPS Mobility [1, 2, 1, 1, 2, 3]',
            'UI_Raven_DPS_Speed_Mobility'                   : 'DPS Speed Mobility [1, 1, 1, 1, 2, 3]',
            'UI_Raven_DPS_Armor'                            : 'DPS Armor [1, 2, 1, 2, 2, 3]',
            #
            'UI_Arlequin_Machine_Gun_Dynamics'              : 'Machine Gun Dynamics [1, 2, 2, 1, 1, 1]',
            'UI_Arlequin_Machine_Gun_Speed_Mobility'        : 'Machine Gun Speed Mobility [1, 1, 2, 1, 1, 1]',
            'UI_Arlequin_Machine_Gun_HP'                    : 'Machine Gun HP [1, 2, 2, 2, 2, 1]',
            'UI_Arlequin_Double_Gun_Dynamics'               : 'Double Gun Dynamics [1, 2, 1, 1, 1, 2]',
            'UI_Arlequin_Double_Gun_Speed_Mobility'         : 'Double Gun Speed Mobility [1, 1, 1, 1, 1, 2]',
            'UI_Arlequin_Double_Gun_HP'                     : 'Double Gun HP [1, 2, 1, 2, 2, 2]',
            'UI_Arlequin_HE_Dynamics'                       : 'HE Dynamics [1, 2, 2, 1, 2, 3]',
            'UI_Arlequin_HE_Speed_Mobility'                 : 'HE Speed Mobility [1, 1, 2, 1, 2, 3]',
            'UI_Arlequin_HE_HP'                             : 'HE HP [1, 2, 2, 2, 2, 3]',
            #
            'UI_Harbinger_Mk_IV_DPM_Rotation'               : 'DPM Rotation [1, 2, 1, 2, 1, 1]',
            'UI_Harbinger_Mk_IV_DPM_Mobility'               : 'DPM Mobility [1, 2, 1, 1, 1, 1]',
            'UI_Harbinger_Mk_IV_DPM_Armor'                  : 'DPM Armor [1, 2, 1, 2, 2, 1]',
            'UI_Harbinger_Mk_IV_Autoreloader_Rotation'      : 'Autoreloader Rotation [1, 2, 1, 2, 1, 2]',
            'UI_Harbinger_Mk_IV_Autoreloader_Mobility'      : 'Autoreloader Mobility [1, 2, 1, 1, 1, 2]',
            'UI_Harbinger_Mk_IV_Autoreloader_Speed_Mobility': 'Autoreloader Speed Mobility [1, 1, 1, 1, 1, 2]',
            'UI_Harbinger_Mk_IV_Autoreloader_Armor'         : 'Autoreloader Armor [1, 2, 1, 2, 2, 2]',
            'UI_Harbinger_Mk_IV_DPS_Mobility'               : 'DPS Mobility [1, 2, 1, 1, 2, 3]',
            'UI_Harbinger_Mk_IV_DPS_Speed_Mobility'         : 'DPS Speed Mobility [1, 1, 1, 1, 2, 3]',
            'UI_Harbinger_Mk_IV_DPS_Armor'                  : 'DPS Armor [1, 2, 1, 2, 2, 3]',
            #
            'UI_autoUpgrade_text': 'Auto-upgrades vehicle in Steel Hunter battle',
            'UI_autoUpgrade_tooltip': '',
            'UI_showLoot3D_text': 'Show 3D loot marker, after press Radar button',
            'UI_showLoot3D_tooltip': '',

        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_name'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('autoUpgrade'),
                self.tb.createControl('showLoot3D'),

                self.tb.createOptions('Varyag'),
                self.tb.createOptions('Walkure'),
                self.tb.createOptions('Raven'),
                self.tb.createOptions('Arlequin'),
                self.tb.createOptions('Harbinger_Mk_IV'),
            ],
            'column2': []
        }


if BattleUpgradePanel:
    VEHICLES = {
        13057: 'Varyag',
        43793: 'Walkure',
        42785: 'Raven',
        13377: 'Arlequin',
        41553: 'Harbinger_Mk_IV',
        0: 'Bái_Láng',
        1: 'Beowulf',
        2: 'Huragan'
    }
    _config = ConfigInterface()
    analytics = Analytics(_config.ID, _config.version, 'UA-121940539-1')

    @override(BattleUpgradePanel, '__onVehicleStateUpdated')
    def onVehicleStateUpdated(func, *args):
        result = func(*args)
        if not _config.data['enabled'] or not _config.data['autoUpgrade']:
            return result
        self = args[0]
        if self._BattleUpgradePanel__vehicleIsAlive and self._BattleUpgradePanel__localVisible and self._BattleUpgradePanel__isEnabled and self._BattleUpgradePanel__upgrades:
            vehicle = self._getVehicle()
            name = VEHICLES[vehicle.intCD]
            ids = _config.data['selected_' + name]
            config = _config.data[name][ids]
            level = self._BattleUpgradePanel__getCurrentLvl()
            selectedItem = config[level]
            selectedLevel = config[selectedItem] - 1
            if level == 6 and config[5] == 2:
                selectedLevel = config[selectedItem] - 2
            self.selectVehicleModule(selectedLevel)
            # inject.message(_config.i18n['UI_battleMessage'] % (selectedItem, level))
        return result


    @override(plugins.BattleRoyaleRadarPlugin, '_addLootEntry')
    def addLootEntry(func, *args):
        entryId = func(*args)
        if not _config.data['enabled'] or not _config.data['showLoot3D']:
            return entryId

        self, typeId, xzPosition = args
        try:
            found = entryId in self._lootEntriesModels
        except:
            self._lootEntriesModels = {}
            found = False

        vEntry = findFirst(lambda entry: entry.entryId == entryId, self._lootEntries)
        if vEntry is not None:
            matrix = self._RadarPlugin__getMatrixByXZ(xzPosition)
            position = matrix.translation
            testResTerrain = BigWorld.wg_collideSegment(BigWorld.player().spaceID, Math.Vector3(position.x, 1000.0, position.z), Math.Vector3(position.x, -1000, position.z), 128)
            if testResTerrain is not None:
                position.y = testResTerrain.closestPoint[1]
            if not found:
                lootTypeParam = self._BattleRoyaleRadarPlugin__getLootMarkerByTypeId(typeId)
                modelPath = 'objects/lootYellow.model'
                if 'improved' in lootTypeParam:
                    modelPath = 'objects/lootGreen.model'
                if 'airdrop' in lootTypeParam:
                    modelPath = 'objects/lootBlue.model'
                self._lootEntriesModels[entryId] = __StaticObjectMarker3D({'path': modelPath}, position)
                self._lootEntriesModels[entryId]._StaticObjectMarker3D__model.scale = Math.Vector3(1.0, 400, 1.0) * 0.1
            self._lootEntriesModels[entryId]._StaticObjectMarker3D__model.position = position
        return entryId


    @override(plugins.BattleRoyaleRadarPlugin, 'timeOutDone')
    def timeOutDone(func, *args):
        result = func(*args)
        if _config.data['enabled'] and _config.data['showLoot3D']:
            self = args[0]
            for entryId in self._lootEntriesModels:
                self._lootEntriesModels[entryId].clear()
            self._lootEntriesModels = {}
        return result
