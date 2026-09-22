# -*- coding: utf-8 -*-
"""Vehicle averages in the random hangar, rendered through OpenWG Gameface."""
import json
import logging
import math
import weakref

from CurrentVehicle import g_currentVehicle
from dossiers2.ui.achievements import MARK_ON_GUN_RECORD
from gui.shared.personality import ServicesLocator
from DriftkingsCore import DriftkingsConfigInterface, Analytics, override, calculate_version

LOG = logging.getLogger('Driftkings.HangarEfficiency')
FEATURE = 'DriftkingsHangarEfficiency'
RESOURCE = 'mods/Driftkings/HangarEfficiency/model'
ASSETS = 'coui://gui/gameface/mods/Driftkings/HangarEfficiency/'
g_controller = None


def finite(value, default=0.0):
    try:
        value = float(value)
        return default if math.isnan(value) or math.isinf(value) else value
    except (TypeError, ValueError, OverflowError):
        return default


class ConfigInterface(DriftkingsConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.2.0 (%(file_compile_date)s)'
        self.author = 'by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'avgAssist': True,
            'avgBlocked': True,
            'avgDamage': True,
            'avgStun': True,
            'gunMarks': True,
            'winRate': True,
            'battles': True,
            'positionX': 0,
            'positionY': 0
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_positionX_text': 'Horizontal position (X)',
            'UI_setting_positionX_tooltip': 'Smaller: left. Larger: right.',
            'UI_setting_positionY_text': 'Vertical position (Y)',
            'UI_setting_positionY_tooltip': 'Smaller: up. Larger: down.',
            'UI_version': calculate_version(self.version),
            'UI_setting_avgAssist_text': 'Avg Assist',
            'UI_setting_avgAssist_tooltip': 'Display average damage done with your assistance',
            'UI_setting_avgBlocked_text': 'Avg Blocked',
            'UI_setting_avgBlocked_tooltip': 'Display average armor blocked damage',
            'UI_setting_avgDamage_text': 'Avg Damage',
            'UI_setting_avgDamage_tooltip': 'Display average damage dealt',
            'UI_setting_avgStun_text': 'Avg Stun',
            'UI_setting_avgStun_tooltip': 'Display average damage to targets whose crews you have stunned (SPG)',
            'UI_setting_gunMarks_text': 'Gun Marks',
            'UI_setting_gunMarks_tooltip': 'Display gun mark percentage',
            'UI_setting_winRate_text': 'Win Rate',
            'UI_setting_winRate_tooltip': 'Show win percentage',
            'UI_setting_battles_text': 'Battles',
            'UI_setting_battles_tooltip': 'Show battles count'
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
                self.tb.createControl('winRate'),
                self.tb.createControl('battles'),
                self.tb.createStepper('positionX', -3840, 3840, 1),
                self.tb.createStepper('positionY', -2160, 2160, 1)
            ]
        }

    def get_view_config(self):
        return {'x': finite(self.data['positionX']), 'y': finite(self.data['positionY'])}

    def onApplySettings(self, settings):
        settings = dict(settings)
        for key, limit in (('positionX', 3840), ('positionY', 2160)):
            if key in settings:
                settings[key] = max(-limit, min(limit, finite(settings[key], self.data[key])))
        super(ConfigInterface, self).onApplySettings(settings)
        if g_controller is not None:
            g_controller.onApplySettings()


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


class EfficiencyData(object):
    def build_panel_model(self):
        result = {'config': config.get_view_config(), 'rows': [], 'vehicle': ''}
        if not g_currentVehicle.isPresent():
            return result
        vehicle = g_currentVehicle.item
        dossier = ServicesLocator.itemsCache.items.getVehicleDossier(g_currentVehicle.intCD)
        if dossier is None:
            return result
        stats = dossier.getRandomStats()
        battles = max(0, int(finite(stats.getBattlesCount())))
        result['vehicle'] = unicode(vehicle.shortUserName)
        values = [
            ('avgDamage', stats.getAvgDamage(), 'damage'),
            ('avgAssist', stats.getDamageAssistedEfficiency(), 'help'),
            ('avgBlocked', stats.getAvgDamageBlocked(), 'armor'),
            ('avgStun', stats.getAvgDamageAssistedStun(), 'stun'),
            ('battles', battles, 'battles'),
            ('winRate', finite(stats.getWinsEfficiency()) * 100, 'wins')
        ]
        for key, value, icon in values:
            if not config.data[key] or (key == 'avgStun' and vehicle.type != 'SPG'):
                continue
            text = ('%.2f%%' % finite(value) if key == 'winRate' else str(int(finite(value))))
            result['rows'].append({'key': key, 'label': config.i18n['UI_setting_%s_text' % key],
                                   'value': text if battles or key == 'battles' else '--',
                                   'icon': 'coui://gui/maps/icons/HangarEfficiency/%s.png' % icon})
        if config.data['gunMarks'] and vehicle.level > 4:
            marks = stats.getAchievement(MARK_ON_GUN_RECORD)
            if marks is not None:
                icon = marks.getIcons()['95x85']
                # Achievement icons use ../maps/... paths relative to gui/flash.
                icon = icon[3:] if icon.startswith('../') else icon
                result['rows'].append({'key': 'gunMarks', 'label': config.i18n['UI_setting_gunMarks_text'],
                                       'value': '%.2f%%' % finite(marks.getDamageRating()) if battles else '--',
                                       'icon': 'coui://gui/' + icon})
        return result


