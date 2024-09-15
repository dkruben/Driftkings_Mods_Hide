# -*- coding: utf-8 -*-
import traceback
from functools import partial
from math import degrees

import Keys
from Avatar import PlayerAvatar
from constants import ARENA_BONUS_TYPE
from gui.shared.utils.TimeInterval import TimeInterval
from messenger import MessengerEntry
from nations import NAMES

from DriftkingsCore import SimpleConfigInterface, Analytics, getPlayer, getTarget, override, checkKeys, logError, callback, cancelCallback, calculate_version

MACROS = [
    '{{nick_name}}', '{{marks_on_gun}}', '{{vehicle_type}}', '{{vehicle_name}}', '{{vehicle_system_name}}', '{{icon_system_name}}', '{{gun_name}}', '{{gun_caliber}}',
    '{{max_ammo}}', '{{gun_reload}}', '{{gun_dpm}}', '{{gun_reload_equip}}', '{{gun_dpm_equip}}', '{{gun_clip}}', '{{gun_clip_reload}}',
    '{{gun_burst}}', '{{gun_burst_reload}}', '{{gun_aiming_time}}', '{{gun_accuracy}}',
    '{{shell_name_1}}', '{{shell_name_2}}', '{{shell_name_3}}',
    '{{shell_damage_1}}', '{{shell_damage_2}}', '{{shell_damage_3}}', '{{shell_power_1}}', '{{shell_power_2}}', '{{shell_power_3}}', '{{shell_type_1}}',
    '{{shell_type_2}}', '{{shell_type_3}}', '{{shell_speed_1}}', '{{shell_speed_2}}', '{{shell_speed_3}}', '{{shell_distance_1}}', '{{shell_distance_2}}',
    '{{shell_distance_3}}', '{{angle_pitch_up}}', '{{angle_pitch_down}}', '{{angle_pitch_left}}', '{{angle_pitch_right}}', '{{vehicle_max_health}}',
    '{{armor_hull_front}}', '{{armor_hull_side}}', '{{armor_hull_back}}', '{{turret_name}}', '{{armor_turret_front}}', '{{armor_turret_side}}',
    '{{armor_turret_back}}', '{{vehicle_weight}}', '{{chassis_max_weight}}', '{{engine_name}}', '{{engine_power}}', '{{engine_power_density}}',
    '{{speed_forward}}', '{{speed_backward}}', '{{hull_speed_turn}}', '{{turret_speed_turn}}', '{{invis_stand}}', '{{invis_stand_shot}}', '{{invis_move}}',
    '{{invis_move_shot}}', '{{vision_radius}}', '{{radio_name}}', '{{radio_radius}}',
    '{{nation}}', '{{level}}', '{{rlevel}}',
    '{{pl_vehicle_weight}}', '{{pl_gun_reload}}', '{{pl_gun_reload_equip}}', '{{pl_gun_dpm}}', '{{pl_gun_dpm_equip}}', '{{pl_vision_radius}}', '{{pl_gun_aiming_time}}'
]

COMPARE_MACROS = ['compareDelim', 'compareColor']


