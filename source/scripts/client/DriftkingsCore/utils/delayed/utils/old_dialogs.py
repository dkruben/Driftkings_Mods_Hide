# -*- coding: utf-8 -*-
from gui.Scaleform.daapi.view.dialogs import ConfirmDialogButtons, DIALOG_BUTTON_ID
from gui.Scaleform.daapi.view.dialogs.SimpleDialog import SimpleDialog

from frameworks.wulf import WindowLayer
from gui.impl.pub.dialog_window import DialogButtons
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader
from wg_async import AsyncReturn, wg_async, wg_await

from ... import override

__all__ = ('showConfirmDialog', 'showI18nDialog', 'showInfoDialog', 'showCrewDialog')


def _showSimpleDialog(header, text, buttons, callback):
    from gui import DialogsInterface
    from gui.Scaleform.daapi.view.dialogs import SimpleDialogMeta
    DialogsInterface.showDialog(SimpleDialogMeta(header, text, buttons, None), callback)


def showConfirmDialog(header, text, buttons, callback):
    _showSimpleDialog(header, text, (_ConfirmButtons if len(buttons) == 2 else _RestartButtons)(*buttons), callback)


def showI18nDialog(header, text, key, callback):
    from gui.Scaleform.daapi.view.dialogs import I18nConfirmDialogButtons
    _showSimpleDialog(header, text, I18nConfirmDialogButtons(key), callback)


def showInfoDialog(header, text, button, callback):
    from gui.Scaleform.daapi.view.dialogs import InfoDialogButtons
    _showSimpleDialog(header, text, InfoDialogButtons(button), callback)


class _ConfirmButtons(ConfirmDialogButtons):
    def getLabels(self):
        return ({'id': DIALOG_BUTTON_ID.SUBMIT, 'label': self._submit, 'focused': True},
                {'id': DIALOG_BUTTON_ID.CLOSE, 'label': self._close, 'focused': False})


class _RestartButtons(_ConfirmButtons):
    def __init__(self, submit, shutdown, close):
        self._shutdown = shutdown
        super(_RestartButtons, self).__init__(submit, close)

    def getLabels(self):
        return ({'id': DIALOG_BUTTON_ID.SUBMIT, 'label': self._submit, 'focused': True},
                {'id': 'shutdown', 'label': self._shutdown, 'focused': False},
                {'id': DIALOG_BUTTON_ID.CLOSE, 'label': self._close, 'focused': False})


class DialogBase(object):
    appLoader = dependency.descriptor(IAppLoader)

    @property
    def view(self):
        app = self.appLoader.getApp()
        if app is not None and app.containerManager is not None:
            return app.containerManager.getView(WindowLayer.VIEW)
        return None


class CrewDialog(DialogBase):
    @wg_async
    def showCrewDialog(self, vehicle_name, message, logo, confirm, cancel, ignore):
        from gui.impl.dialogs import dialogs
        from gui.impl.dialogs.builders import InfoDialogBuilder
        builder = InfoDialogBuilder()
        builder.setFormattedTitle('\n'.join((logo, vehicle_name)))
        builder.setFormattedMessage(message)
        builder.addButton(DialogButtons.SUBMIT, None, True, rawLabel=confirm)
        builder.addButton(DialogButtons.CANCEL, None, False, rawLabel=cancel)
        builder.addButton(DialogButtons.PURCHASE, None, False, rawLabel=ignore)
        result = yield wg_await(dialogs.show(builder.build(self.view)))
        raise AsyncReturn(result)


showCrewDialog = CrewDialog().showCrewDialog


@override(SimpleDialog, '__callHandler')
def new_callHandler(func, self, buttonID, *args, **kwargs):
    if len(self._SimpleDialog__buttons) != 3:
        return func(self, buttonID, *args, **kwargs)
    self._SimpleDialog__handler(buttonID)
    self._SimpleDialog__isProcessed = True


@override(SimpleDialog, '_dispose')
def new_Dialog_dispose(func, self, *args, **kwargs):
    if len(self._SimpleDialog__buttons) == 3:
        self._SimpleDialog__isProcessed = True
        # don't call the handler upon window destruction, onWindowClose is fine
    return func(self, *args, **kwargs)
