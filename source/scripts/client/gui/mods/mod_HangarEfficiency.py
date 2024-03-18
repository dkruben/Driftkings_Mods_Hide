# -*- coding: utf-8-*-
from collections import namedtuple

from dossiers2.ui.achievements import MARK_ON_GUN_RECORD
from helpers import dependency
from skeletons.gui.shared import IItemsCache
from CurrentVehicle import g_currentVehicle
from gui.Scaleform.daapi.view.lobby.hangar.ammunition_panel import AmmunitionPanel

from DriftkingsCore import SimpleConfigInterface, Analytics, override, logDebug

EfficiencyAVGData = namedtuple('EfficiencyAVGData', ('damage', 'assist', 'stun', 'blocked', 'marksOnGunValue', 'marksOnGunIcon', 'name', 'marksAvailable', 'winRate'))


class ConfigInterface(SimpleConfigInterface):
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        default = 2500
        self.__default = EfficiencyAVGData(default, default, default, 0, 0.0, '', 'Undefined', False, 0.0)
        self.__EfficiencyAVGData = None

        self.place = 'img://gui/maps/icons/HangarEfficiency'
        self.icon_size = 'width=\'18\' height=\'18\' vspace=\'-3\''
        self.icons = {
            'assistIcon': '<img src=\'{}/help.png\' {}>'.format(self.place, self.icon_size),
            'blockedIcon': '<img src=\'{}/armor.png\' {}>'.format(self.place, self.icon_size),
            'damageIcon': '<img src=\'{}/damage.png\' {}>'.format(self.place, self.icon_size),
            'winRateIcon': '<img src=\'{}/wins.png\' {}>'.format(self.place, self.icon_size),
            'stunIcon': '<img src=\'{}/stun.png\' {}>'.format(self.place, self.icon_size),
            'spottedIcon': '<img src=\'{}/detection.png\' {}>'.format(self.place, self.icon_size),
        }
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'avgAssist': False,
            'avgBlocked': False,
            'avgDamage': False,
            'avgStun': False,
            'gunMarks': False,
            'winRate': False
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_avgAssist_text': 'Avg Assist',
            'UI_setting_avgAssist_tooltip': '',
            'UI_setting_avgBlocked_text': 'Avg Blocked',
            'UI_setting_avgBlocked_tooltip': '',
            'UI_setting_avgDamage_text': 'Avg Damage',
            'UI_setting_avgDamage_tooltip': '',
            'UI_setting_avgStun_text': 'Avg Stun',
            'UI_setting_avgStun_tooltip': '',
            'UI_setting_gunMarks_text': 'Gun Marks',
            'UI_setting_gunMarks_tooltip': '',
            'UI_setting_winRate_text': 'Win Rate',
            'UI_setting_winRate_tooltip': '',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('avgAssist'),
                self.tb.createControl('avgBlocked'),
                self.tb.createControl('avgDamage')
            ],
            'column2': [
                self.tb.createControl('avgStun'),
                self.tb.createControl('gunMarks'),
                self.tb.createControl('winRate')
            ]
        }

    def onVehicleChanged(self):
        if g_currentVehicle.isPresent():
            self.setAvgData(g_currentVehicle.intCD, g_currentVehicle.item.userName, g_currentVehicle.item.level)
        else:
            self.__EfficiencyAVGData = None

    @staticmethod
    def getWinsEfficiency(random):
        win_rate = random.getWinsEfficiency()
        return round(win_rate * 100, 2) if win_rate is not None else 0.0

    def setAvgData(self, intCD, name, level):
        dossier = self.itemsCache.items.getVehicleDossier(intCD)
        random = dossier.getRandomStats()
        marksOnGun = random.getAchievement(MARK_ON_GUN_RECORD)
        icon = marksOnGun.getIcons()['95x85'][3:]
        marksOnGunIcon = '<img src=\'img://gui/{}\' width=\'20\' height=\'18\' vspace=\'-8\'>'.format(icon)
        self.__EfficiencyAVGData = EfficiencyAVGData(
            int(random.getAvgDamage() or 0),
            int(random.getDamageAssistedEfficiency() or 0),
            int(random.getAvgDamageAssistedStun() or 0),
            int(random.getAvgDamageBlocked() or 0),
            round(marksOnGun.getDamageRating(), 2),
            marksOnGunIcon,
            name,
            level > 4,
            self.getWinsEfficiency(random)
        )
        logDebug(False, self.__EfficiencyAVGData)

    @property
    def efficiencyAvgData(self):
        return self.__EfficiencyAVGData or self.__default

    def getAvgData(self):
        data = self.efficiencyAvgData
        text = []
        if self.data['avgDamage']:
            text.append('{damageIcon}{damage}')
        if self.data['avgAssist']:
            text.append('{assistIcon}{assist}')
        if self.data['avgBlocked']:
            text.append('{blockedIcon}{blocked}')
        if self.data['avgStun'] and data.stun:
            text.append('{stunIcon}{stun}')
        if self.data['winRate']:
            text.append('{winRateIcon}{winRate}%')
        if self.data['gunMarks'] and data.marksAvailable:
            text.append('{marksOnGunIcon}{marksOnGunValue}%')
        if text:
            params = data._asdict()
            params.update(config.icons)
            return '<font face=\'$TitleFont\' size=\'20\' color=\'#FAFAFA\'>{}</font>'.format('  '.join(text).format(**params))
        return ''


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(AmmunitionPanel, 'as_updateVehicleStatusS')
def updateStatus(func, self, data):
    config.onVehicleChanged()
    if config.data['enabled']:
        if data['message']:
            data['message'] += '\n' + config.getAvgData()
        else:
            data['message'] = config.getAvgData()
    return func(self, data)
