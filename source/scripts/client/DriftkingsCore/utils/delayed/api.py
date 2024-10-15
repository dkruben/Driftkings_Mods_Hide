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
            def removeModification(*_, **__):
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
        import Event
        from gui.shared.personality import ServicesLocator
        from gui.Scaleform.framework.entities.View import ViewKey
        from gui.modsSettingsApi.api import ModsSettingsApi
        from gui.modsSettingsApi.hotkeys import HotkeysController
        from gui.modsSettingsApi.view import loadView, ModsSettingsApiWindow
        from gui.modsSettingsApi.context_menu import HotkeyContextMenuHandler
        from gui.modsSettingsApi._constants import MOD_ICON, VIEW_ALIAS
    except ImportError as err:
        logError('DriftkingsCore: ModsSettingsApi package not loaded:', err)
        return modsListApi, None, None

    ModsSettingsApiWindow.api = None
    HotkeyContextMenuHandler.api = None

    @override(ModsSettingsApiWindow, '__init__')
    def new_view_init(base, self, ctx, *args, **kwargs):
        self.api = ctx
        base(self, ctx, *args, **kwargs)

    @override(HotkeyContextMenuHandler, '__init__')
    def new_ctx_init(base, self, *args, **kwargs):
        self.api = ServicesLocator.appLoader.getDefLobbyApp().containerManager.getViewByKey(ViewKey(VIEW_ALIAS)).api
        base(self, *args, **kwargs)

    class DriftkingsSettings(ModsSettingsApi):
        def __init__(self, modsGroup, ID, langID, i18n):
            self.modsGroup = modsGroup
            self.ID = ID
            self.lang = langID
            self.isMSAWindowOpen = False
            self.activeMods = set()
            self.state = {'templates': {}, 'settings': {}}
            self.settingsListeners = {}
            self.buttonListeners = {}
            self.hotkeys = HotkeysController(self)
            self.onWindowOpened = Event.Event()
            self.onWindowClosed = Event.Event()
            self.onHotkeysUpdated = Event.Event()
            self.onSettingsChanged = Event.Event()
            self.onButtonClicked = Event.Event()
            self.userSettings = {
                'modsListApiName': "Driftking's Mods Settings",
                'modsListApiDescription': "<font color='#DD7700'><b>Driftkings</b></font>'s modification settings",
                'windowTitle': "Driftking's Mods Settings",
                'modsListApiIcon': 'gui/maps/icons/Driftkings/small.png' or MOD_ICON,
                'enableButtonTooltip': '{HEADER}ON/OFF{/HEADER}{BODY}Enable/Disable this mod{/BODY}'
            }
            smart_update(self.userSettings, i18n)
            self.loadSettings()
            self.loadState()
            kwargs = {
                'id': ID,
                'name': self.userSettings.get('modsListApiName'),
                'description': self.userSettings.get('modsListApiDescription'),
                'icon': self.userSettings.get('modsListApiIcon'),
                'enabled': True,
                'login': True,
                'lobby': True,
                'callback': self.MSAPopulate
            }
            modsListApi.addModification(**kwargs)
            self.onWindowClosed += self.MSADispose

        def MSAPopulate(self):
            self.isMSAWindowOpen = True
            self.onWindowOpened()
            loadView(self)

        def MSADispose(self):
            self.isMSAWindowOpen = False

        def MSAApply(self, alias, *args, **kwargs):
            if alias in self.settingsListeners:
                self.settingsListeners[alias](*args, **kwargs)

        def MSAButton(self, alias, *args, **kwargs):
            if alias in self.buttonListeners:
                self.buttonListeners[alias](*args, **kwargs)

        def loadSettings(self):
            smart_update(self.userSettings, loadJson(self.ID, self.lang, self.userSettings, 'mods/configs/%s/%s/i18n/' % (self.modsGroup, self.ID)))

        def loadState(self):
            pass

        def saveState(self):
            pass

        def setModTemplate(self, linkage, template, callback, buttonHandler):
            self.settingsListeners[linkage] = callback
            self.buttonListeners[linkage] = buttonHandler
            return super(DriftkingsSettings, self).setModTemplate(linkage, template, self.MSAApply, self.MSAButton)

    return modsListApi, ModsSettingsApi, DriftkingsSettings

g_modsListApi, MSA_Orig, ModsSettings = try_import()


def registerSettings(config):
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
        print config.LOG, '=' * 35
        print config.LOG, 'no-GUI mode activated'
        print config.LOG, '=' * 35
        return
    if config.modSettingsID not in config.modSettingsContainers:
        config.modSettingsContainers[config.modSettingsID] = ModsSettings(
            config.modsGroup, config.modSettingsID, newLangID, config.container_i18n)
    msc = config.modSettingsContainers[config.modSettingsID]
    msc.onWindowOpened += config.onMSAPopulate
    msc.onWindowClosed += config.onMSADestroy
    if not hasattr(config, 'blockIDs'):
        msc.setModTemplate(config.ID, config.template, config.onApplySettings, config.onButtonPress)
        return
    templates = config.template
    [msc.setModTemplate(config.ID + ID, templates[ID], partial(config.onApplySettings, blockID=ID), partial(config.onButtonPress, blockID=ID)) for ID in config.blockIDs]