g_data = EfficiencyData()


class HangarEfficiencyController(object):
    def __init__(self):
        self.views = weakref.WeakKeyDictionary()
        self.visible = weakref.WeakKeyDictionary()

    def onApplySettings(self):
        for child in list(self.views.values()):
            child.refresh()

    def setVisible(self, parent, visible):
        self.visible[parent] = visible
        child = self.views.get(parent)
        if child is not None:
            child.refresh()


def install_gameface():
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent
    from gui.impl.gen_utils import INVALID_RES_ID
    from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
    from openwg_gameface import gf_mod_inject, res_id_by_key

    class EfficiencyModel(ViewModel):
        def __init__(self):
            super(EfficiencyModel, self).__init__(properties=2, commands=0)

        def _initialize(self):
            super(EfficiencyModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            gf_mod_inject(self, FEATURE, styles=[ASSETS + 'efficiency.css'], scripts=[ASSETS + 'efficiency.js'])

    class EfficiencyView(ViewComponent):
        def __init__(self, parent, resource_id):
            self._hangarRef = weakref.ref(parent)
            self._efficiencyActive = False
            super(EfficiencyView, self).__init__(layoutID=resource_id, model=EfficiencyModel)
            g_controller.views[parent] = self

        def _getEvents(self):
            return ((g_currentVehicle.onChanged, self.refresh),
                    (ServicesLocator.itemsCache.onSyncCompleted, self.refresh))

        def _onLoading(self, *args, **kwargs):
            super(EfficiencyView, self)._onLoading(*args, **kwargs)
            self._efficiencyActive = True
            self.refresh()

        def _finalize(self):
            self._efficiencyActive = False
            parent = self._hangarRef()
            if parent is not None and g_controller.views.get(parent) is self:
                g_controller.views.pop(parent, None)
            super(EfficiencyView, self)._finalize()

        def refresh(self, *args):
            if not self._efficiencyActive:
                return
            try:
                parent = self._hangarRef()
                visible = bool(parent is not None and g_controller.visible.get(parent, False)
                               and config.data['enabled'])
                payload = g_data.build_panel_model() if visible else {'config': config.get_view_config()}
                payload['config']['visible'] = visible
                with self.getViewModel().transaction() as model:
                    model._setString(0, json.dumps(payload, separators=(',', ':'), allow_nan=False))
            except Exception:
                LOG.exception('Could not update Gameface hangar card')
                with self.getViewModel().transaction() as model:
                    model._setString(0, '{"config":{"visible":false}}')

    @override(RandomHangar, '_getChildComponents')
    def get_children(original, parent, *args, **kwargs):
        children = dict(original(parent, *args, **kwargs))
        try:
            resource_id = res_id_by_key(RESOURCE)
            if resource_id == INVALID_RES_ID:
                LOG.warning('Missing Gameface resource: %s. Check OpenWG 1.1.6 and the resource map.', RESOURCE)
            else:
                children[resource_id] = lambda: EfficiencyView(parent, resource_id)
        except Exception:
            LOG.exception('Could not attach Gameface hangar card')
        return children

    @override(RandomHangar, '_onShown')
    def on_shown(original, parent, *args, **kwargs):
        result = original(parent, *args, **kwargs)
        g_controller.setVisible(parent, True)
        return result

    @override(RandomHangar, '_onHidden')
    def on_hidden(original, parent, *args, **kwargs):
        g_controller.setVisible(parent, False)
        return original(parent, *args, **kwargs)


g_controller = HangarEfficiencyController()
try:
    install_gameface()
except Exception:
    LOG.exception('Gameface hangar efficiency integration unavailable')
