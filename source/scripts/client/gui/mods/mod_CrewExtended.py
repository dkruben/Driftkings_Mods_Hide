# -*- coding: utf-8 -*-
import math

from CurrentVehicle import g_currentVehicle
from gui.Scaleform.daapi.view.lobby.barracks import barracks_data_provider
from gui.Scaleform.daapi.view.meta.CrewMeta import CrewMeta
from gui.shared.gui_items.dossier import TankmanDossier
from items import tankmen

from DriftkingsCore import SimpleConfigInterface, override, Analytics


class ConfigInterface(SimpleConfigInterface):
    def __init__(self):
        self.version_int = 1.70
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.7.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU (spoter mods)'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'personalFileTotalXP': True,
            'personalFileSkillXP': True,
            'personalFileSkillBattle': True,
            'currentCrewRankOnTop': True,
            'currentCrewRankBattle': True,
            'currentCrewRoleBattle': False,
            'currentCrewBattleIcon': True,
            'currentColorBattle': '28F09C',
            'currentCrewRankExp': False,
            'currentCrewRoleExp': True,
            'currentCrewExpIcon': True,
            'currentCrewShowNewSkillPercent': True,
            'currentCrewShowSkillResetStatus': True,
            'currentColorExp': '00FFFF',
            'barracksEnable': True,
            'barracksBattleOrExp': True,
            'barracksSkillIcons': True,
            'premiumSkillIcon': '<img align=\'top\' src=\'img://gui/maps/icons/library/referralCoin-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'>',
            'battleIcon': '<img align=\'top\' src=\'img://gui/maps/icons/library/BattleResultIcon-1.png\' height=\'14\' width=\'14\' vspace=\'-3\'>',
            'expIcon': '<img align=\'top\' src=\'img://gui/maps/icons/library/XpIcon-1.png\' height=\'16\' width=\'16\' vspace=\'-3\'>'

        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_personalFileSilverXP_text': 'To reset main skill: {} experience',
            'UI_setting_personalFile_text': 'Personal File :',
            'UI_setting_personalFileTotalXP_text': 'Show total exp',
            'UI_setting_personalFileTotalXP_tooltip': 'Show Total Experience to current tankman',
            'UI_setting_personalFileSkillXP_text': 'Show exp to 100%',
            'UI_setting_personalFileSkillXP_tooltip': 'Show Experience to current skill with format: to 1% (to 100%)',
            'UI_setting_personalFileSkillBattle_text': 'Show battles to 100%',
            'UI_setting_personalFileSkillBattle_tooltip': 'Show Battles to current skill with format: 1 battle to 1% (100 battle to 100%)',

            'UI_setting_currentCrew_text': 'Current Crew :',

            'UI_setting_currentColorBattleCheck_text': 'Change Battles color',
            'UI_setting_currentColorBattle_text': 'Default: <font color=\'#%(currentColorBattle)s\'></font>',
            'UI_setting_currentColorBattle_tooltip': '',

            'UI_setting_currentCrewRankOnTop_text': 'Show Rank on Top',
            'UI_setting_currentCrewRankOnTop_tooltip': 'Default Role on top in current crew list in hangar, change it! :)',
            'UI_setting_currentCrewRankBattle_text': 'Show Battles in Rank',
            'UI_setting_currentCrewRankBattle_tooltip': 'Show Battles to current skill in Rank field',
            'UI_setting_currentCrewRoleBattle_text': 'Show Battles in Role',
            'UI_setting_currentCrewRoleBattle_tooltip': 'Show Battles to current skill in Role field',
            'UI_setting_currentCrewBattleIcon_text': 'Show Battle Icon',
            'UI_setting_currentCrewBattleIcon_tooltip': '',
            'UI_setting_currentCrewRankExp_text': 'Show Exp in Rank',
            'UI_setting_currentCrewRankExp_tooltip': 'Show Exp to current skill in Rank field',
            'UI_setting_currentCrewRoleExp_text': 'Show Exp in Role',
            'UI_setting_currentCrewRoleExp_tooltip': 'Show Exp to current skill in Role field',
            'UI_setting_currentCrewExpIcon_text': 'Show Exp Icon',
            'UI_setting_currentCrewExpIcon_tooltip': '',
            'UI_setting_currentCrewShowNewSkillPercent_text': 'Show percentage new skills',
            'UI_setting_currentCrewShowNewSkillPercent_tooltip': '',
            'UI_setting_currentCrewShowSkillResetStatus_text': 'Show skill reset without gold',
            'UI_setting_currentCrewShowSkillResetStatus_tooltip': '',

            'UI_setting_currentColorExpCheck_text': 'Change Exp color',
            'UI_setting_currentColorExp_text': 'Default: <font color=\'#%(currentColorExp)s\'></font>',
            'UI_setting_currentColorExp_tooltip': '',

            'UI_setting_barracks_text': 'Barracks :',

            'UI_setting_barracksEnable_text': 'Show in Barracks',
            'UI_setting_barracksEnable_tooltip': '',
            'UI_setting_barracksBattleOrExp_text': 'Show Battle or Exp',
            'UI_setting_barracksBattleOrExp_tooltip': 'Enabled: Show Battles to next skill level\nDisabled: Show Experience to next skill level',
            'UI_setting_barracksSkillIcons_text': 'Show Skill Icons',
            'UI_setting_barracksSkillIcons_tooltip': '',
            'UI_setting_premiumSkillIcon_text': 'Icon: Premium crew member',
            'UI_setting_premiumSkillIcon_tooltip': '',
            'UI_setting_battleIcon_text': 'Icon: Battle',
            'UI_setting_battleIcon_tooltip': '',
            'UI_setting_expIcon_text': 'Icon: Experience',
            'UI_setting_expIcon_tooltip': '',

        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        xLabel1 = self.tb.createLabel('currentCrew')
        xLabel1['text'] += ''

        xColorBattle = self.tb.createControl('currentColorBattle', self.tb.types.ColorChoice)
        xColorBattle['text'] = self.tb.getLabel('currentColorBattleCheck')
        xColorBattle['tooltip'] %= {'currentColorBattle': self.data['currentColorBattle']}

        xLabel2 = self.tb.createLabel('personalFile')
        xLabel2['text'] += ''

        xColorExp = self.tb.createControl('currentColorExp', self.tb.types.ColorChoice)
        xColorExp['text'] = self.tb.getLabel('currentColorExpCheck')
        xColorExp['tooltip'] %= {'currentColorExp': self.data['currentColorExp']}

        xLabel3 = self.tb.createLabel('barracks')
        xLabel3['text'] += ''

        return {
            'modDisplayName': self.i18n['UI_description'],
            'settingsVersion': 1,
            'enabled': self.data['enabled'],
            'column1': [
                xLabel1,
                self.tb.createControl('currentCrewBattleIcon'),
                self.tb.createControl('currentCrewRankBattle'),
                self.tb.createControl('currentCrewShowNewSkillPercent'),
                self.tb.createControl('currentCrewRoleBattle'),
                self.tb.createControl('currentCrewShowNewSkillPercent'),
                xColorBattle,
                xLabel2,
                self.tb.createControl('personalFileTotalXP'),
                self.tb.createControl('personalFileSkillBattle'),
                self.tb.createControl('personalFileSkillXP')
            ],
            'column2': [
                self.tb.createControl('currentCrewRankOnTop'),
                self.tb.createControl('currentCrewExpIcon'),
                self.tb.createControl('currentCrewRankExp'),
                self.tb.createControl('currentCrewRoleExp'),
                self.tb.createControl('currentCrewShowSkillResetStatus'),
                xColorExp,
                xLabel3,
                self.tb.createControl('barracksEnable'),
                self.tb.createControl('barracksBattleOrExp'),
                self.tb.createControl('barracksSkillIcons')
            ]
        }

    @property
    def checkXVM(self):
        try:
            import xvm_main
            return True
        except ImportError:
            return False

    @staticmethod
    def getLastSkillBattlesLeft(self, tankman):
        if not self.getBattlesCount():
            result = None
        else:
            avgExp = self.getAvgXP()
            newSkillReady = self.tmanDescr.roleLevel == tankmen.MAX_SKILL_LEVEL and (
                        len(self.tmanDescr.skills) == 0 or self.tmanDescr.lastSkillLevel == tankmen.MAX_SKILL_LEVEL)
            if avgExp and not newSkillReady:
                result = max(1, int(math.ceil(tankman.getNextSkillXpCost() / avgExp)))
            else:
                result = 0
        return result

    # noinspection PyProtectedMember
    @staticmethod
    def changeStats(data, dossier, tankman):
        for index in data:
            if config.data['personalFileTotalXP'] and index['label'] == 'common':
                totalXP = dossier._TankmanDossier__packStat('xp', tankman.descriptor.totalXP())
                isMaxRoleLevel = tankman.roleLevel == 100
                if isMaxRoleLevel:
                    silverXP = dossier._TankmanDossier__packStat('empty', 0)
                    silverXP['value'] = config.i18n['UI_setting_personalFileSilverXP_text'].format(dossier._TankmanDossier__formatValueForUI(min(0, tankman.descriptor.freeXP - 39153)))
                    silverXP['secondValue'] = ''
                    index['stats'] += (totalXP, silverXP)
                else:
                    index['stats'] += (totalXP,)
            if index['label'] == 'studying':
                for ids in index['stats']:
                    if config.data['personalFileSkillXP'] and ids['name'] == 'nextSkillXPLeft':
                        ids['value'] = ' '
                        ids['secondValue'] = '%s (%s)' % (ids['secondValue'], dossier._TankmanDossier__formatValueForUI(tankman.getNextSkillXpCost()))
                    if config.data['personalFileSkillBattle'] and ids['name'] == 'nextSkillBattlesLeft':
                        battles = dossier.getLastSkillBattlesLeft(tankman)
                        ids['value'] = '%s (%s)' % (ids['value'], dossier._TankmanDossier__formatValueForUI(battles))
                        ids['secondValue'] = '%s (%s)' % (ids['secondValue'], dossier._TankmanDossier__formatValueForUI(dossier._TankmanDossier__getBattlesLeftOnPremiumVehicle(battles)))
        return data

    # noinspection PyProtectedMember
    def changeTankMan(self, data):
        for tankmenData in data['tankmen']:
            if tankmenData['tankmanID'] in g_currentVehicle.item.crewIndices:
                if config.data['currentCrewRankOnTop']:
                    role, rank = (tankmenData['role'], tankmenData['rank'])
                    tankmenData['role'], tankmenData['rank'] = (rank, role)
                tankman = g_currentVehicle.itemsCache.items.getTankman(tankmenData['tankmanID'])
                dossier = g_currentVehicle.itemsCache.items.getTankmanDossier(tankmenData['tankmanID'])
                exp = max(1, tankman.getNextSkillXpCost() if not None else 0)
                battles = max(1, dossier.getLastSkillBattlesLeft(tankman) if not None else 0)
                if g_currentVehicle.item.isPremium:
                    battles = dossier._TankmanDossier__getBattlesLeftOnPremiumVehicle(battles)
                textBattle = self.generateTextString(dossier, 'Battle', battles, config.data['currentCrewRankOnTop'] and tankman.descriptor.freeSkillsNumber)
                textExp = self.generateTextString(dossier, 'Exp', exp, not config.data['currentCrewRankOnTop'] and tankman.descriptor.freeSkillsNumber)
                tankmenData['rank'] = textBattle[0] + textExp[0] + tankmenData['rank']
                tankmenData['role'] = textBattle[1] + textExp[1] + tankmenData['role']
                if config.data['currentCrewShowNewSkillPercent'] or config.data['currentCrewShowSkillResetStatus']:
                    for skill in tankmenData['skills']:
                        if 'buyCount' in skill:
                            newSkillsCount, lastNewSkillLvl = tankman.newSkillCount
                            level = (newSkillsCount - 1) * 100 + lastNewSkillLvl
                            if level > 0 and level != 100:
                                skill['active'] = tankman.descriptor.freeXP > 39153 if config.data['currentCrewShowSkillResetStatus'] else True
                                skill['icon'] = u'new_skill.png'
                                skill['buy'] = False
                                tankmenData['lastSkillLevel'] = level if config.data['currentCrewShowNewSkillPercent'] else 100
        return data

    @staticmethod
    def generateTextString(dossier, sign, value, premiumSkill):
        text = ''
        if premiumSkill:
            text = config.data['premiumSkillIcon']
        # noinspection PyProtectedMember
        text += '<font color=\'%s\'>%s </font>' % (config.data['currentColor%s' % sign], dossier._TankmanDossier__formatValueForUI(value))
        if config.data['currentCrew%sIcon' % sign]:
            if 'Battle' in sign:
                text += config.data['battleIcon']
            if 'Exp' in sign:
                text += config.data['expIcon']
        return text if config.data['currentCrewRank%s' % sign] else '', text if config.data['currentCrewRole%s' % sign] else ''

    def changeBarracksData(self, tankman, tankmenData):
        dossier = g_currentVehicle.itemsCache.items.getTankmanDossier(tankmenData['tankmanID'])
        if config.data['barracksBattleOrExp']:
            battles = max(1, dossier.getLastSkillBattlesLeft(tankman) if not None else 0)
            if g_currentVehicle.item.isPremium:
                # noinspection PyProtectedMember
                battles = dossier._TankmanDossier__getBattlesLeftOnPremiumVehicle(battles)
            text, _ = self.generateTextString(dossier, 'Battle', battles, tankman.descriptor.freeSkillsNumber)
        else:
            exp = max(1, tankman.getNextSkillXpCost() if not None else 0)
            _, text = self.generateTextString(dossier, 'Exp', exp, tankman.descriptor.freeSkillsNumber)
        skills = ''
        if config.data['barracksSkillIcons']:
            newSkillsCount, lastNewSkillLvl = tankman.newSkillCount
            level = (newSkillsCount - 1) * 100 + lastNewSkillLvl
            for skill in tankman.skills:
                if skill.isEnable:
                    skills += '<img align=\"top\" src=\"img://gui/maps//icons/tankmen/skills/small/%s\" vspace=\"-3\"/>' % skill.icon
                    if skill.level < 100 and not newSkillsCount:
                        skills += '%s%%' % skill.level
            if level > -1:
                skills += '<img align=\"top\" src=\"img://gui/maps//icons/tankmen/skills/small/new_skill.png\" vspace=\"-3\"/>%s%%' % level
        tankmenData['role'] = text + ' ' + tankmenData['role'] + skills
        return tankmenData


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')
TankmanDossier.getLastSkillBattlesLeft = config.getLastSkillBattlesLeft


@override(TankmanDossier, 'getStats')
def new_getStats(func, *args):
    if config.data['enabled']:
        return config.changeStats(func(*args), *args)
    return func(*args)


@override(CrewMeta, 'as_tankmenResponseS')
def new_tankmenResponseS(func, *args):
    import BigWorld
    BigWorld.tankmanResponse = args[0]
    if config.data['enabled']:
        return func(args[0], config.changeTankMan(args[1]))
    return func(*args)


@override(barracks_data_provider, '_packTankmanData')
def new_packTankmenData(func, *args):
    data = func(*args)
    if config.data['enabled'] and config.data['barracksEnable'] and not config.checkXVM:
        return config.changeBarracksData(args[0], data)
    return data
