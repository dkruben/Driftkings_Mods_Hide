# -*- coding: utf-8 -*-
import traceback
from math import degrees

import GUI
import Keys
from Avatar import PlayerAvatar
from constants import ARENA_BONUS_TYPE
from gui import InputHandler
from gui import g_guiResetters
from gui.shared.utils.TimeInterval import TimeInterval
from helpers import dependency
from messenger import MessengerEntry
from nations import NAMES
from skeletons.account_helpers.settings_core import ISettingsCore
from gambiter import g_guiFlash
from gambiter.flash import COMPONENT_TYPE, COMPONENT_EVENT, COMPONENT_ALIGN

from DriftkingsCore import DriftkingsConfigInterface, Analytics, getPlayer, getTarget, override, calculate_version, checkKeys

COMPARE_MACROS = ['compareDelim', 'compareColor']
ROMAN_LEVELS = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI')
PRESET_TEMPLATES = {
    'default': "<font face='$FieldFont' size='16' color='#FFFFFF'><b><font color='#FFA500'>{{vehicle_name}}</font> ({{vehicle_type}} {{level}})</b></font>\n<font color='#14AFF1'>Reload: {{gun_reload}} sec | DPM: {{gun_dpm_equip}}</font>\n<font color='#96CC29'>View: {{vision_radius}}m | Camo: {{invis_stand}}</font>\n<font color='#FF9999'>Armor: {{armor_hull_front}}/{{armor_hull_side}}/{{armor_hull_back}} | HP: {{vehicle_max_health}}</font>\n<font color='#FFCC00'>Speed: {{speed_forward}}km/h | Shell: {{shell_damage_1}}dmg</font>",
    'minimal': "<font face='$FieldFont' size='16' color='#FFFFFF'><b>{{vehicle_name}} ({{vehicle_type}} {{level}})</b></font>\n<font color='#14AFF1'>Reload: {{gun_reload}}s | DPM: {{gun_dpm_equip}}</font>\n<font color='#96CC29'>View: {{vision_radius}}m</font>",
    'detailed': "<font face='$FieldFont' size='16' color='#FFFFFF'><b><font color='#FFA500'>{{vehicle_name}}</font> ({{vehicle_type}} {{level}})</b></font>\n<font color='#14AFF1'>Reload: {{gun_reload}} sec | DPM: {{gun_dpm_equip}} | Aim: {{gun_aiming_time}}s</font>\n<font color='#96CC29'>View: {{vision_radius}}m | Camo: {{invis_stand}}/{{invis_move}}</font>\n<font color='#FF9999'>Armor: {{armor_hull_front}}/{{armor_hull_side}}/{{armor_hull_back}} | Turret: {{armor_turret_front}}/{{armor_turret_side}}/{{armor_turret_back}}</font>\n<font color='#FFCC00'>Speed: {{speed_forward}}km/h | HP: {{vehicle_max_health}} | Power: {{engine_power_density}}hp/t</font>\n<font color='#CCCCCC'>Shell: {{shell_name_1}} {{shell_damage_1}}dmg | Pen: {{shell_power_1}}mm</font>",
    'full': "<font face='$FieldFont' size='16' color='#FFFFFF'><font color='#FF557F'><tab>Tank: {{vehicle_name}}</font>\n<tab>Reload: <font color='#17EB17'>{{gun_reload_equip}}sec.</font>\n<img src='img://gui/maps/icons/vehicle/{{icon_system_name}}.png'>\n<textformat tabstops='[65]'>Weight: <font color='#FF3C38'>{{vehicle_weight}} ton.</font><tab>View: <font color='#002AFF'>{{vision_radius}} mt.</font></textformat>\n<textformat tabstops='[65,105,145]'>Cassis:<tab>{{armor_hull_front}}<tab>{{armor_hull_side}}<tab>{{armor_hull_back}}</textformat>\n<textformat tabstops='[65,105,145]'>Torret:<tab>{{armor_turret_front}}<tab>{{armor_turret_side}}<tab>{{armor_turret_back}}</textformat>\n<textformat tabstops='[65,105,145]'>Shell Type:<tab><font color='#FF7F00'>{{shell_type_1}}</font><tab><font color='#FFD400'>{{shell_type_2}}</font><tab><font color='#FFAA55'>{{shell_type_3}}</font></textformat>\n<textformat tabstops='[65,105,145]'>Piercing:<tab>{{shell_power_1}}<tab>{{shell_power_2}}<tab>{{shell_power_3}}</textformat>\n<textformat tabstops='[65,105,145]'>Av. Dmg:<tab>{{shell_damage_1}}<tab>{{shell_damage_2}}<tab>{{shell_damage_3}}</textformat></font>",
    'kmp': "<font face='$FieldFont' size='16' color='#FFFFFF'><b>{{vehicle_name}}\n~{{gun_reload_equip}} sec. | {{shell_power_1}} / {{shell_damage_1}}\nView: {{vision_radius}} mt.\n<font color='{{compareColor({{vehicle_weight}}, {{pl_vehicle_weight}})}}'>{{vehicle_weight}} ton. {{compareDelim({{vehicle_weight}}, {{pl_vehicle_weight}})}} {{pl_vehicle_weight}} ton.</font></font>",
    'ndo': "<font face='$FieldFont' size='16' color='#FFFFFF'><textformat tabstops='[5,150,214]'><font size='0'>.</font><tab><font color='#FF9900'>{{vehicle_name}}</font>\nReload:  {{gun_reload_equip}} sec</textformat></b><textformat tabstops='[5,54,150,214,246,279]'><font size='0'>.</font><tab>\nView:  {{vision_radius}} mt\nShell Type:  {{shell_type_1}}  {{shell_type_2}}  {{shell_type_3}}</textformat></b><textformat tabstops='[5,54,80,105,150,214,246,279]'><font size='0'>.</font>\nTorret:  {{armor_turret_front}}  {{armor_turret_side}}  {{armor_turret_back}}\nAv. Damage:  {{shell_damage_1}}  {{shell_damage_2}}  {{shell_damage_3}}</textformat></b><textformat tabstops='[5,54,80,105,150,214,246,279]'><font size='0'>.</font>\nChassis:  {{armor_hull_front}}  {{armor_hull_side}}  {{armor_hull_back}}\nPiercing:  {{shell_power_1}}  {{shell_power_2}}  {{shell_power_3}}</textformat></font>",
    'driftkings': "<font face='$FieldFont' size='16' color='#FFFFFF'><b><font color='#FFA500'>{{vehicle_name}}</font> ({{vehicle_type}} {{level}})</b></font>\n<font color='#14AFF1'>Reload: {{gun_reload}} sec | DPM: {{gun_dpm_equip}}</font>\n<font color='#96CC29'>View: {{vision_radius}}m | Camo: {{invis_stand}}</font>\n<font color='#FF9999'>Armor: {{armor_hull_front}}/{{armor_hull_side}}/{{armor_hull_back}} | HP: {{vehicle_max_health}}</font>\n<font color='#FFCC00'>Speed: {{speed_forward}}km/h | Power: {{engine_power_density}}hp/t | Turn: {{chassis_rotation_speed}}°/s</font>\n<font color='#CCCCCC'>Shell: {{shell_name_1}} {{shell_damage_1}}dmg | Pen: {{shell_power_1}}mm</font>"
}
TEMPLATE_INDEX_TO_KEY = {0: 'default', 1: 'minimal', 2: 'detailed', 3: 'full', 4: 'kmp', 5: 'ndo', 6: 'driftkings'}


