# -*- coding: utf-8-*-
from helpers import dependency
from skeletons.gui.shared import IItemsCache
from gui.Scaleform.daapi.view.lobby.hangar.ammunition_panel import AmmunitionPanel

from DriftkingsCore import SimpleConfigInterface, Analytics, override, cachedVehicleData


class ConfigInterface(SimpleConfigInterface):
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        self.place = 'img://gui/maps/icons/HangarEfficiency'
        self.icon_size = 'width=\'18\' height=\'18\' vspace=\'-3\''
        self.icons = {
            'assistIcon': '<img src=\'%s/help.png\' %s>' % (self.place, self.icon_size),
            'blockedIcon': '<img src=\'%s/armor.png\' %s>' % (self.place, self.icon_size),
            'damageIcon': '<img src=\'%s/damage.png\' %s>' % (self.place, self.icon_size),
            'winRateIcon': '<img src=\'%s/wins.png\' %s>' % (self.place, self.icon_size),
            'stunIcon': '<img src=\'%s/stun.png\' %s>' % (self.place, self.icon_size),
            'spottedIcon': '<img src=\'%s/detection.png\' %s>' % (self.place, self.icon_size),
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


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


def getAvgData():
    data = cachedVehicleData.efficiencyAvgData
    text = []
    if config.data['avgDamage']:
        text.append('{damageIcon}{damage}')
    if config.data['avgAssist']:
        text.append('{assistIcon}{assist}')
    if config.data['avgBlocked']:
        text.append('{blockedIcon}{blocked}')
    if config.data['avgStun'] and data.stun:
        text.append('{stunIcon}{stun}')
    if config.data['winRate']:
        text.append('{winRateIcon}{winRate}%')
    if config.data['gunMarks'] and data.marksAvailable:
        text.append('{marksOnGunIcon}{marksOnGunValue}%')
    if text:
        params = data._asdict()
        params.update(config.icons)
        return '<font face=\'$TitleFont\' size=\'20\' color=\'#FAFAFA\'>%s</font>' % ('  '.join(text).format(**params))
    return ''


@override(AmmunitionPanel, 'as_updateVehicleStatusS')
def updateStatus(func, self, data):
    cachedVehicleData.onVehicleChanged()
    if config.data['enabled']:
        if data['message']:
            data['message'] += '\n' + getAvgData()
        else:
            data['message'] = getAvgData()
    return func(self, data)
