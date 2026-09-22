# -*- coding: utf-8 -*-
"""Associate slotted achievement objects with their own dossier, with bounded storage."""
from collections import OrderedDict

from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement
from .monkeypatch import override

_dossiers = OrderedDict()
_MAX_DOSSIERS = 256


@override(MarkOnGunAchievement, '__init__')
def _rememberDossier(func, self, dossier, value=None):
    result = func(self, dossier, value)
    _dossiers[id(self)] = (self, dossier)
    while len(_dossiers) > _MAX_DOSSIERS:
        _dossiers.popitem(last=False)
    return result


def getAchievementDossier(achievement):
    item = _dossiers.get(id(achievement))
    return item[1] if item is not None and item[0] is achievement else None