class ConfigInterface(SimpleConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.4.5 %(file_compile_date)s'
        self.author = 'orig. Kotyarko_O'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.defaultKeys = {'altKey': [Keys.KEY_LALT]}
        self.data = {
            'enabled': True,
            'showFor': 0,
            'aliveOnly': False,
            'textLock': False,
            'delay': 5,
            'altKey': self.defaultKeys['altKey'],
            'compareValues': {'moreThan': {'delim': '&gt;', 'color': '#FF0000'}, 'equal': {'delim': '=', 'color': '#FFFFFF'}, 'lessThan': {'delim': '&lt;', 'color': '#00FF00'}},
            'format': '<font color=\'#F0F0F0\'><b>{{vehicle_name}}</b></font><br><textformat tabstops=\'[80]\'><font color=\'#14AFF1\'>{{gun_reload_equip}} sec.</font><tab><font color=\'#96CC29\'>{{vision_radius}} mt.</font></textformat>',
            # flash
            'textPosition': {'x': 40.0, 'y': 5.0},
            'textShadow': {'enabled': True, 'distance': 0, 'angle': 90, 'color': '#000000', 'alpha': 0.8, 'blurX': 2, 'blurY': 2, 'strength': 2, 'quality': 2},
            'textStyle': {'size': 14, 'font': '$TitleFont', 'align': 'left'}
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_textLock_text': 'Disable text mouse dragging',
            'UI_setting_textLock_tooltip': 'This setting controls whether you are able to move text window with a mouse or not.',
            'UI_setting_showFor_text': 'Show For',
            'UI_setting_showFor_tooltip': ' • <b>Ally</b> - Just show to \'ALLY\' players tanks.\n • <b>Enemy</b> - Just show to \'ENEMY\' players tanks.\n • <b>All</b> - Show to \'ALL\' players tanks.',
            'UI_showFor_ally': 'Ally',
            'UI_showFor_enemy': 'Enemy',
            'UI_showFor_all': 'All',
            'UI_setting_aliveOnly_text': 'Alive Only',
            'UI_setting_aliveOnly_tooltip': 'Show only for alive players.',
            'UI_setting_altKey_text': 'Alt. Key',
            'UI_setting_altKey_tooltip': 'Key for self vehicle information display.',
            'UI_setting_delay_text': 'Delay',
            'UI_setting_delay_tooltip': 'Hide panel delay (in seconds)',
            'UI_delay_format': ' sec.'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        xFormat = self.i18n['UI_delay_format']
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('textLock'),
                self.tb.createSlider('delay', 1.0, 10, 1.0, '{{value}}%s' % xFormat),
                self.tb.createControl('aliveOnly'),
                self.tb.createHotKey('altKey'),
                self.tb.createOptions('showFor', [self.i18n['UI_showFor_' + x] for x in ('all', 'ally', 'enemy')])
            ],
            'column2': []
        }

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)
        if g_flash is not None:
            g_flash.onApplySettings()


class Flash(object):
    def __init__(self, ID):
        self.ID = ID
        self.texts = []
        self.callbacks = []
        self.isTextAdding = False
        self.isTextRemoving = False
        self.setup()
        COMPONENT_EVENT.UPDATED += self.__updatePosition

    def __updatePosition(self, alias, data):
        if alias != self.ID:
            return
        config.onApplySettings({'textPosition': data})

    def onApplySettings(self):
        g_guiFlash.updateComponent(self.ID, dict(config.data['textPosition'], drag=not config.data['textLock'], border=not config.data['textLock']))

    def setup(self):
        self.texts = []
        g_guiFlash.createComponent(self.ID, COMPONENT_TYPE.PANEL, dict(config.data['textPosition'], drag=not config.data['textLock'], border=not config.data['textLock'], limit=True))
        self.createBox(0)

    def createBox(self, idx):
        component_id = self._getTextComponentID(idx)
        g_guiFlash.createComponent(component_id, COMPONENT_TYPE.LABEL, {'text': '', 'alpha': 0.0, 'x': 0, 'y': 0, 'alignX': COMPONENT_ALIGN.CENTER, 'alignY': COMPONENT_ALIGN.TOP})
        shadow = config.data['textShadow']
        if shadow['enabled']:
            g_guiFlash.updateComponent(component_id, {'shadow': shadow})

    def removeBox(self, idx):
        g_guiFlash.deleteComponent(self._getTextComponentID(idx))

    def addText(self, text):
        if not config.data['enabled']:
            return
        if self.isTextAdding:
            callback(0.1, partial(self.addText, text))
            return
        style_conf = config.data['textStyle']
        formatted_text = '<font size=\'%s\' face=\'%s\'><p align=\'%s\'>%s</p></font>' % (style_conf['size'], style_conf['font'], style_conf['align'], text)

        if self.texts:
            self.removeFirstText()

        idx = len(self.texts)
        self.texts.append(formatted_text)

        if idx > 0:
            self.createBox(idx)

        g_guiFlash.updateComponent(self._getTextComponentID(idx), {'text': formatted_text})
        g_guiFlash.updateComponent(self._getTextComponentID(idx), {'alpha': 1.0}, {'duration': 0.5})
        self.isTextAdding = True
        callback(0.5, self.onTextAddingComplete)
        self.callbacks.append(callback(config.data['delay'] + 0.5, self.removeFirstText))

    def onTextAddingComplete(self):
        self.isTextAdding = False

    def onTextRemovalComplete(self):
        self.isTextRemoving = False
        for idx in range(len(self.texts)):
            g_guiFlash.updateComponent(self._getTextComponentID(idx), {'text': self.texts[idx], 'alpha': 1.0, 'y': idx})
        if len(self.texts) > 0:
            self.removeBox(len(self.texts))

    def removeFirstText(self):
        if self.isTextRemoving:
            callback(0.1, self.removeFirstText)
            return
        if self.texts:
            del self.texts[0]
        if self.callbacks:
            try:
                cancelCallback(self.callbacks[0])
            except ValueError:
                pass
            except StandardError:
                traceback.print_exc()
            del self.callbacks[0]
        self.isTextRemoving = True
        g_guiFlash.updateComponent(self._getTextComponentID(0), {'alpha': 0.0}, {'duration': 0.5})
        for idx in range(1, len(self.texts) + 1):
            g_guiFlash.updateComponent(self._getTextComponentID(idx), {'y': 0}, {'duration': 0.5})
        callback(0.5, self.onTextRemovalComplete)

    def _getTextComponentID(self, idx):
        return '{}.text{}'.format(self.ID, idx)