class ConfigInterface(DriftkingsConfigInterface):

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.9.0 (%(file_compile_date)s)'
        self.author = 'orig. Kotyarko_O, adapted by: _DKRuben_EU'
        self.defaultKeys = {'altKey': [Keys.KEY_LALT]}
        self.data = {
            'enabled': True,
            'aliveOnly': False,
            'altKey': self.defaultKeys['altKey'],
            'compareValues': {
                'equal': {'color': '#FFFFFF', 'delim': '='},
                'lessThan': {'color': '#00FF00', 'delim': '&lt;'},
                'moreThan': {'color': '#FF0000', 'delim': '&gt;'}
            },
            'delay': 5,
            'templatePreset': 0,
            'showFor': 0,
            'textLock': False,
            'textPosition': {'x': 700.0, 'y': 300.0, 'alignX': 'center', 'alignY': 'center'},
            'textShadow': {'alpha': 0.8, 'angle': 90, 'blurX': 5, 'blurY': 5, 'color': '#000000', 'distance': 1, 'quality': 2, 'strength': 2},
            'backgroundEnabled': True,
            'backgroundAlpha': 0.7,
            'version': calculate_version(self.version)
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_textLock_text': 'Disable text mouse dragging',
            'UI_setting_textLock_tooltip': 'This setting controls whether you are able to move text window with a mouse or not.',
            'UI_setting_showFor_text': 'Show For',
            'UI_setting_showFor_tooltip': '• <b>Ally</b> - Just show to \'ALLY\' players tanks.\n• <b>Enemy</b> - Just show to \'ENEMY\' players tanks.\n• <b>All</b> - Show to \'ALL\' players tanks.',
            'UI_showFor_ally': 'Ally',
            'UI_showFor_enemy': 'Enemy',
            'UI_showFor_all': 'All',
            'UI_setting_aliveOnly_text': 'Alive Only',
            'UI_setting_aliveOnly_tooltip': 'Show only for alive players.',
            'UI_setting_altKey_text': 'Alt. Key',
            'UI_setting_altKey_tooltip': 'Key for self vehicle information display.',
            'UI_setting_delay_text': 'Delay',
            'UI_setting_delay_tooltip': 'Hide panel delay (in seconds)',
            'UI_delay_format': ' sec.',
            'UI_setting_backgroundEnabled_text': 'Enable Background',
            'UI_setting_backgroundEnabled_tooltip': 'Show a background behind the text',
            'UI_setting_backgroundAlpha_text': 'Background Opacity',
            'UI_setting_backgroundAlpha_tooltip': 'Opacity of the background panel (0-1)',
            'UI_setting_templatePreset_text': 'Template Preset',
            'UI_setting_templatePreset_tooltip': 'Choose a predefined template for the information display',
            'UI_templatePreset_default': 'Default',
            'UI_templatePreset_minimal': 'Minimal',
            'UI_templatePreset_detailed': 'Detailed',
            'UI_templatePreset_full': 'Full',
            'UI_templatePreset_kmp': 'KMP',
            'UI_templatePreset_ndo': 'NDO',
            'UI_templatePreset_driftkings': 'Driftkings',
            'armor_piercing': 'AP',
            'high_explosive': 'HE',
            'armor_piercing_cr': 'APCR',
            'armor_piercing_he': 'HESH',
            'hollow_charge': 'HEAT'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        xFormat = self.i18n['UI_delay_format']
        showForOptions = ['all', 'ally', 'enemy']
        showForLabels = [self.i18n['UI_showFor_' + x] for x in showForOptions]
        templateOptions = ['default', 'minimal', 'detailed', 'full', 'kmp', 'ndo', 'driftkings']
        templateLabels = [self.i18n['UI_templatePreset_' + x] for x in templateOptions]
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('textLock'),
                self.tb.createSlider('delay', 1.0, 10, 1.0, '{{value}}%s' % xFormat),
                self.tb.createControl('aliveOnly'),
                self.tb.createHotKey('altKey'),
                self.tb.createOptions('showFor', showForLabels)
            ],
            'column2': [
                self.tb.createControl('backgroundEnabled'),
                self.tb.createSlider('backgroundAlpha', 0.1, 1.0, 0.1, '{{value}}'),
                self.tb.createOptions('templatePreset', templateLabels)
            ]
        }

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)


