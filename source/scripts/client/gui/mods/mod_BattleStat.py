# -*- coding: utf-8 -*-
"""
BattleStat - A World of Tanks mod that displays team win chance statistics during battles.
"""
import GUI
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from constants import ARENA_BONUS_TYPE, SHELL_TYPES
from gui import g_guiResetters
from helpers import dependency
from helpers.CallbackDelayer import CallbackDelayer
from items import vehicles
from skeletons.account_helpers.settings_core import ISettingsCore
from vehicle_systems.CompoundAppearance import CompoundAppearance

from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, logError, getPlayer, getEntity, replaceMacros
from DriftkingsInject import g_events


class ConfigInterface(DriftkingsConfigInterface):
    """Configuration interface for the BattleStat mod."""
    def init(self):
        """Initialize configuration settings."""
        self.ID = '%(mod_ID)s'
        self.version = '1.0.6 (%(file_compile_date)s)'
        self.author = 'by: StranikS_Scan, re-coded by: Driftkings'
        self.data = {
            'enabled': True,
            'format': '{header}: {allyChance} {compareSign} {enemyChance}',
            'background': True,
            'textPosition': {
                'alignX': 'right',
                'alignY': 'top',
                'x': -250,
                'y': 443,
                'drag': True,
                'border': False,
                'visible': True,
                'alpha': 1.0,
            },
            'textShadow': {
                'enabled': True,
                'distance': 0,
                'angle': 90,
                'color': '#000000',
                'alpha': 1,
                'blurX': 2,
                'blurY': 2,
                'strength': 100,
                'quality': 1
            },
            'textFormat': {
                'font': '$FieldFont',
                'size': 16,
                'bold': False,
                'italic': False,
                'color': '#DBD7D2',
            },
            'compareValuesColor': {
                'bestValue': '#90EE90',
                'worstValue': '#FFBCAD'
            }
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_teamChances_text': 'Show team chances',
            'UI_setting_teamChances_tooltip': 'Displays win chance percentage for each team during battle',
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        """Create settings template."""
        return {
            'modDisplayName': self.i18n['UI_description'],
            'enabled': self.data['enabled'],
            'column1': [],
            'column2': []
        }


class Flash:
    """Handles the Flash UI elements for displaying statistics."""
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self):
        """Initialize Flash UI settings."""
        textFormat = config.data['textFormat']
        self.font = textFormat['font']
        self.size = textFormat['size']
        self.color = textFormat['color']
        self.bold = textFormat['bold']
        self.italic = textFormat['italic']
        # Prepare HTML formatting tags
        self._begin_tag = '<font face=\'%s\' size=\'%d\' color=\'%s\'>%s%s' % (self.font, self.size, self.color, '<b>' if self.bold else '', '<i>' if self.italic else '')
        self._end_tag = '%s%s</font>' % ('</b>' if self.bold else '', '</i>' if self.italic else '')
        self.name = {}
        self.data = {}

    def startBattle(self):
        """Set up UI elements at battle start."""
        if not config.data['enabled']:
            return
        self.data = self._setup()
        COMPONENT_EVENT.UPDATED += self._updatePosition
        self.createObject(COMPONENT_TYPE.LABEL, self.data[COMPONENT_TYPE.LABEL])
        self.updateObject(COMPONENT_TYPE.LABEL, {'background': config.data['background']})
        self.setShadow()
        g_guiResetters.add(self.screenResize)

    def stopBattle(self):
        """Clean up UI elements at battle end."""
        if not config.data['enabled']:
            return
        g_guiResetters.remove(self.screenResize)
        COMPONENT_EVENT.UPDATED -= self._updatePosition
        self.deleteObject(COMPONENT_TYPE.LABEL)

    def deleteObject(self, name):
        """Delete a UI component."""
        g_guiFlash.deleteComponent(self.name[name])

    def createObject(self, name, data):
        """Create a UI component."""
        g_guiFlash.createComponent(self.name[name], name, data)

    def updateObject(self, name, data):
        """Update a UI component."""
        g_guiFlash.updateComponent(self.name[name], data)

    def _updatePosition(self, alias, props):
        """Update component position when dragged."""
        if str(alias) == str(config.ID):
            x = props.get('x', config.data['textPosition']['x'])
            y = props.get('y', config.data['textPosition']['y'])
            if x and x != config.data['textPosition']['x']:
                config.data['textPosition']['x'] = x
                self.data[COMPONENT_TYPE.LABEL]['x'] = x
            if y and y != config.data['textPosition']['y']:
                config.data['textPosition']['y'] = y
                self.data[COMPONENT_TYPE.LABEL]['y'] = y
            config.onApplySettings({'textPosition': {'x': x, 'y': y}})

    def _setup(self):
        """Set up component data."""
        self.name = {COMPONENT_TYPE.LABEL: str(config.ID)}
        component_data = {
            COMPONENT_TYPE.LABEL: {
                'x': 0,
                'y': 0,
                'drag': True,
                'border': True,
                'alignX': 'center',
                'alignY': 'center',
                'visible': True,
                'text': ''
            }
        }
        for key, value in config.data['textPosition'].items():
            if key in component_data[COMPONENT_TYPE.LABEL]:
                component_data[COMPONENT_TYPE.LABEL][key] = value
        return component_data

    def setShadow(self):
        """Apply shadow settings to the text."""
        if config.data['textShadow']['enabled']:
            shadow_config = config.data['textShadow']
            self.updateObject(COMPONENT_TYPE.LABEL, {
                'shadow': {
                    'distance': shadow_config['distance'],
                    'angle': shadow_config['angle'],
                    'color': shadow_config['color'],
                    'alpha': shadow_config['alpha'],
                    'blurX': shadow_config['blurX'],
                    'blurY': shadow_config['blurY'],
                    'strength': shadow_config['strength'],
                    'quality': shadow_config['quality']
                }
            })

    def getHtmlTextWithTags(self, text, font=None, size=None, color=None, bold=None, italic=None):
        """Format text with HTML tags."""
        if not text:
            return ''
        return '<font face=\'%s\' size=\'%d\' color=\'%s\'>%s%s%s%s%s</font>' % (font if font else self.font, size if size else self.size, color if color else self.color, '<b>' if bold or self.bold else '', '<i>' if italic or self.italic else '', text, '</b>' if bold or self.bold else '', '</i>' if italic or self.italic else '')

    def getSimpleTextWithTags(self, text):
        """Apply default formatting to text."""
        return self._begin_tag + text + self._end_tag if text else ''

    def HtmlText(self, text):
        """Update the label with formatted text."""
        self.updateObject(COMPONENT_TYPE.LABEL, {'text': str(text)})

    def setVisible(self, status):
        """Set component visibility."""
        self.updateObject(COMPONENT_TYPE.LABEL, {'visible': status})

    @staticmethod
    def screenFix(screen, value, align=1):
        """Fix position values to stay within screen bounds."""
        if align == 1:
            if value > screen:
                return float(max(0, screen))
            if value < 0:
                return 0.0
        elif align == -1:
            if value < -screen:
                return min(0, -screen)
            if value > 0:
                return 0.0
        elif align == 0:
            scr = screen / 2.0
            if value < scr:
                return float(scr)
            if value > -scr:
                return float(-scr)
        return value

    def screenResize(self):
        """Handle screen resize events."""
        current_screen = GUI.screenResolution()
        scale = float(self.settingsCore.interfaceScale.get())
        x_max, y_max = current_screen[0] / scale, current_screen[1] / scale
        x = config.data['textPosition'].get('x', None)
        align_x = config.data['textPosition']['alignX']
        if align_x == COMPONENT_ALIGN.LEFT:
            x = self.screenFix(x_max, config.data['textPosition']['x'], 1)
        elif align_x == COMPONENT_ALIGN.RIGHT:
            x = self.screenFix(x_max, config.data['textPosition']['x'], -1)
        elif align_x == COMPONENT_ALIGN.CENTER:
            x = self.screenFix(x_max, config.data['textPosition']['x'], 0)
        if x is not None and x != config.data['textPosition']['x']:
            config.data['textPosition']['x'] = x
            self.data[COMPONENT_TYPE.LABEL]['x'] = x
        y = config.data['textPosition'].get('y', None)
        align_y = config.data['textPosition']['alignY']
        if align_y == COMPONENT_ALIGN.TOP:
            y = self.screenFix(y_max, config.data['textPosition']['y'], 1)
        elif align_y == COMPONENT_ALIGN.BOTTOM:
            y = self.screenFix(y_max, config.data['textPosition']['y'], -1)
        elif align_y == COMPONENT_ALIGN.CENTER:
            y = self.screenFix(y_max, config.data['textPosition']['y'], 0)
        if y is not None and y != config.data['textPosition']['y']:
            config.data['textPosition']['y'] = y
            self.data[COMPONENT_TYPE.LABEL]['y'] = y
        self.updateObject(COMPONENT_TYPE.LABEL, {'x': x, 'y': y})

    def getData(self):
        """Get component data."""
        return self.data

    def getNames(self):
        """Get component names."""
        return self.name