g_flash = None
config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')
try:
    from gambiter import g_guiFlash
    from gambiter.flash import COMPONENT_TYPE, COMPONENT_ALIGN, COMPONENT_EVENT
    g_flash = Flash(config.ID)
except ImportError as err:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    logError(config.ID, 'gambiter.GUIFlash not found. Text viewing disabled. {}', err)
except StandardError:
    g_guiFlash = COMPONENT_TYPE = COMPONENT_ALIGN = COMPONENT_EVENT = None
    traceback.print_exc()


def _isEntitySatisfiesConditions(entity):
    if (entity is None) or not hasattr(entity, 'publicInfo'):
        return False
    enabled_for = config.data['showFor']
    is_ally = 0 < getattr(entity.publicInfo, 'team', 0) == getPlayer().team
    show_for = (enabled_for == 0) or ((enabled_for == 1) and is_ally) or ((enabled_for == 2) and not is_ally)
    alive_only = (not config.data['aliveOnly']) or (config.data['aliveOnly'] and entity.isAlive())
    return show_for and alive_only


class DataConstants(object):

    __slots__ = ('_playerVehicle', '_vehicle', '_typeDescriptor', '_gunShots',)

    def __init__(self):
        self._playerVehicle = None
        self._vehicle = None
        self._typeDescriptor = None
        self._gunShots = None

    def init(self, vehicle, playerVehicle=None):
        self._playerVehicle = playerVehicle
        self._vehicle = vehicle
        self._typeDescriptor = vehicle.typeDescriptor if vehicle is not None else self._playerVehicle.typeDescriptor
        self._gunShots = self._typeDescriptor.gun.shots if self._typeDescriptor else None

    def reset(self):
        self._playerVehicle = None
        self._vehicle = None
        self._typeDescriptor = None
        self._gunShots = None

    def nick_name(self):
        return self._vehicle.publicInfo.name if self._vehicle else None

    def marks_on_gun(self):
        return self._vehicle.publicInfo.marksOnGun if self._vehicle else None

    def vehicle_type(self):
        if self._typeDescriptor:
            tags = self._typeDescriptor.type.tags
            if 'lightTank' in tags:
                return 'LT'
            elif 'mediumTank' in tags:
                return 'MT'
            elif 'heavyTank' in tags:
                return 'HT'
            elif 'AT-SPG' in tags:
                return 'TD'
            elif 'SPG' in tags:
                return 'SPG'
        return None

    def vehicle_name(self):
        return self._typeDescriptor.type.userString if self._typeDescriptor else None

    def vehicle_system_name(self):
        return self._typeDescriptor.name if self._typeDescriptor else None

    def icon_system_name(self):
        return self._typeDescriptor.name.replace(':', '-') if self._typeDescriptor else None

    def gun_name(self):
        return self._typeDescriptor.gun.shortUserString if self._typeDescriptor else None

    def max_ammo(self):
        return self._typeDescriptor.gun.maxAmmo if self._typeDescriptor else None

    def gun_reload(self):
        return '%.2f' % self._typeDescriptor.gun.reloadTime if self._typeDescriptor else None

    def gun_dpm(self):
        if not self._typeDescriptor:
            return None
        time = self._typeDescriptor.gun.reloadTime + (self._typeDescriptor.gun.clip[0] - 1) * \
               self._typeDescriptor.gun.clip[1]
        shell = self._typeDescriptor.gun.shots[0].shell
        damage = shell.armorDamage if hasattr(shell, 'armorDamage') else shell.damage
        return '%d' % (round(self._typeDescriptor.gun.clip[0] / time * 60 * damage[0], 0))

    def gun_reload_equip(self, eq1=1, eq2=1, eq3=1, eq4=1):
        if not self._typeDescriptor:
            return None
        else:
            reload_orig = self._typeDescriptor.gun.reloadTime
            rammer = 0.9 if (self._typeDescriptor.gun.clip[0] == 1) and (eq1 == 1) else 1
            if (eq2 == 1) and (eq3 == 1) and (eq4 == 1):
                crew = 1.32
            elif (eq2 == 1) and (eq3 == 1) and (eq4 == 0):
                crew = 1.27
            elif (eq2 == 1) and (eq3 == 0) and (eq4 == 1):
                crew = 1.21
            elif (eq2 == 1) and (eq3 == 0) and (eq4 == 0):
                crew = 1.16
            elif (eq2 == 0) and (eq3 == 1) and (eq4 == 1):
                crew = 1.27
            elif (eq2 == 0) and (eq3 == 1) and (eq4 == 0):
                crew = 1.21
            elif (eq2 == 0) and (eq3 == 0) and (eq4 == 1):
                crew = 1.16
            else:
                crew = 1.10
            return '%.2f' % (round((reload_orig / (0.57 + 0.43 * crew)) * rammer, 2))

    def gun_dpm_equip(self, eq1=1, eq2=1, eq3=1, eq4=1):
        if not self._typeDescriptor:
            return None
        reload_equip = float(self.gun_reload_equip(eq1, eq2, eq3, eq4))
        time = reload_equip + (self._typeDescriptor.gun.clip[0] - 1) * self._typeDescriptor.gun.clip[1]
        shell = self._typeDescriptor.gun.shots[0].shell
        damage = shell.armorDamage if hasattr(shell, 'armorDamage') else shell.damage
        return '%d' % (round(self._typeDescriptor.gun.clip[0] / time * 60 * damage[0], 0))

    def gun_clip(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.gun.clip[0])

    def gun_clip_reload(self):
        return None if not self._typeDescriptor else '%.1f' % (self._typeDescriptor.gun.clip[1])

    def gun_burst(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.gun.burst[0])

    def gun_burst_reload(self):
        return None if not self._typeDescriptor else '%.1f' % (self._typeDescriptor.gun.burst[1])

    def gun_aiming_time(self):
        return None if not self._typeDescriptor else '%.1f' % self._typeDescriptor.gun.aimingTime

    def gun_accuracy(self):
        return None if not self._typeDescriptor else '%.2f' % round(self._typeDescriptor.gun.shotDispersionAngle * 100, 2)

    def shell_name_1(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 1) else '%s' % self._gunShots[0].shell.userString

    def shell_name_2(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 2) else '%s' % self._gunShots[1].shell.userString

    def shell_name_3(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 3) else '%s' % self._gunShots[2].shell.userString

    def shell_damage_1(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 1) else '%d' % (self._gunShots[0].shell.armorDamage[0] if hasattr(self._gunShots[0].shell, 'armorDamage') else self._gunShots[0].shell.damage[0])

    def shell_damage_2(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 2) else '%d' % (self._gunShots[1].shell.armorDamage[0] if hasattr(self._gunShots[1].shell, 'armorDamage') else self._gunShots[1].shell.damage[0])

    def shell_damage_3(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 3) else '%d' % (self._gunShots[2].shell.armorDamage[0] if hasattr(self._gunShots[2].shell, 'armorDamage') else self._gunShots[2].shell.damage[0])

    def shell_power_1(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 1) else '%d' % (self._gunShots[0].piercingPower[0])

    def shell_power_2(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 2) else '%d' % (self._gunShots[1].piercingPower[0])

    def shell_power_3(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 3) else '%d' % (self._gunShots[2].piercingPower[0])

    def shell_type_1(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 1) else self._gunShots[0].shell.kind.lower()

    def shell_type_2(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 2) else self._gunShots[1].shell.kind.lower()

    def shell_type_3(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 3) else self._gunShots[2].shell.kind.lower()

    def shell_speed_1(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 1) else '%d' % round(self._gunShots[0].speed * 1.25)

    def shell_speed_2(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 2) else '%d' % round(self._gunShots[1].speed * 1.25)

    def shell_speed_3(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 3) else '%d' % round(self._gunShots[2].speed * 1.25)

    def shell_distance_1(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 1) else '%d' % self._gunShots[0].maxDistance

    def shell_distance_2(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 2) else '%d' % self._gunShots[1].maxDistance

    def shell_distance_3(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 3) else '%d' % self._gunShots[2].maxDistance

    def stun_radius(self):
        if (self._gunShots is not None) and (self._gunShots[0].shell.stun is not None):
            return '%d' % self._gunShots[0].shell.stun.stunRadius
        else:
            return None

    def stun_duration_min(self):
        if (self._gunShots is not None) and (self._gunShots[0].shell.stun is not None):
            time = (round(self._gunShots[0].shell.stun.stunRadius * self._gunShots[0].shell.stun.guaranteedStunDuration, 1))
            return '%.1f' % time
        else:
            return None

    def stun_duration_max(self):
        if (self._gunShots is not None) and (self._gunShots[0].shell.stun is not None):
            return '%d' % self._gunShots[0].shell.stun.stunDuration
        else:
            return None

    def angle_pitch_up(self):
        return None if not self._typeDescriptor else '%d' % (degrees(-self._typeDescriptor.gun.pitchLimits['absolute'][0]))

    def angle_pitch_down(self):
        return None if not self._typeDescriptor else '%d' % (degrees(-self._typeDescriptor.gun.pitchLimits['absolute'][1]))

    def angle_pitch_left(self):
        return None if (not self._typeDescriptor) or (not self._typeDescriptor.gun.turretYawLimits) else '%d' % (degrees(-self._typeDescriptor.gun.turretYawLimits[0]))

    def angle_pitch_right(self):
        return None if (not self._typeDescriptor) or (not self._typeDescriptor.gun.turretYawLimits) else '%d' % (degrees(self._typeDescriptor.gun.turretYawLimits[1]))

    def vehicle_max_health(self):
        return None if not self._typeDescriptor else '%d' % self._typeDescriptor.maxHealth

    def armor_hull_front(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.hull.primaryArmor[0])

    def armor_hull_side(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.hull.primaryArmor[1])

    def armor_hull_back(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.hull.primaryArmor[2])

    def turret_name(self):
        return None if not self._typeDescriptor else '%s' % self._typeDescriptor.turret.shortUserString

    def armor_turret_front(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.turret.primaryArmor[0])

    def armor_turret_side(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.turret.primaryArmor[1])

    def armor_turret_back(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.turret.primaryArmor[2])

    def vehicle_weight(self):
        return '%.1f' % (round(self._typeDescriptor.physics['weight'] / 1000, 1)) if self._typeDescriptor else None

    def chassis_max_weight(self):
        return None if not self._typeDescriptor else '%.1f' % (round(self._typeDescriptor.chassis.maxLoad / 1000, 1))

    def engine_name(self):
        return None if not self._typeDescriptor else '%s' % self._typeDescriptor.engine.shortUserString

    def engine_power(self):
        return None if not self._typeDescriptor else '%d' % (round(self._typeDescriptor.engine.power / 735.49875, 0))

    def engine_power_density(self):
        if not self._typeDescriptor:
            return None
        power = self._typeDescriptor.engine.power / 735.49875
        weight = self._typeDescriptor.physics['weight'] / 1000
        return '%.2f' % (round(power / weight, 2))

    def speed_forward(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.physics['speedLimits'][0] * 3.6)

    def speed_backward(self):
        return None if not self._typeDescriptor else '%d' % (self._typeDescriptor.physics['speedLimits'][1] * 3.6)

    def hull_speed_turn(self):
        return None if not self._typeDescriptor else '%.2f' % (degrees(self._typeDescriptor.chassis.rotationSpeed))

    def turret_speed_turn(self):
        return None if not self._typeDescriptor else '%.2f' % (degrees(self._typeDescriptor.turret.rotationSpeed))

    def invis_stand(self):
        return None if not self._typeDescriptor else '%.1f' % (self._typeDescriptor.type.invisibility[1] * 57)

    def invis_stand_shot(self):
        return None if not self._typeDescriptor else '%.2f' % (self._typeDescriptor.type.invisibility[1] * self._typeDescriptor.gun.invisibilityFactorAtShot * 57)

    def invis_move(self):
        return None if not self._typeDescriptor else '%.1f' % (self._typeDescriptor.type.invisibility[0] * 57)

    def invis_move_shot(self):
        return None if not self._typeDescriptor else '%.2f' % (self._typeDescriptor.type.invisibility[0] * self._typeDescriptor.gun.invisibilityFactorAtShot * 57)

    def vision_radius(self):
        return None if not self._typeDescriptor else '%d' % self._typeDescriptor.turret.circularVisionRadius

    def radio_name(self):
        return None if not self._typeDescriptor else '%s' % self._typeDescriptor.radio.shortUserString

    def radio_radius(self):
        return None if not self._typeDescriptor else '%d' % self._typeDescriptor.radio.distance

    def nation(self):
        return None if not self._typeDescriptor else NAMES[self._typeDescriptor.type.customizationNationID]

    def level(self):
        return None if not self._typeDescriptor else '%d' % self._typeDescriptor.type.level

    def rlevel(self):
        _ROMAN_LEVEL = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI')
        return None if not self._typeDescriptor else _ROMAN_LEVEL[self._typeDescriptor.type.level - 1]

    def pl_gun_reload(self):
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self.gun_reload()

    def pl_gun_reload_equip(self):
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self.gun_reload_equip()

    def pl_gun_dpm(self):
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self.gun_dpm()

    def pl_gun_dpm_equip(self):
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self.gun_dpm_equip()

    def pl_vehicle_weight(self):
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self.vehicle_weight()

    def pl_vision_radius(self):
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self.vision_radius()

    def pl_gun_aiming_time(self):
        self._typeDescriptor = self._playerVehicle.typeDescriptor
        return self.gun_aiming_time()


