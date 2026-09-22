# -*- coding: utf-8 -*-
"""EU 2.4 Gameface implementation; the legacy NationTreeNode SWF is not used."""
import json
import logging
import weakref

from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_OF_MASTERY_RECORD
from frameworks.wulf import ViewModel, ViewSettings
from gui.impl.pub import ViewImpl
from gui.shared.personality import ServicesLocator
from DriftkingsCore import DriftkingsConfigInterface, override

LOG = logging.getLogger('Driftkings.MarksOnGunTechTree')
FEATURE = 'DriftkingsMarksOnGunTechTree'
RESOURCE = 'mods/Driftkings/MarksOnGunTechTree/model'
ASSETS = 'coui://gui/gameface/mods/Driftkings/MarksOnGunTechTree/'
_views = weakref.WeakKeyDictionary()


class ConfigInterface(DriftkingsConfigInterface):
    def init(self):
        self.ID = 'MarksOnGunTechTree'
        self.version = '2.1.0 (%(file_compile_date)s)'
        self.data = {
            'enabled': True,
            'showInTechTree': True,
            'showInTechTreeMarkOfGunPercent': True,
            'showInTechTreeMastery': True,
            'showInTechTreeMarkOfGunTankNameColored': False,
            'badgeOffsetX': 115,
            'badgeOffsetY': 0,
            'badgeFontSize': 14
        }
        self.i18n = {'UI_description': 'MarksOnGunTechTree (Gameface)'}
        for key, label in (('showInTechTree', 'Show badges in the tech tree'), ('showInTechTreeMarkOfGunPercent', 'Show Marks of Excellence percentage'), ('showInTechTreeMastery', 'Show mastery badge'), ('showInTechTreeMarkOfGunTankNameColored', 'Color vehicle name by MoE')):
            self.i18n['UI_setting_' + key + '_text'] = label
            self.i18n['UI_setting_' + key + '_tooltip'] = ''
        self.i18n.update({
            'UI_setting_badgeOffsetX_text': 'Position X (left / right)',
            'UI_setting_badgeOffsetX_tooltip': 'Negative: left. Positive: right.',
            'UI_setting_badgeOffsetY_text': 'Position Y (up / down)',
            'UI_setting_badgeOffsetY_tooltip': 'Negative: up. Positive: down.'
        })
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showInTechTree'),
                self.tb.createControl('showInTechTreeMarkOfGunPercent'),
                self.tb.createControl('showInTechTreeMastery'),
                self.tb.createControl('showInTechTreeMarkOfGunTankNameColored')
            ],
            'column2': [
                self.tb.createStepper('badgeOffsetX', -300, 300, 1, manual=True),
                self.tb.createStepper('badgeOffsetY', -100, 100, 1, manual=True)
                ]
        }

    def onApplySettings(self, settings):
        super(ConfigInterface, self).onApplySettings(settings)
        for child in list(_views.values()):
            try:
                child.refresh()
            except Exception:
                LOG.exception('Could not apply tech tree settings to the active view')


config = ConfigInterface()


def vehicle_marks(vehicle_id):
    """Only the account's own dossier; no network requests or other-player data."""
    dossier = ServicesLocator.itemsCache.items.getVehicleDossier(int(vehicle_id))
    vehicle = ServicesLocator.itemsCache.items.getItemByCD(int(vehicle_id))
    tier = int(vehicle.level)
    raw = dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') if tier >= 5 else 0
    percent = max(0.0, min(100.0, float(raw or 0) / 100.0))
    mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
    mastery_value = int(mastery.getValue() or 0) if mastery else 0
    return {'percent': percent, 'tier': tier, 'mastery': max(0, min(4, mastery_value))}


def make_payload(vehicle_ids):
    enabled = bool(config.data.get('enabled') and config.data.get('showInTechTree'))
    vehicles = {}
    if enabled:
        for vehicle_id in vehicle_ids:
            try:
                values = vehicle_marks(vehicle_id)
                vehicles[str(vehicle_id)] = values
            except Exception:
                # One unavailable dossier must not prevent the tree from opening.
                LOG.debug('Dossier unavailable for %s', vehicle_id, exc_info=True)
    return json.dumps({
        'enabled': enabled, 'vehicles': vehicles,
        'showPercent': bool(config.data.get('showInTechTreeMarkOfGunPercent')),
        'showMastery': bool(config.data.get('showInTechTreeMastery')),
        'colorName': bool(config.data.get('showInTechTreeMarkOfGunTankNameColored')),
        'offsetX': config.data.get('badgeOffsetX', 115),
        'offsetY': config.data.get('badgeOffsetY', 0),
        'fontSize': config.data.get('badgeFontSize', 14)}, separators=(',', ':'))


def install():
    from gui.impl.gen_utils import INVALID_RES_ID
    from gui.impl.lobby.tech_tree.tech_tree_view import TechTreeView
    from openwg_gameface import gf_mod_inject, res_id_by_key
    for name in ('_onLoading', '_finalize', '_TechTreeView__fillNodeOverrides', '_TechTreeView__updateNodeOverrides'):
        if not callable(getattr(TechTreeView, name, None)):
            raise RuntimeError('Unsupported TechTreeView API: ' + name)

    class MarksModel(ViewModel):
        def __init__(self):
            super(MarksModel, self).__init__(properties=2, commands=0)

        def _initialize(self):
            super(MarksModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            gf_mod_inject(self, FEATURE, styles=[ASSETS + 'marks.css'], scripts=[ASSETS + 'marks.js'])

    class MarksView(ViewImpl):
        def __init__(self, resource_id):
            self.vehicle_ids = ()
            super(MarksView, self).__init__(ViewSettings(resource_id, model=MarksModel()))

        def refresh(self, vehicle_ids=None):
            if vehicle_ids is not None:
                self.vehicle_ids = tuple(vehicle_ids)
            with self.getViewModel().transaction() as model:
                model._setString(0, make_payload(self.vehicle_ids))

    @override(TechTreeView, '_onLoading')
    def new__on_loading(original, view, *args, **kwargs):
        try:
            resource_id = res_id_by_key(RESOURCE)
            if resource_id == INVALID_RES_ID:
                LOG.warning('Missing resource map entry: %s', RESOURCE)
            else:
                child = MarksView(resource_id)
                _views[view] = child
                view.setChildView(resource_id, child)
                LOG.info('Attached Gameface tech tree badges (resource %s)', resource_id)
        except Exception:
            LOG.exception('Could not attach tech tree badges')
        return original(view, *args, **kwargs)

    @override(TechTreeView, '_TechTreeView__fillNodeOverrides')
    def new__fill_nodes(original, view, model, nodes):
        result = original(view, model, nodes)
        child = _views.get(view)
        if child is not None:
            try:
                child.refresh(nodes.keys())
            except Exception:
                LOG.exception('Could not refresh tech tree badges')
        return result

    @override(TechTreeView, '_TechTreeView__updateNodeOverrides')
    def new__update_nodes(original, view, nodes):
        result = original(view, nodes)
        child = _views.get(view)
        if child is not None:
            try:
                child.refresh()
            except Exception:
                LOG.exception('Could not update tech tree badges')
        return result

    @override(TechTreeView, '_finalize')
    def new__finalize(original, view, *args, **kwargs):
        _views.pop(view, None)
        return original(view, *args, **kwargs)


try:
    install()
except Exception:
    LOG.exception('Gameface tech tree integration unavailable; keeping the standard tree')