# Initialize configuration and UI components
config = ConfigInterface()
analytics = Analytics(config.ID, config.version)
g_flash = Flash()

# Import gambiter components with error handling
try:
    from gambiter import g_guiFlash
    from gambiter.flash import COMPONENT_TYPE, COMPONENT_EVENT, COMPONENT_ALIGN
except ImportError as err:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    logError(config.ID, 'gambiter.GUIFlash not found. {}', err)


class TanksStatistic:
    """Tracks and calculates team statistics and win chances."""

    def __init__(self):
        """Initialize statistics tracking."""
        self.base = {}
        self.reset()

    def reset(self):
        """Reset all statistical values."""
        self.__allyTanksCount = None
        self.__enemyTanksCount = None
        self.__allyTeamHP = None
        self.__enemyTeamHP = None
        self.__allyTeamOneDamage = None
        self.__enemyTeamOneDamage = None
        self.__allyTeamDPM = None
        self.__enemyTeamDPM = None
        self.__allyTeamForces = None
        self.__enemyTeamForces = None
        self.__enemyChance = None
        self.__allyChance = None

    # Properties with descriptive docstrings
    @property
    def allyChance(self):
        """Win chance percentage for ally team."""
        return self.__allyChance

    @property
    def enemyChance(self):
        """Win chance percentage for enemy team."""
        return self.__enemyChance

    @property
    def allyTanksCount(self):
        """Number of tanks in ally team."""
        return self.__allyTanksCount

    @property
    def enemyTanksCount(self):
        """Number of tanks in enemy team."""
        return self.__enemyTanksCount

    @property
    def allyTeamHP(self):
        """Health points of ally team."""
        return self.__allyTeamHP

    @property
    def enemyTeamHP(self):
        """Health points of enemy team."""
        return self.__enemyTeamHP

    @property
    def allyTeamOneDamage(self):
        """Average damage per shot for ally team."""
        return self.__allyTeamOneDamage

    @property
    def enemyTeamOneDamage(self):
        """Average damage per shot for enemy team."""
        return self.__enemyTeamOneDamage

    @property
    def allyTeamDPM(self):
        """Damage per minute for ally team."""
        return self.__allyTeamDPM

    @property
    def enemyTeamDPM(self):
        """Damage per minute for enemy team."""
        return self.__enemyTeamDPM

    @property
    def allyTeamForces(self):
        """Combat effectiveness of ally team."""
        return self.__allyTeamForces

    @property
    def enemyTeamForces(self):
        """Combat effectiveness of enemy team."""
        return self.__enemyTeamForces

    def _get_team_count(self, is_enemy, with_dead=False):
        """Count tanks in a team."""
        return sum(1 for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def _get_team_hp(self, is_enemy, with_dead=False):
        """Get total HP of a team."""
        return sum(value['hp'] for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def _get_team_damage(self, is_enemy, with_dead=False):
        """Get total damage per shot of a team."""
        return sum(value['gun']['currentDamage'] for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def _get_team_dpm(self, is_enemy, with_dead=False):
        """Get total DPM of a team."""
        return sum(value['gun']['currentDpm'] for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def _get_team_forces(self, is_enemy, with_dead=False):
        """Get total combat effectiveness of a team."""
        return sum(value['force'] for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def __getAllyTanksCount(self, with_dead=False):
        """Count ally tanks."""
        return self._get_team_count(False, with_dead)

    def __getEnemyTanksCount(self, with_dead=False):
        """Count enemy tanks."""
        return self._get_team_count(True, with_dead)

    def __getAllyTeamHP(self, with_dead=False):
        """Get ally team HP."""
        return self._get_team_hp(False, with_dead)

    def __getEnemyTeamHP(self, with_dead=False):
        """Get enemy team HP."""
        return self._get_team_hp(True, with_dead)

    def __getAllyTeamOneDamage(self, with_dead=False):
        """Get ally team damage per shot."""
        return self._get_team_damage(False, with_dead)

    def __getEnemyTeamOneDamage(self, with_dead=False):
        """Get enemy team damage per shot."""
        return self._get_team_damage(True, with_dead)

    def __getAllyTeamDPM(self, with_dead=False):
        """Get ally team DPM."""
        return self._get_team_dpm(False, with_dead)

    def __getEnemyTeamDPM(self, with_dead=False):
        """Get enemy team DPM."""
        return self._get_team_dpm(True, with_dead)

    def __getAllyTeamForces(self, with_dead=False):
        """Get ally team forces."""
        return self._get_team_forces(False, with_dead)

    def __getEnemyTeamForces(self, with_dead=False):
        """Get enemy team forces."""
        return self._get_team_forces(True, with_dead)

    def addVehicleInfo(self, vehicle_id, vehicle_info):
        """Add or update vehicle information in the statistics."""
        if vehicle_id not in self.base:
            v_type = vehicle_info['vehicleType']
            self.base[vehicle_id] = tank = {}
            tank['accountDBID'] = vehicle_info['accountDBID']
            tank['userName'] = vehicle_info['name']
            tank['tank_id'] = v_type.type.compactDescr
            tank['name'] = v_type.type.shortUserString.replace(' ', '')
            tank['type'] = {'tag': set(vehicles.VEHICLE_CLASS_TAGS & v_type.type.tags).pop()}
            tank['isEnemy'] = vehicle_info['team'] != getPlayer().team
            tank['isAlive'] = vehicle_info['isAlive']
            tank['level'] = v_type.level
            tank['hp'] = tank['hpMax'] = v_type.maxHealth
            tank['gun'] = {'reload': float(v_type.gun.reloadTime)}
            if v_type.gun.clip[0] > 1:
                tank['gun']['ammer'] = {'reload': tank['gun']['reload'], 'capacity': v_type.gun.clip[0], 'shellReload': float(v_type.gun.clip[1])}
                tank['gun']['reload'] = (tank['gun']['ammer']['shellReload'] + tank['gun']['ammer']['reload'] / tank['gun']['ammer']['capacity'])
            tank['gun']['shell'] = {'AP': {'damage': 0, 'dpm': 0}, 'APRC': {'damage': 0, 'dpm': 0}, 'HC': {'damage': 0, 'dpm': 0}, 'HE': {'damage': 0, 'dpm': 0}}
            for shot in v_type.gun.shots:
                shell_type = self._getShellType(shot.shell.kind)
                damage = self._getShellDamage(shot.shell)
                if damage > tank['gun']['shell'][shell_type]['damage']:
                    damage_factor = 0.5 if shell_type == 'HE' else 1.0
                    tank['gun']['shell'][shell_type]['damage'] = damage * damage_factor
                    tank['gun']['shell'][shell_type]['dpm'] = damage * 60 / tank['gun']['reload']
            if 'SPG' == tank['type']['tag']:
                shell = 'HE'
            else:
                shell = self._getBestShellType(tank['gun']['shell'])
            tank['gun']['currentShell'] = shell
            tank['gun']['currentDamage'] = tank['gun']['shell'][shell]['damage']
            tank['gun']['currentDpm'] = tank['gun']['shell'][shell]['dpm']

            self.update(0, vehicle_id)

    def _getShellType(self, shell_kind):
        """Convert shell kind to string identifier."""
        if shell_kind == SHELL_TYPES.ARMOR_PIERCING_CR:
            return 'APRC'
        elif shell_kind == SHELL_TYPES.HOLLOW_CHARGE:
            return 'HC'
        elif shell_kind == SHELL_TYPES.HIGH_EXPLOSIVE:
            return 'HE'
        else:
            return 'AP'

    @staticmethod
    def _getShellDamage(shell):
        """Get shell damage value."""
        damage = shell.armorDamage[0] if hasattr(shell, 'armorDamage') else shell.damage[0]
        return float(damage)

    @staticmethod
    def _getBestShellType(shell_data):
        """Determine best shell type based on available options."""
        if shell_data['AP']['damage'] > 0:
            return 'AP'
        elif shell_data['APRC']['damage'] > 0:
            return 'APRC'
        elif shell_data['HC']['damage'] > 0:
            return 'HC'
        else:
            return 'HE'

    def update(self, reason, vehicleID):
        """Update statistics based on changes."""
        if not self.base:
            return
        if reason <= 2:
            self.__allyTeamHP = self.__getAllyTeamHP()
            self.__enemyTeamHP = self.__getEnemyTeamHP()
        if reason <= 1:
            self.__allyTanksCount = self.__getAllyTanksCount()
            self.__enemyTanksCount = self.__getEnemyTanksCount()
            self.__allyTeamOneDamage = self.__getAllyTeamOneDamage()
            self.__enemyTeamOneDamage = self.__getEnemyTeamOneDamage()
            self.__allyTeamDPM = self.__getAllyTeamDPM()
            self.__enemyTeamDPM = self.__getEnemyTeamDPM()
        self._calculateForces()
        self.__allyTeamForces = self.__getAllyTeamForces()
        self.__enemyTeamForces = self.__getEnemyTeamForces()
        all_forces = self.__allyTeamForces + self.__enemyTeamForces
        if all_forces != 0:
            self.__allyChance = 100 * self.__allyTeamForces / all_forces
            self.__enemyChance = 100 * self.__enemyTeamForces / all_forces
            for value in self.base.values():
                if value['isAlive']:
                    value['contribution'] = 100 * value['force'] / all_forces
                else:
                    value['contribution'] = 0
        else:
            self.__allyChance = 0
            self.__enemyChance = 0
        self._triggerEvents(reason, vehicleID)

    def _calculateForces(self):
        """Calculate combat effectiveness for each vehicle."""
        for value in self.base.values():
            if value['isAlive']:
                if value['isEnemy']:
                    value['Th'] = value['hp'] / self.__allyTeamDPM if self.__allyTeamDPM > 0 else 999999.9
                    value['Te'] = self.__allyTeamHP / value['gun']['currentDpm'] if value['gun']['currentDpm'] > 0 else 999999.9
                else:
                    value['Th'] = value['hp'] / self.__enemyTeamDPM if self.__enemyTeamDPM > 0 else 999999.9
                    value['Te'] = self.__enemyTeamHP / value['gun']['currentDpm'] if value['gun']['currentDpm'] > 0 else 999999.9
                value['force'] = value['Th'] / value['Te'] if value['Te'] > 0 else 999999.9
            else:
                value['Th'] = 0
                value['Te'] = 999999.9
                value['force'] = 0

    def _triggerEvents(self, reason, vehicleID):
        """Trigger events based on statistic changes."""
        g_events.onVehiclesChanged(self, reason, vehicleID)
        if reason <= 1:
            g_events.onCountChanged(self.__allyTanksCount, self.__enemyTanksCount)
        g_events.onHealthChanged(self.__allyTeamHP, self.__enemyTeamHP)
        g_events.onChanceChanged(self.__allyChance, self.__enemyChance, self.__allyTeamForces, self.__enemyTeamForces)


# Initialize statistics tracker
g_tanksStatistic = TanksStatistic()


class BattleStatDisplay(CallbackDelayer):
    """Handles the display of battle statistics."""
    def __init__(self):
        """Initialize the display handler."""
        CallbackDelayer.__init__(self)
        self.macro = {}
        self.compareValuesColor = (config.data['compareValuesColor']['bestValue'], config.data['compareValuesColor']['worstValue'], config.data['textFormat']['color'])

    @staticmethod
    def compare_sign(ally, enemy):
        """Get HTML comparison sign based on values."""
        if ally < enemy:
            return '&#x003C;'
        elif ally > enemy:
            return '&#x003E;'
        return '&#x007C;'

    def flash_text(self):
        """Update the displayed text."""
        if not config.data.get('enabled', False):
            return
        g_flash.setVisible(True)
        ally = g_tanksStatistic.allyChance
        enemy = g_tanksStatistic.enemyChance
        ally_text = self.formatChanceText(ally, enemy)
        enemy_text = self.formatChanceText(enemy, ally)
        text = self.formatText(ally_text, enemy_text, ally, enemy)
        data = g_flash.getSimpleTextWithTags(text)
        g_flash.HtmlText(data)
        self.delayCallback(0.3, self.flash_text)

    def formatChanceText(self, value, comparison_value):
        """Format chance text with color based on comparison."""
        if value > comparison_value:
            color = self.compareValuesColor[0]
        elif value < comparison_value:
            color = self.compareValuesColor[1]
        else:
            color = self.compareValuesColor[2]
        return g_flash.getHtmlTextWithTags('%6.2f' % value, color=color)

    def updateMacros(self, data):
        """Update macro dictionary with new values."""
        for key, value in data.items():
            self.macro['{%s}' % key] = str(value)

    def formatText(self, ally_text, enemy_text, ally, enemy):
        """Format the final display text using macros."""
        data = {'header': 'Chances', 'allyChance': ally_text, 'enemyChance': enemy_text, 'compareSign': self.compare_sign(ally, enemy)}
        self.updateMacros(data)
        return replaceMacros(config.data['format'], self.macro)


g_mod = BattleStatDisplay()


# Override hooks for game events
@override(Vehicle, 'onHealthChanged')
def new__onHealthChanged(func, self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
    """Handle vehicle health changes."""
    func(self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs)
    if self.id in g_tanksStatistic.base:
        tank = g_tanksStatistic.base[self.id]
        if tank['hp'] != self.health:
            reason = 2
            tank['hp'] = self.health if self.health > 0 else 0
            if tank['hp'] == 0:
                tank['isAlive'] = False
                reason = 1
            g_tanksStatistic.update(reason, self.id)


@override(PlayerAvatar, 'vehicle_onAppearanceReady')
def new__onAppearanceReady(func, self, vehicle):
    """Handle vehicle appearance ready event."""
    func(self, vehicle)
    if vehicle.id in g_tanksStatistic.base:
        entity = getEntity(vehicle.id)
        if entity:
            tank = g_tanksStatistic.base[vehicle.id]
            if tank['hp'] != entity.health:
                reason = 2
                tank['hp'] = vehicle.health if vehicle.health > 0 else 0
                if tank['hp'] == 0:
                    tank['isAlive'] = False
                    reason = 1
                g_tanksStatistic.update(reason, vehicle.id)


@override(CompoundAppearance, 'prerequisites')
def new__prerequisites(func, self, typeDescriptor, vehicleID, *args, **kwargs):
    """Handle vehicle prerequisites loading."""
    result = func(self, typeDescriptor, vehicleID, *args, **kwargs)
    try:
        g_tanksStatistic.addVehicleInfo(vehicleID, getPlayer().arena.vehicles.get(vehicleID))
    finally:
        return result


@override(PlayerAvatar, '_PlayerAvatar__onArenaVehicleKilled')
def new__onArenaVehicleKilled(func, self, targetID, *args, **kwargs):
    """Handle vehicle killed event."""
    func(self, targetID, *args, **kwargs)
    if targetID in g_tanksStatistic.base:
        tank = g_tanksStatistic.base[targetID]
        if tank['isAlive']:
            tank['isAlive'] = False
            tank['hp'] = 0
            g_tanksStatistic.update(1, targetID)  # Tank destroyed


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(func, self):
    """Handle battle start."""
    func(self)
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        g_tanksStatistic.reset()
        for vehicleID in self.arena.vehicles:
            g_tanksStatistic.addVehicleInfo(vehicleID, self.arena.vehicles.get(vehicleID))
        g_flash.startBattle()
        g_mod.flash_text()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new__destroyGUI(func, *args):
    """Handle battle end."""
    func(*args)
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        g_flash.stopBattle()