class Flash(object):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self):
        self.name = {}
        self.data = {}

    def startBattle(self):
        if not config.data['enabled']:
            return
        self.data = self.setup()
        COMPONENT_EVENT.UPDATED += self.__updatePosition
        if g_guiFlash is not None and COMPONENT_TYPE is not None:
            self.createObject(COMPONENT_TYPE.LABEL, self.data[COMPONENT_TYPE.LABEL])
            self.updateObject(COMPONENT_TYPE.LABEL, {'background': config.data['backgroundEnabled']})
            self.updateObject(COMPONENT_TYPE.LABEL, {'alpha': config.data['backgroundAlpha']})
        g_guiResetters.add(self.screenResize)

    def stopBattle(self):
        if not config.data['enabled']:
            return
        g_guiResetters.remove(self.screenResize)
        if COMPONENT_EVENT is not None:
            COMPONENT_EVENT.UPDATED -= self.__updatePosition
        if g_guiFlash is not None and COMPONENT_TYPE is not None:
            self.deleteObject(COMPONENT_TYPE.LABEL)

    def deleteObject(self, name):
        g_guiFlash.deleteComponent(self.name[name])

    def createObject(self, name, data):
        g_guiFlash.createComponent(self.name[name], name, data)

    def updateObject(self, name, data):
        g_guiFlash.updateComponent(self.name[name], data)

    def __updatePosition(self, alias, props):
        if str(alias) == str(config.ID):
            x = props.get('x', config.data['textPosition']['x'])
            if x is not None and x != config.data['textPosition']['x']:
                config.data['textPosition']['x'] = x
                self.data[COMPONENT_TYPE.LABEL]['x'] = x
            y = props.get('y', config.data['textPosition']['y'])
            if y is not None and y != config.data['textPosition']['y']:
                config.data['textPosition']['y'] = y
                self.data[COMPONENT_TYPE.LABEL]['y'] = y
            config.onApplySettings({'textPosition': {'x': x, 'y': y}})

    def setup(self):
        self.name = {COMPONENT_TYPE.LABEL: '%s' % config.ID}
        self.data = {
            COMPONENT_TYPE.LABEL: {
                'x': 0,
                'y': 0,
                'drag': not config.data['textLock'],
                'border': not config.data['textLock'],
                'alignX': 'center',
                'alignY': 'center',
                'visible': True,
                'text': '',
                'shadow': {
                    'distance': config.data['textShadow']['distance'],
                    'angle': config.data['textShadow']['angle'],
                    'color': config.data['textShadow']['color'],
                    'alpha': config.data['textShadow']['alpha'],
                    'blurX': config.data['textShadow']['blurX'],
                    'blurY': config.data['textShadow']['blurY'],
                    'strength': config.data['textShadow']['strength'],
                    'quality': config.data['textShadow']['quality']
                }
            }
        }
        for key, value in config.data['textPosition'].items():
            if key in self.data[COMPONENT_TYPE.LABEL]:
                self.data[COMPONENT_TYPE.LABEL][key] = value
        return self.data

    def addText(self, text=''):
        self.updateObject(COMPONENT_TYPE.LABEL, {'text': text})

    def setVisible(self, status):
        data = {'visible': status}
        self.updateObject(COMPONENT_TYPE.LABEL, data)

    @staticmethod
    def screenFix(screen, value, align=1):
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
        curScr = GUI.screenResolution()
        scale = float(self.settingsCore.interfaceScale.get())
        xMo, yMo = curScr[0] / scale, curScr[1] / scale
        x = config.data['textPosition'].get('x', None)
        if config.data['textPosition']['alignX'] == COMPONENT_ALIGN.LEFT:
            x = self.screenFix(xMo, config.data['textPosition']['x'], 1)
        elif config.data['textPosition']['alignX'] == COMPONENT_ALIGN.RIGHT:
            x = self.screenFix(xMo, config.data['textPosition']['x'], -1)
        elif config.data['textPosition']['alignX'] == COMPONENT_ALIGN.CENTER:
            x = self.screenFix(xMo, config.data['textPosition']['x'], 0)
        if x is not None and x != config.data['textPosition']['x']:
            config.data['textPosition']['x'] = x
            self.data[COMPONENT_TYPE.LABEL]['x'] = x
        y = config.data['textPosition'].get('y', None)
        if config.data['textPosition']['alignY'] == COMPONENT_ALIGN.TOP:
            y = self.screenFix(yMo, config.data['textPosition']['y'], 1)
        elif config.data['textPosition']['alignY'] == COMPONENT_ALIGN.BOTTOM:
            y = self.screenFix(yMo, config.data['textPosition']['y'], -1)
        elif config.data['textPosition']['alignY'] == COMPONENT_ALIGN.CENTER:
            y = self.screenFix(yMo, config.data['textPosition']['y'], 0)
        if y is not None and y != config.data['textPosition']['y']:
            config.data['textPosition']['y'] = y
            self.data[COMPONENT_TYPE.LABEL]['y'] = y
        self.updateObject(COMPONENT_TYPE.LABEL, {'x': x, 'y': y})

    def getData(self):
        return self.data

    def getNames(self):
        return self.name


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)
g_flash = Flash()


