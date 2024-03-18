# -*- coding: utf-8 -*-
import re

import BigWorld
from notification.NotificationsCollection import NotificationsCollection
from notification.actions_handlers import NotificationsActionsHandlers

from ... import override

__all__ = ()


@override(NotificationsCollection, 'addItem')
def new_addItem(func, self, item, *args, **kwargs):
    if 'temp_SM' not in item._vo['message']['message']:
        return func(self, item, *args, **kwargs)
    item._vo['message']['message'] = item._vo['message']['message'].replace('temp_SM', '')
    item._vo['notify'] = False
    if item._settings:
        item._settings.isNotify = False
    return True


@override(NotificationsActionsHandlers, 'handleAction')
def new_handleAction(func, self, model, typeID, entityID, actionName, *args, **kwargs):
    from notification.settings import NOTIFICATION_TYPE
    if typeID == NOTIFICATION_TYPE.MESSAGE and re.match('https?://', actionName, re.I):
        BigWorld.wg_openWebBrowser(actionName)
    else:
        func(self, model, typeID, entityID, actionName, *args, **kwargs)
