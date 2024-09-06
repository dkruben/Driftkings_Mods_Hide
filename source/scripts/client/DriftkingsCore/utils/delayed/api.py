# -*- coding: utf-8 -*-
import traceback
from functools import partial
from DriftkingsCore import loadJson, override, logError, smart_update

__all__ = ('g_modsListApi', 'registerSettings',)


def try_import():
    try:
        from gui.modsListApi import g_modsListApi as modsListApi
    except ImportError:
        logError('DriftkingsCore', 'ModsListApi package not found, ModsSettingsApi check skipped')

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
        from Event import SafeEvent
        from gui.shared.personality import ServicesLocator
        from gui.shared.utils.functions import makeTooltip
        from gui.Scaleform.framework.managers.context_menu import ContextMenuManager
        from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
        from gui.Scaleform.framework.entities.View import ViewKey
        # modsSettingsApi
        from gui.modsSettingsApi.api import ModsSettingsApi
        from gui.modsSettingsApi.hotkeys import HotkeysController
        from gui.modsSettingsApi.l10n import l10n
        from gui.modsSettingsApi.view import loadView, ModsSettingsApiWindow
        from gui.modsSettingsApi.context_menu import HotkeyContextMenuHandler
        from gui.modsSettingsApi._constants import MOD_ICON, VIEW_ALIAS
    except ImportError as e:
        logError('DriftkingsCore: ModsSettingsApi package not loaded:', e)
        return modsListApi, None, None

    ModsSettingsApiWindow.api = None
    HotkeyContextMenuHandler.api = None

    @override(ModsSettingsApiWindow, '__init__')
    def new_init(func, self, ctx, *args, **kwargs):
        self.api = ctx
        return func(self, ctx, *args, **kwargs)

    @override(ContextMenuManager, 'requestOptions')
    def new_requestOptions(func, self, handlerType, ctx, *args, **kwargs):
        func(self, handlerType, ctx, *args, **kwargs)
        if handlerType == 'modsSettingsHotkeyContextMenuHandler':
            self._ContextMenuManager__currentHandler.api = ServicesLocator.appLoader.getDefLobbyApp().containerManager.getViewByKey(ViewKey(VIEW_ALIAS)).api

    class DriftkingsSettings(ModsSettingsApi):
        """
        Custom class for Driftkings mod settings.
        """

        def __init__(self, modsGroup, ID, langID, i18n):
            self.modsGroup = modsGroup
            self.ID = ID
            self.lang = langID
            self.modSettingsID = 'Driftkings_GUI'
            self.isMSAWindowOpen = False
            self.activeMods = set()
            self.config = {'templates': {}, 'settings': {}, 'data': {}}
            self.settingsListeners = {}
            self.buttonListeners = {}
            self.onSettingsChanged = SafeEvent()
            self.onButtonClicked = SafeEvent()
            self.onWindowClosed = SafeEvent()
            self.updateHotKeys = SafeEvent()
            self.onWindowOpened = SafeEvent()

            # Initialize hotkeys controller
            self.hotkeys = HotkeysController(self)
            self.hotkeys.onUpdated += self.updateHotKeys

            # Initialize user settings
            self.userSettings = {
                'modsListApiName': l10n('name'),
                'modsListApiDescription': l10n('description'),
                'modsListApiIcon': 'gui/maps/icons/Driftkings/small.png' or MOD_ICON,
                'windowTitle': l10n('name'),
                'enableButtonTooltip': makeTooltip(l10n('stateswitcher/tooltip/header'), l10n('stateswitcher/tooltip/body')),
            }
            smart_update(self.userSettings, i18n)

            # Load settings and config
            self.settingsLoad()
            self.configLoad()

            # Add modification to modsListApi
            modsListApi.addModification(
                id=ID,
                name=self.userSettings.get('modsListApiName'),
                description=self.userSettings.get('modsListApiDescription'),
                icon=self.userSettings.get('modsListApiIcon'),
                enabled=True,
                login=True,
                lobby=True,
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

        def MSAApply(self, alias, *args, **kwargs):
            if alias in self.settingsListeners:
                self.settingsListeners[alias](*args, **kwargs)

        def MSAButton(self, alias, *args, **kwargs):
            if alias in self.buttonListeners:
                self.buttonListeners[alias](*args, **kwargs)

        def settingsLoad(self):
            try:
                config_data = loadJson(self.ID, self.lang, self.userSettings, 'mods/configs/%s/%s/i18n/' % (self.modsGroup, self.ID))
                smart_update(self.userSettings, config_data)
            except IOError:
                logError('DriftkingsCore', 'Configuration file not found for ID: %s' % self.ID)
            except Exception as err:
                logError('DriftkingsCore', 'Error loading configurations: %s' % str(err))

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
    for ID in config.blockIDs:
        msc.setModTemplate(config.ID + ID, templates[ID], partial(config.onApplySettings, blockID=ID), partial(config.onButtonPress, blockID=ID))