class DataConstants(object):
    __slots__ = ('_playerVehicle', '_vehicle', '_typeDescriptor', '_gunShots', '_macroHandlers', '_cachedResults',)

    def __init__(self):
        self._playerVehicle = None
        self._vehicle = None
        self._typeDescriptor = None
        self._gunShots = None
        self._cachedResults = {}
        self._macroHandlers = self._buildMacroHandlers()

    def init(self, vehicle, playerVehicle=None):
        if not vehicle and not playerVehicle:
            return
        self._playerVehicle = playerVehicle
        self._vehicle = vehicle
        self._typeDescriptor = vehicle.typeDescriptor if vehicle is not None else self._playerVehicle.typeDescriptor
        self._gunShots = self._typeDescriptor.gun.shots if self._typeDescriptor else None
        self._cachedResults = {}

    def reset(self):
        self._playerVehicle = None
        self._vehicle = None
        self._typeDescriptor = None
        self._gunShots = None
        self._cachedResults = {}

    @staticmethod
    def l10n(text):
        if text is None:
            return None
        if text in config.i18n:
            text = config.i18n[text]
            if text is None:
                return None
        while True:
            localizedMacroStart = text.find('{{l10n:')
            if localizedMacroStart == -1:
                break
            localizedMacroEnd = text.find('}}', localizedMacroStart)
            if localizedMacroEnd == -1:
                break
            macro = text[localizedMacroStart + 7:localizedMacroEnd]
            parts = macro.split(':')
            macro = config.i18n.get(parts[0], parts[0])
            parts = parts[1:]
            if parts:
                try:
                    macro = macro.format(*parts)
                except StandardError:
                    print('macro:  {}'.format(macro))
                    print('params: {}'.format(parts))
                    traceback.print_exc()
            text = text[:localizedMacroStart] + macro + text[localizedMacroEnd + 2:]
        return config.i18n.get(text, text)

    def _buildMacroHandlers(self):
        handlers = {
            'nick_name': lambda: self._vehicle.publicInfo.name if self._vehicle else None,
            'marks_on_gun': lambda: self._vehicle.publicInfo.marksOnGun if self._vehicle else None,
            'vehicle_type': self._get_vehicle_type,
            'vehicle_name': lambda: self._typeDescriptor.type.userString if self._typeDescriptor else None,
            'vehicle_system_name': lambda: self._typeDescriptor.name if self._typeDescriptor else None,
            'icon_system_name': lambda: self._typeDescriptor.name.replace(':', '-') if self._typeDescriptor else None,
            'gun_name': lambda: self._typeDescriptor.gun.shortUserString if self._typeDescriptor else None,
            'max_ammo': lambda: self._typeDescriptor.gun.maxAmmo if self._typeDescriptor else None,
            'gun_reload': lambda: '%.2f' % self._typeDescriptor.gun.reloadTime if self._typeDescriptor else None,
            'gun_reload_with_crew': lambda: '%.2f' % round(self._typeDescriptor.gun.reloadTime * self._typeDescriptor.miscAttrs.get('gunReloadTimeFactor', 1) / 1.0695 + 0.0043 * self._typeDescriptor.miscAttrs.get('crewLevelIncrease', 0), 1) if self._typeDescriptor else None,
            'gun_dpm': self._get_gun_dpm,
            'gun_reload_equip': self._get_gun_reload_equip,
            'gun_dpm_equip': self._get_gun_dpm_equip,
            'gun_clip': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.gun.clip[0],
            'gun_clip_reload': lambda: None if not self._typeDescriptor else '%.1f' % self._typeDescriptor.gun.clip[1],
            'gun_burst': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.gun.burst[0],
            'gun_burst_reload': lambda: None if not self._typeDescriptor else '%.1f' % self._typeDescriptor.gun.burst[1],
            'gun_aiming_time': lambda: None if not self._typeDescriptor else '%.1f' % self._typeDescriptor.gun.aimingTime,
            'gun_accuracy': lambda: None if not self._typeDescriptor else '%.2f' % round(self._typeDescriptor.gun.shotDispersionAngle * 100, 2),
            'angle_pitch_up': lambda: None if not self._typeDescriptor else '%d' % degrees(-self._typeDescriptor.gun.pitchLimits['absolute'][0]),
            'angle_pitch_down': lambda: None if not self._typeDescriptor else '%d' % degrees(-self._typeDescriptor.gun.pitchLimits['absolute'][1]),
            'angle_pitch_left': lambda: None if not self._typeDescriptor or not self._typeDescriptor.gun.turretYawLimits else '%d' % degrees(-self._typeDescriptor.gun.turretYawLimits[0]),
            'angle_pitch_right': lambda: None if not self._typeDescriptor or not self._typeDescriptor.gun.turretYawLimits else '%d' % degrees(self._typeDescriptor.gun.turretYawLimits[1]),
            'vehicle_max_health': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.maxHealth,
            'armor_hull_front': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.hull.primaryArmor[0],
            'armor_hull_side': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.hull.primaryArmor[1],
            'armor_hull_back': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.hull.primaryArmor[2],
            'turret_name': lambda: None if not self._typeDescriptor else '%s' % self._typeDescriptor.turret.shortUserString,
            'armor_turret_front': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.turret.primaryArmor[0],
            'armor_turret_side': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.turret.primaryArmor[1],
            'armor_turret_back': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.turret.primaryArmor[2],
            'vehicle_weight': lambda: '%.1f' % round(self._typeDescriptor.physics['weight'] / 1000, 1) if self._typeDescriptor else None,
            'chassis_max_weight': lambda: None if not self._typeDescriptor else '%.1f' % round(self._typeDescriptor.chassis.maxLoad / 1000, 1),
            'engine_name': lambda: None if not self._typeDescriptor else '%s' % self._typeDescriptor.engine.shortUserString,
            'engine_power': lambda: None if not self._typeDescriptor else '%d' % round(self._typeDescriptor.engine.power / 735.49875, 0),
            'engine_power_density': self._get_engine_power_density,
            'speed_forward': lambda: None if not self._typeDescriptor else '%d' % (self._typeDescriptor.physics['speedLimits'][0] * 3.6),
            'speed_backward': lambda: None if not self._typeDescriptor else '%d' % (self._typeDescriptor.physics['speedLimits'][1] * 3.6),
            'hull_speed_turn': lambda: None if not self._typeDescriptor else '%.2f' % degrees(self._typeDescriptor.chassis.rotationSpeed),
            'turret_speed_turn': lambda: None if not self._typeDescriptor else '%.2f' % degrees(self._typeDescriptor.turret.rotationSpeed),
            'chassis_rotation_speed': lambda: None if not self._typeDescriptor else '%d' % degrees(self._typeDescriptor.chassis.rotationSpeed),
            'invis_stand': lambda: None if not self._typeDescriptor else '%.1f' % (self._typeDescriptor.type.invisibility[1] * 57),
            'invis_stand_shot': lambda: None if not self._typeDescriptor else '%.2f' % (self._typeDescriptor.type.invisibility[1] * self._typeDescriptor.gun.invisibilityFactorAtShot * 57),
            'invis_move': lambda: None if not self._typeDescriptor else '%.1f' % (self._typeDescriptor.type.invisibility[0] * 57),
            'invis_move_shot': lambda: None if not self._typeDescriptor else '%.2f' % (self._typeDescriptor.type.invisibility[0] * self._typeDescriptor.gun.invisibilityFactorAtShot * 57),
            'vision_radius': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.turret.circularVisionRadius,
            'radio_name': lambda: None if not self._typeDescriptor else '%s' % self._typeDescriptor.radio.shortUserString,
            'radio_radius': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.radio.distance,
            'nation': lambda: None if not self._typeDescriptor else NAMES[self._typeDescriptor.type.customizationNationID],
            'level': lambda: None if not self._typeDescriptor else '%d' % self._typeDescriptor.type.level,
            'rlevel': self._get_roman_level,
            'pl_vehicle_weight': self._get_pl_vehicle_weight,
            'pl_gun_reload': self._get_pl_gun_reload,
            'pl_gun_reload_equip': self._get_pl_gun_reload_equip,
            'pl_gun_dpm': self._get_pl_gun_dpm,
            'pl_gun_dpm_equip': self._get_pl_gun_dpm_equip,
            'pl_vision_radius': self._get_pl_vision_radius,
            'pl_gun_aiming_time': self._get_pl_gun_aiming_time,
        }
        handlers.update(self._generateShellHandlers())
        handlers.update({'stun_radius': self._get_stun_radius, 'stun_duration_min': self._get_stun_duration_min, 'stun_duration_max': self._get_stun_duration_max, })
        return handlers

    def _generateShellHandlers(self):
        handlers = {}
        handlers.update({
            'shell_name_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%s" % self._gunShots[0].shell.userString,
            'shell_name_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%s" % self._gunShots[1].shell.userString,
            'shell_name_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%s" % self._gunShots[2].shell.userString,
            'shell_damage_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 1) else "%d" % (self._gunShots[0].shell.armorDamage[0] if hasattr(self._gunShots[0].shell, 'armorDamage') else self._gunShots[0].shell.damage[0]),
            'shell_damage_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 2) else "%d" % (self._gunShots[1].shell.armorDamage[0] if hasattr(self._gunShots[1].shell, 'armorDamage') else self._gunShots[1].shell.damage[0]),
            'shell_damage_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % (self._gunShots[2].shell.armorDamage[0] if hasattr(self._gunShots[2].shell, 'armorDamage') else self._gunShots[2].shell.damage[0]),
            'shell_power_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 1) else "%d" % (self._gunShots[0].piercingPower[0]),
            'shell_power_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 2) else "%d" % (self._gunShots[1].piercingPower[0]),
            'shell_power_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % (self._gunShots[2].piercingPower[0]),
            'shell_type_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 1) else self.l10n(self._gunShots[0].shell.kind.lower()),
            'shell_type_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 2) else self.l10n(self._gunShots[1].shell.kind.lower()),
            'shell_type_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else self.l10n(self._gunShots[2].shell.kind.lower()),
            'shell_speed_1': lambda : None if (not self._gunShots) or (len(self._gunShots) < 1) else "%d" % round(self._gunShots[0].speed * 1.25),
            'shell_speed_2': lambda : None if (not self._gunShots) or (len(self._gunShots) < 2) else "%d" % round(self._gunShots[1].speed * 1.25),
            'shell_speed_3': lambda : None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % round(self._gunShots[2].speed * 1.25),
            'shell_distance_1': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % self._gunShots[0].maxDistance,
            'shell_distance_2': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % self._gunShots[1].maxDistance,
            'shell_distance_3': lambda: None if (not self._gunShots) or (len(self._gunShots) < 3) else "%d" % self._gunShots[2].maxDistance
        })
        return handlers

    def _get_vehicle_type(self):
        if 'vehicle_type' in self._cachedResults:
            return self._cachedResults['vehicle_type']
        if self._typeDescriptor:
            tags = self._typeDescriptor.type.tags
            result = None
            if 'lightTank' in tags:
                result = 'LT'
            elif 'mediumTank' in tags:
                result = 'MT'
            elif 'heavyTank' in tags:
                result = 'HT'
            elif 'AT-SPG' in tags:
                result = 'TD'
            elif 'SPG' in tags:
                result = 'SPG'
            self._cachedResults['vehicle_type'] = result
            return result
        return None

    def _get_gun_dpm(self):
        if 'gun_dpm' in self._cachedResults:
            return self._cachedResults['gun_dpm']
        if not self._typeDescriptor:
            return None
        time = self._typeDescriptor.gun.reloadTime + (self._typeDescriptor.gun.clip[0] - 1) * self._typeDescriptor.gun.clip[1]
        shell = self._typeDescriptor.gun.shots[0].shell
        damage = shell.armorDamage if hasattr(shell, 'armorDamage') else shell.damage
        result = '%d' % round(self._typeDescriptor.gun.clip[0] / time * 60 * damage[0], 0)
        self._cachedResults['gun_dpm'] = result
        return result

    def _get_gun_reload_equip(self, eq1=1, eq2=1, eq3=1, eq4=1):
        cache_key = 'gun_reload_equip_%s_%s_%s_%s' % (eq1, eq2, eq3, eq4)
        if cache_key in self._cachedResults:
            return self._cachedResults[cache_key]
        if not self._typeDescriptor:
            return None
        reload_orig = self._typeDescriptor.gun.reloadTime
        rammer = 0.9 if self._typeDescriptor.gun.clip[0] == 1 and eq1 == 1 else 1
        if eq2 == 1 and eq3 == 1 and eq4 == 1:
            crew = 1.32
        elif eq2 == 1 and eq3 == 1 and eq4 == 0:
            crew = 1.27
        elif eq2 == 1 and eq3 == 0 and eq4 == 1:
            crew = 1.21
        elif eq2 == 1 and eq3 == 0 and eq4 == 0:
            crew = 1.16
        elif eq2 == 0 and eq3 == 1 and eq4 == 1:
            crew = 1.27
        elif eq2 == 0 and eq3 == 1 and eq4 == 0:
            crew = 1.21
        elif eq2 == 0 and eq3 == 0 and eq4 == 1:
            crew = 1.16
        else:
            crew = 1.1
        result = '%.2f' % round(reload_orig / (0.57 + 0.43 * crew) * rammer, 2)
        self._cachedResults[cache_key] = result
        return result

    def _get_gun_dpm_equip(self, eq1=1, eq2=1, eq3=1, eq4=1):
        cache_key = 'gun_dpm_equip_%s_%s_%s_%s' % (eq1, eq2, eq3, eq4)
        if cache_key in self._cachedResults:
            return self._cachedResults[cache_key]
        if not self._typeDescriptor:
            return None
        reloadEquip = float(self._get_gun_reload_equip(eq1, eq2, eq3, eq4))
        time = reloadEquip + (self._typeDescriptor.gun.clip[0] - 1) * self._typeDescriptor.gun.clip[1]
        shell = self._typeDescriptor.gun.shots[0].shell
        damage = shell.armorDamage if hasattr(shell, 'armorDamage') else shell.damage
        result = '%d' % round(self._typeDescriptor.gun.clip[0] / time * 60 * damage[0], 0)
        self._cachedResults[cache_key] = result
        return result

    def _get_engine_power_density(self):
        if 'engine_power_density' in self._cachedResults:
            return self._cachedResults['engine_power_density']
        if not self._typeDescriptor:
            return None
        power = self._typeDescriptor.engine.power / 735.49875
        weight = self._typeDescriptor.physics['weight'] / 1000
        result = '%.2f' % round(power / weight, 2)
        self._cachedResults['engine_power_density'] = result
        return result

    def _get_roman_level(self):
        if 'roman_level' in self._cachedResults:
            return self._cachedResults['roman_level']
        if not self._typeDescriptor:
            return None
        level_idx = self._typeDescriptor.type.level - 1
        if 0 <= level_idx < len(ROMAN_LEVELS):
            result = ROMAN_LEVELS[level_idx]
            self._cachedResults['roman_level'] = result
            return result
        return None

    def _get_stun_radius(self):
        if 'stun_radius' in self._cachedResults:
            return self._cachedResults['stun_radius']
        if self._gunShots is not None and len(self._gunShots) > 0 and hasattr(self._gunShots[0].shell, 'stun') and self._gunShots[0].shell.stun is not None:
            result = '%d' % self._gunShots[0].shell.stun.stunRadius
            self._cachedResults['stun_radius'] = result
            return result
        return None

    def _get_stun_duration_min(self):
        if 'stun_duration_min' in self._cachedResults:
            return self._cachedResults['stun_duration_min']
        if self._gunShots is not None and len(self._gunShots) > 0 and hasattr(self._gunShots[0].shell, 'stun') and self._gunShots[0].shell.stun is not None:
            time = round(self._gunShots[0].shell.stun.stunRadius * self._gunShots[0].shell.stun.guaranteedStunDuration, 1)
            result = '%.1f' % time
            self._cachedResults['stun_duration_min'] = result
            return result
        return None

    def _get_stun_duration_max(self):
        if 'stun_duration_max' in self._cachedResults:
            return self._cachedResults['stun_duration_max']
        if self._gunShots is not None and len(self._gunShots) > 0 and hasattr(self._gunShots[0].shell, 'stun') and self._gunShots[0].shell.stun is not None:
            result = '%d' % self._gunShots[0].shell.stun.stunDuration
            self._cachedResults['stun_duration_max'] = result
            return result
        return None

    def _get_pl_vehicle_weight(self):
        if not self._playerVehicle:
            return None
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        result = '%.1f' % round(self._typeDescriptor.physics['weight'] / 1000, 1) if self._typeDescriptor else None
        return result

    def _get_pl_gun_reload(self):
        if not self._playerVehicle:
            return None
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return '%.2f' % self._typeDescriptor.gun.reloadTime if self._typeDescriptor else None

    def _get_pl_gun_reload_equip(self):
        if not self._playerVehicle:
            return None
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self._get_gun_reload_equip()

    def _get_pl_gun_dpm(self):
        if not self._playerVehicle:
            return None
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self._get_gun_dpm()

    def _get_pl_gun_dpm_equip(self):
        if not self._playerVehicle:
            return None
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self._get_gun_dpm_equip()

    def _get_pl_vision_radius(self):
        if not self._playerVehicle:
            return None
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return '%d' % self._typeDescriptor.turret.circularVisionRadius if self._typeDescriptor else None

    def _get_pl_gun_aiming_time(self):
        if not self._playerVehicle:
            return None
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return '%.1f' % self._typeDescriptor.gun.aimingTime if self._typeDescriptor else None

    def __getattr__(self, name):
        if name in self._macroHandlers:
            return self._macroHandlers[name]
        raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))


