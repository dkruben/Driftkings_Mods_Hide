# -*- coding: utf-8 -*-
from constants import ARENA_GUI_TYPE

AS_BATTLE = 'InfoPanelView'
AS_INJECTOR = 'InfoPanelViewInjector'
AS_SWF = 'InfoPanel.swf'

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

COMPARE_MACROS = ['compareDelim', 'compareColor', 'isTarget', 'isPremium']

DISABLED_BATTLES = (ARENA_GUI_TYPE.EPIC_RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM_TRAINING, ARENA_GUI_TYPE.EPIC_TRAINING)
