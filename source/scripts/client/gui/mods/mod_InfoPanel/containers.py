# -*- coding: utf-8 -*-
from nations import NAMES
from helpers import i18n

from math import degrees


class DataConstants(object):
    __slots__ = ('_playerVehicle', '_vehicle', '_typeDescriptor', '_gunShots')

    def __init__(self):
        self._playerVehicle = None
        self._vehicle = None
        self._typeDescriptor = None
        self._gunShots = None

    def init(self, vehicle, playerVehicle=None):
        self._playerVehicle = playerVehicle
        self._vehicle = vehicle
        self._typeDescriptor = vehicle.typeDescriptor if vehicle is not None else self._playerVehicle.typeDescriptor
        self._gunShots = self._typeDescriptor.gun.shots

    def reset(self):
        self._playerVehicle = None
        self._vehicle = None
        self._typeDescriptor = None
        self._gunShots = None

    def nick_name(self):
        return None if not self._vehicle else '%s' % self._vehicle.publicInfo.name

    def marks_on_gun(self):
        return None if not self._vehicle else '%s' % self._vehicle.publicInfo.marksOnGun

    def vehicle_type(self):
        vehType = None
        if self._typeDescriptor is not None and 'lightTank' in self._typeDescriptor.type.tags:
            vehType = 'LT'
        elif self._typeDescriptor is not None and 'mediumTank' in self._typeDescriptor.type.tags:
            vehType = 'MT'
        elif self._typeDescriptor is not None and 'heavyTank' in self._typeDescriptor.type.tags:
            vehType = 'HT'
        elif self._typeDescriptor is not None and 'AT-SPG' in self._typeDescriptor.type.tags:
            vehType = 'TD'
        elif self._typeDescriptor is not None and 'SPG' in self._typeDescriptor.type.tags:
            vehType = 'SPG'
        return vehType

    def vehicle_name(self):
        return None if not self._typeDescriptor else '%s' % self._typeDescriptor.type.userString

    def vehicle_system_name(self):
        return None if not self._typeDescriptor else '%s' % self._typeDescriptor.name

    def icon_system_name(self):
        return None if not self._typeDescriptor else '%s' % (self._typeDescriptor.name.replace(':', '-'))

    def gun_name(self):
        return None if not self._typeDescriptor else '%s' % self._typeDescriptor.gun.shortUserString

    @staticmethod
    def gun_caliber():
        return None if not gs else '%d' % gs[0].shell.caliber

    def max_ammo(self):
        return None if not self._typeDescriptor else '%d' % self._typeDescriptor.gun.maxAmmo

    def gun_reload(self):
        return None if not self._typeDescriptor else '%.2f' % self._typeDescriptor.gun.reloadTime

    def gun_dpm(self):
        if not self._typeDescriptor:
            return None
        else:
            time = self._typeDescriptor.gun.reloadTime + (self._typeDescriptor.gun.clip[0] - 1) * self._typeDescriptor.gun.clip[1]
            return '%d' % (round(self._typeDescriptor.gun.clip[0] / time * 60 * self._typeDescriptor.gun.shots[0].shell.damage[0], 0))

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
        else:
            reload_equip = float(self.gun_reload_equip(eq1, eq2, eq3, eq4))
            time = reload_equip + (self._typeDescriptor.gun.clip[0] - 1) * self._typeDescriptor.gun.clip[1]
            return '%d' % (round(self._typeDescriptor.gun.clip[0] / time * 60 * self._typeDescriptor.gun.shots[0].shell.damage[0], 0))

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
        return None if (not self._gunShots) or (len(self._gunShots) < 1) else '%d' % (self._gunShots[0].shell.damage[0])

    def shell_damage_2(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 2) else '%d' % (self._gunShots[1].shell.damage[0])

    def shell_damage_3(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 3) else '%d' % (self._gunShots[2].shell.damage[0])

    def shell_power_1(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 1) else '%d' % (self._gunShots[0].piercingPower[0])

    def shell_power_2(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 2) else '%d' % (self._gunShots[1].piercingPower[0])

    def shell_power_3(self):
        return None if (not self._gunShots) or (len(self._gunShots) < 3) else '%d' % (self._gunShots[2].piercingPower[0])

    def shell_type_1(self):
        return None if not self._gunShots or len(self._gunShots) < 1 else i18n.makeString('#ingame_gui:damageLog/shellType/%s' % self._gunShots[0].shell.kind.upper())

    def shell_type_2(self):
        return None if not self._gunShots or len(self._gunShots) < 2 else i18n.makeString('#ingame_gui:damageLog/shellType/%s' % self._gunShots[1].shell.kind.upper())

    def shell_type_3(self):
        return None if not self._gunShots or len(self._gunShots) < 3 else i18n.makeString('#ingame_gui:damageLog/shellType/%s' % self._gunShots[2].shell.kind.upper())

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
        return None if not self._typeDescriptor else '%.1f' % (round(self._typeDescriptor.physics['weight'] / 1000, 1))

    def chassis_max_weight(self):
        return None if not self._typeDescriptor else '%.1f' % (round(self._typeDescriptor.chassis.maxLoad / 1000, 1))

    def engine_name(self):
        return None if not self._typeDescriptor else '%s' % self._typeDescriptor.engine.shortUserString

    def engine_power(self):
        return None if not self._typeDescriptor else '%d' % (round(self._typeDescriptor.engine.power / 735.49875, 0))

    def engine_power_density(self):
        if not self._typeDescriptor:
            return None
        else:
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
        return None if not self._typeDescriptor else '%d' % self._typeDescriptor.radio.shortUserString

    def radio_radius(self):
        return None if not self._typeDescriptor else '%d' % self._typeDescriptor.radio.distance

    def nation(self):
        return None if not self._typeDescriptor else (NAMES[self._typeDescriptor.type.customizationNationID])

    def level(self):
        return None if not self._typeDescriptor else '%d' % self._typeDescriptor.type.level

    def rlevel(self):
        _ROMAN_LEVEL = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X')
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


container = DataConstants()