class CompareMacros(object):
    __slots__ = ('value1', 'value2')

    def __init__(self):
        self.value1 = None
        self.value2 = None

    def reset(self):
        self.value1 = None
        self.value2 = None

    def setData(self, value1, value2):
        self.value1 = float(value1)
        self.value2 = float(value2)

    @property
    def compareDelim(self):
        return self._getCompareAttribute('delim')

    @property
    def compareColor(self):
        return self._getCompareAttribute('color')

    def _getCompareAttribute(self, attribute):
        if self.value1 is None or self.value2 is None:
            raise ValueError('Values must be defined before comparison.')
        if self.value1 > self.value2:
            return config.data['compareValues']['moreThan'][attribute]
        elif self.value1 == self.value2:
            return config.data['compareValues']['equal'][attribute]
        else:
            return config.data['compareValues']['lessThan'][attribute]


class InfoPanel(DataConstants):
    def __init__(self):
        self.textFormats = self.getText() if config.data['enabled'] else None
        self.hotKeyDown = False
        self.visible = False
        self.timer = None
        DataConstants.__init__(self)

    def reset(self):
        DataConstants.reset(self)
        self.textFormats = self.getText() if config.data['enabled'] else None
        self.hotKeyDown = False
        self.visible = False
        self.timer = None

    @staticmethod
    def getText():
        template_index = config.data['templatePreset']
        template_key = TEMPLATE_INDEX_TO_KEY.get(template_index, 'default')
        return PRESET_TEMPLATES.get(template_key, PRESET_TEMPLATES['default'])

    @staticmethod
    def isConditions(entity):
        player = getPlayer()
        if entity is None or not hasattr(entity, 'publicInfo'):
            return False
        playerTeam = player.team
        team = getattr(entity.publicInfo, 'team', 0)
        isAlly = team > 0 and team == playerTeam
        if config.data['showFor'] == 0:
            showFor = True
        elif config.data['showFor'] == 1:
            showFor = isAlly
        elif config.data['showFor'] == 2:
            showFor = not isAlly
        else:
            showFor = False
        isAlive = entity.isAlive() if config.data['aliveOnly'] else True
        return showFor and isAlive

    def getFuncResponse(self, funcName):
        if not hasattr(self, funcName):
            return ''
        func = getattr(self, funcName, None)
        if callable(func):
            result = func()
            if result is not None:
                return str(result)
            return ''
        return ''

    def setTextsFormatted(self):
        if not config.data['enabled']:
            return ''
        textFormat = self.textFormats
        textFormat = self.replaceMacros(textFormat, self._macroHandlers.keys())
        textFormat = self.replaceCompareMacros(textFormat, COMPARE_MACROS)
        return textFormat

    def replaceMacros(self, textFormat, macros):
        for macro in macros:
            macroPattern = '{{' + macro + '}}'
            if macroPattern in textFormat:
                funcName = macro
                funcResponse = self.getFuncResponse(funcName)
                textFormat = textFormat.replace(macroPattern, funcResponse)
        return textFormat

    @staticmethod
    def replaceCompareMacros(textFormat, compareMacros):
        for macro in compareMacros:
            macroPattern = macro + '('
            if macroPattern in textFormat:
                startIndex = textFormat.find(macroPattern)
                endIndex = textFormat.find(')', startIndex + len(macroPattern)) + 1
                reader = textFormat[startIndex:endIndex]
                func = reader.split('(')[0]
                args = reader[reader.find('(') + 1:reader.find(')')].split(',')
                if len(args) == 2:
                    arg1, arg2 = args[0].strip(), args[1].strip()
                    g_comparator.setData(arg1, arg2)
                    funcRes = getattr(g_comparator, func)
                    textFormat = textFormat.replace('{{' + reader + '}}', str(funcRes))
        return textFormat

    def keyPressed(self, event):
        if not config.data['enabled']:
            return
        if checkKeys(config.data['altKey']) and event.isKeyDown():
            self.onUpdateVehicle(getPlayer().getVehicleAttached())
            self.hotKeyDown = True
        elif not checkKeys(config.data['altKey']) and event.isKeyDown():
            self.hotKeyDown = False
            target = getTarget()
            if self.isConditions(target):
                self.onUpdateVehicle(target)
            else:
                self.hide()

    def hide(self):
        if self.timer is not None and self.timer.isStarted():
            self.timer.stop()
            self.timer = None
            g_flash.setVisible(False)

    def onUpdateBlur(self):
        if self.hotKeyDown or getPlayer().getVehicleAttached() is None:
            return
        if self.timer is not None and self.timer.isStarted():
            self.timer.stop()
            self.timer = None
        self.timer = TimeInterval(config.data['delay'], self, 'hide')
        self.timer.start()

    def onUpdateVehicle(self, vehicle):
        player = getPlayer()
        if self.hotKeyDown:
            return
        playerVehicle = player.getVehicleAttached()
        if playerVehicle is not None and g_flash:
            g_flash.setVisible(True)
            if hasattr(vehicle, 'typeDescriptor'):
                self.init(vehicle, playerVehicle)
            elif hasattr(playerVehicle, 'typeDescriptor'):
                self.init(None, playerVehicle)
            g_flash.addText(self.setTextsFormatted())


g_comparator = CompareMacros()
g_mod = InfoPanel()


@override(PlayerAvatar, 'targetBlur')
def new__targetBlur(func, self, prevEntity):
    if config.data['enabled'] and g_mod.isConditions(prevEntity):
        g_mod.onUpdateBlur()
    func(self, prevEntity)


@override(PlayerAvatar, 'targetFocus')
def new_targetFocus(func, self, entity):
    func(self, entity)
    if not (config.data['enabled'] and g_mod.isConditions(entity)):
        return
    g_mod.onUpdateVehicle(entity)


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    InputHandler.g_instance.onKeyDown += g_mod.keyPressed
    g_flash.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    if not config.data['enabled']:
        return
    if not getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        return
    InputHandler.g_instance.onKeyDown -= g_mod.keyPressed
    g_mod.reset()
    g_flash.stopBattle()
