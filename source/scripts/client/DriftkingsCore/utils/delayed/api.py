# -*- coding: utf-8 -*-
import traceback
from functools import partial

from Event import SafeEvent

from DriftkingsCore import loadJson, override, logError, smart_update

__all__ = ['g_modsListApi']


def try_import():
    try:
        from gui.modsListApi import g_modsListApi as modsListApi
    except ImportError:
        logError('DriftkingsCore: ModsListApi package not found, ModsSettingsApi check skipped')

        class ModsList(object):
            @staticmethod
            def addModification(*_, **__):
                return NotImplemented

            @staticmethod
            def updateModification(*_, **__):
                return NotImplemented

            @staticmethod
            def alertModification(*_, **__):
                return NotImplemented

            @staticmethod
            def clearModificationAlert(*_, **__):
                return NotImplemented

        modsListApi = ModsList()
        return modsListApi, None, None
    try:
        # WG
        from gui.Scaleform.framework.managers.context_menu import ContextMenuManager
        from gui.shared.personality import ServicesLocator
        from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
        from gui.Scaleform.framework.entities.View import ViewKey
        # modSettingsApi
        from gui.modsSettingsApi.api import ModsSettingsApi
        from gui.modsSettingsApi.hotkeys import HotkeysController
        from gui.modsSettingsApi.view import loadView, ModsSettingsApiWindow, HotkeyContextHandler
        from gui.modsSettingsApi._constants import MOD_ICON, MOD_NAME, MOD_DESCRIPTION, STATE_TOOLTIP, VIEW_ALIAS
    except ImportError as e:
        logError('DriftkingsCore: ModsSettingsApi package not loaded:', e)
        return modsListApi, None, None
    ModsSettingsApiWindow.api = None
    HotkeyContextHandler.api = None

    @override(ModsSettingsApiWindow, '__init__')
    def new_init(func, self, ctx, *args, **kwargs):
        self.api = ctx
        return func(self, ctx, *args, **kwargs)

    @override(ContextMenuManager, 'requestOptions')
    def new_requestOptions(func, self, handlerType, ctx, *args, **kwargs):
        func(self, handlerType, ctx, *args, **kwargs)
        if handlerType == 'modsSettingsHotkeyContextHandler':
            self._ContextMenuManager__currentHandler.api = ServicesLocator.appLoader.getDefLobbyApp().containerManager.getViewByKey(ViewKey(VIEW_ALIAS)).api

    class DriftkingsSettings(ModsSettingsApi):
        def __init__(self, modsGroup, ID, langID, i18n):
            self.modsGroup = modsGroup
            self.ID = ID
            self.lang = langID
            # folder to core p1
            self.modSettingsID = 'Driftkings_GUI'
            self.isMSAWindowOpen = False
            self.activeMods = set()
            self.config = {'templates': {}, 'settings': {}, 'data': {}}
            self.settingsListeners = {}
            self.buttonListeners = {}
            # Events
            self.onSettingsChanged = SafeEvent()
            self.onButtonClicked = SafeEvent()
            self.onWindowClosed = SafeEvent()
            self.updateHotKeys = SafeEvent()
            self.onWindowOpened = SafeEvent()
            # folder to core p2
            self.hotkeys = HotkeysController(self)
            self.hotkeys.onUpdated += self.updateHotKeys
            self.userSettings = {
                'modsListApiName': MOD_NAME,
                'modsListApiDescription': MOD_DESCRIPTION,
                'modsListApiIcon': 'gui/maps/icons/Driftkings/small.png',
                'windowTitle': MOD_NAME,
                'enableButtonTooltip': STATE_TOOLTIP,
            }
            smart_update(self.userSettings, i18n)
            self.settingsLoad()
            self.configLoad()
            modsListApi.addModification(
                id=ID,
                name=self.userSettings['modsListApiName'],
                description=self.userSettings['modsListApiDescription'],
                icon=self.userSettings['modsListApiIcon'],
                enabled=True,
                login=True,
                lobby=True,
                # callback=functools.partial(loadView, self)
                callback=self.MSAPopulate
            )
            self.onWindowClosed += self.MSADispose

        @staticmethod
        def MSALoad(api=None):
            app = ServicesLocator.appLoader.getApp()
            app.loadView(SFViewLoadParams(VIEW_ALIAS, VIEW_ALIAS), ctx=api)

        def MSAPopulate(self):
            self.isMSAWindowOpen = True
            self.onWindowOpened()
            self.MSALoad(self)

        def MSADispose(self):
            self.isMSAWindowOpen = False

        def MSAApply(self, alias, *a, **kw):
            self.settingsListeners[alias](*a, **kw)

        def MSAButton(self, alias, *a, **kw):
            self.buttonListeners[alias](*a, **kw)

        def settingsLoad(self):
            smart_update(self.userSettings, loadJson(self.ID, self.lang, self.userSettings, 'mods/configs/%s/%s/i18n/' % (self.modsGroup, self.ID)))

        def configLoad(self):
            pass

        def configSave(self):
            pass

        def setModTemplate(self, linkage, template, callback, buttonHandler):
            self.settingsListeners[linkage] = callback
            self.buttonListeners[linkage] = buttonHandler
            return super(DriftkingsSettings, self).setModTemplate(linkage, template, self.MSAApply, self.MSAButton)

    return modsListApi, ModsSettingsApi, DriftkingsSettings


g_modsListApi, MSA_Orig, ModsSettings = try_import()


def registerSettings(config):
    """
    Register a settings block in this mod's settings window.
    """
    newLangID = config.lang
    try:
        from helpers import getClientLanguage
        newLangID = str(getClientLanguage()).lower()
        if newLangID != config.lang:
            config.lang = newLangID
            config.loadLang()
    except StandardError:
        traceback.print_exc()
    if MSA_Orig is None:
        print config.LOG, '=' * 25
        print config.LOG, 'no-GUI mode activated'
        print config.LOG, '=' * 25
        return
    if config.modSettingsID not in config.modSettingsContainers:
        config.modSettingsContainers[config.modSettingsID] = ModsSettings(config.modsGroup, config.modSettingsID, newLangID, config.container_i18n)
    msc = config.modSettingsContainers[config.modSettingsID]
    msc.onWindowOpened += config.onMSAPopulate
    msc.onWindowClosed += config.onMSADestroy
    if not hasattr(config, 'blockIDs'):
        msc.setModTemplate(config.ID, config.template, config.onApplySettings, config.onButtonPress)
        return
    templates = config.template
    [msc.setModTemplate(config.ID + ID, templates[ID], partial(config.onApplySettings, blockID=ID), partial(config.onButtonPress, blockID=ID))for ID in config.blockIDs]