class CompareMacros(object):
    __slots__ = ('value1', 'value2')

    def __init__(self):
        self.value1 = None
        self.value2 = None

    def reset(self):
        self.value1 = None
        self.value2 = None

    def set_data(self, value1, value2):
        try:
            self.value1 = float(value1)
            self.value2 = float(value2)
        except ValueError:
            raise ValueError('Values must be numeric.')

    @property
    def compareDelim(self):
        return self._get_compare_attribute('delim')

    @property
    def compareColor(self):
        return self._get_compare_attribute('color')

    def _get_compare_attribute(self, attribute):
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
        self.textFormats = config.data['format'] if config.data['enabled'] else None
        self.hotKeyDown = False
        self.visible = False
        self.timer = None
        super(InfoPanel, self).__init__()

    def reset(self):
        self.__init__()
        g_macros.reset()

    def get_func_response(self, func_name):
        if not hasattr(self, func_name):
            return None
        func = getattr(self, func_name, None)
        if callable(func):
            result = func()
            return str(result) if result is not None else ''
        return None

    def set_texts_formatted(self):
        if not config.data['enabled']:
            return ''

        text_format = self.textFormats
        text_format = self.replace_macros(text_format, MACROS)
        text_format = self.replace_compare_macros(text_format, COMPARE_MACROS)

        return text_format

    def replace_macros(self, text_format, macros):
        for macro in macros:
            if macro in text_format:
                func_name = macro.strip('{}')
                func_response = self.get_func_response(func_name)
                text_format = text_format.replace(macro, func_response)
        return text_format

    def replace_compare_macros(self, text_format, compare_macros):
        for macro in compare_macros:
            if macro in text_format:
                start_index = text_format.find(macro + '(')
                end_index = text_format.find(')', start_index + 6) + 1
                reader = text_format[start_index:end_index]
                func = reader.split('(')[0]
                args = reader[reader.find('(') + 1:reader.find(')')].split(',')
                if len(args) == 2:
                    arg1, arg2 = args[0].strip(), args[1].strip()
                    g_macros.set_data(arg1, arg2)
                    func_res = getattr(g_macros, func)
                    text_format = text_format.replace('{{' + reader + '}}', str(func_res))
        return text_format

    def handleKey(self, isDown):
        if isDown:
            self.onUpdateVehicle(getPlayer().getVehicleAttached())
            self.hotKeyDown = True
        else:
            self.hotKeyDown = False
            target = getTarget()
            if _isEntitySatisfiesConditions(target):
                self.onUpdateVehicle(target)
            else:
                self.hide()

    def hide(self):
        if self.timer is not None and self.timer.isStarted():
            self.timer.stop()
            self.timer = None
        self.visible = False

    def onUpdateBlur(self):
        if self.hotKeyDown or (getPlayer().getVehicleAttached() is None):
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
        player_vehicle = player.getVehicleAttached()
        if player_vehicle is not None:
            self.visible = True
            if hasattr(vehicle, 'typeDescriptor'):
                self.init(vehicle, player_vehicle)
            elif hasattr(player_vehicle, 'typeDescriptor'):
                self.init(None, player_vehicle)
            g_flash.addText(self.set_texts_formatted())


g_macros = CompareMacros()
g_mod = InfoPanel()


@override(PlayerAvatar, 'targetBlur')
def new__targetBlur(func, self, prevEntity):
    if config.data['enabled'] and _isEntitySatisfiesConditions(prevEntity):
        g_mod.onUpdateBlur()
    func(self, prevEntity)


@override(PlayerAvatar, 'targetFocus')
def new_targetFocus(func, self, entity):
    func(self, entity)
    if not (config.data['enabled'] and _isEntitySatisfiesConditions(entity)):
        return
    g_mod.onUpdateVehicle(entity)


@override(PlayerAvatar, 'handleKey')
def new_handleKey(func, self, isDown, key, mods):
    func(self, isDown, key, mods)
    if config.data['enabled'] or (key != checkKeys(config.data['altKey'])) or MessengerEntry.g_instance.gui.isFocused():
        return
    g_mod.handleKey(isDown)


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    if not config.data['enabled']:
        return
    if not getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        return
    g_mod.reset()
