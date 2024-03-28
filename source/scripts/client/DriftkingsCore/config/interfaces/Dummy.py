# -*- coding: utf-8 -*-
# from ..template_builders import DummyTemplateBuilder
# vx
import traceback
from functools import partial

import BigWorld
import Event
from constants import DEFAULT_LANGUAGE
from ..template_builders import DummyBlockTemplateBuilder, DummyTemplateBuilder
from DriftkingsCore.utils.delayed.api import modSettingsContainers

# class DummyConfigInterface(object):
#    modSettingsContainers = {}
#    isMSAOpen = property(lambda self: getattr(self.modSettingsContainers.get(self.modSettingsID), 'isMSAOpen', False))
#    MSAInstance = property(lambda self: self.modSettingsContainers.get(self.modSettingsID))

#    def __init__(self):
#        """Declaration for attribute placeholders, all attributes should be defined in init(), getData() and loadLang()"""
#        self.ID = ''
#        self.modsGroup = ''
#        self.i18n = {}
#        self.lang = DEFAULT_LANGUAGE
#        self.modSettingsID = self.ID + '_settings'
#        self.init()
#        self.loadLang()
#        self.tb = self.createTB()
#        self.load()

#    def init(self):
#        """
#        self.ID = 'AwesomeMod'  - mod ID
#        self.modSettingsID = 'AwesomeModSettings' - mod settings container ID.
#            Be careful, this will be an alias for a ViewSettings Object!
#        """
#        pass

#   def getData(self):
#       """
#       :return: dict with your mod settings (if they are stored elsewhere, otherwise you should use ConfigInterface instead)
#       """
#       raise NotImplementedError
#
#    def loadLang(self):
#        """
#        self.i18n = {} - your mod texts for messages, setting labels, etc.
#        """
#        pass

#    def createTB(self):
#        return DummyTemplateBuilder(self.i18n)

#    def createTemplate(self):
#        """
#        :return: dict representing your mod's settings template.
#        """
#        raise NotImplementedError

#    @property
#    def template(self):
#        return self.createTemplate()

#    @property
#    def container_i18n(self):
#        return {}

#    def migrateConfigs(self):
#        """
#        Called before initial config load. Should contain code that updates configs from old version
#        """
#        pass

#    def readData(self, quiet=True):
#        """
#        Is called upon mod loading and every time settings window is opened.
#        Loading main config data from main file should be placed here.
#        :param quiet: optional, if you have debug mode in your mod - this will be useful
#        """
#        pass

#    def readCurrentSettings(self, quiet=True):
#        """
#        Is called upon mod loading and every time settings window is opened.
#        Loading additional config data should be placed here.
#        :param quiet: optional, if you have debug mode in your mod - this will be useful
#        """
#        pass

#    def onApplySettings(self, settings):
#        """
#        Is called when user clicks the "Apply" button in settings window.
#        And also upon mod loading because settings API thinks that it is the only place to store mod settings.
#        :param settings: new setting values.
#        """
#        raise NotImplementedError

#    def updateMod(self):
#        """
#        A function to update mod template after config actions are complete.
#        """
#        if self.MSAInstance is None:
#            return
#        self.MSAInstance.config['templates'][self.ID] = self.template
#        self.MSAInstance.updateModSettings(self.ID, self.getData())

#    def onMSAPopulate(self):
#        """
#        Called when mod settings window is about to start opening.
#        :return:
#        """
#        self.readData()
#        self.readCurrentSettings()
#        self.updateMod()

#    def onMSADestroy(self):
#        """
#        Is called when mod settings window has closed.
#        """
#        pass

#    def onButtonPress(self, vName, value):
#        """
#        Called when a "preview' button for corresponding setting is pressed.
#        :param vName: settings value name
#        :param value: currently selected setting value (may differ from currently applied. As said, used for settings preview)
#        """
#        pass

#    def registerSettings(self):
#        from DriftkingsCore.utils.delayed.api import registerSettings
#        registerSettings(self)

#    def load(self):
#        """
#        Called after mod __init__() is complete.
#        """
#        self.migrateConfigs()
#        self.registerSettings()
#        self.readData(False)
#        self.readCurrentSettings(False)
#        self.updateMod()


# class DummyConfBlockInterface(DummyConfigInterface):
#    def __init__(self):
#        self._blockIDs = []  # overwrite in init() of derived class
#        super(DummyConfBlockInterface, self).__init__()

#    def getData(self, blockID=None):
#        raise NotImplementedError('Data block for block %s is not defined' % blockID)

#    @property
#    def blockIDs(self):
#        return self._blockIDs

#    def createTemplate(self, blockID=None):
#        raise NotImplementedError('Template for block %s is not created' % blockID)

#    @property
#    def template(self):
#        return {blockID: self.createTemplate(blockID) for blockID in self.blockIDs}

#    def onApplySettings(self, settings, blockID=None):
#        raise NotImplementedError

#    def updateMod(self):
#        if self.MSAInstance is None:
#            return
#        templates = self.template  # saves calls
#        for blockID in self.blockIDs:
#            self.MSAInstance.config['templates'][self.ID + blockID] = templates[blockID]
#            self.MSAInstance.updateModSettings(self.ID + blockID, self.getData(blockID))

#    def onButtonPress(self, vName, value, blockID=None):
#        pass

class DummyConfigInterface(object):
    isMSAWindowOpen = property(lambda self: modSettingsContainers[self.modSettingsID].isMSAWindowOpen if self.modSettingsID in modSettingsContainers else False)

    def __init__(self):
        """Declaration for attribute placeholders, all attributes should be defined in init(), getData() and loadLang()"""
        self.ID = ''
        self.i18n = {}
        self.lang = DEFAULT_LANGUAGE
        self.modSettingsID = self.ID + '_settings'
        self._tb = None
        self._containerClass = None
        self.init()
        self.loadLang()
        self.load()

    def init(self):
        """
        self.ID = 'AwesomeMod'  - mod ID
        self.modSettingsID = 'AwesomeModSettings' - mod settings container ID.
            Be careful, this will be an alias for a ViewSettings Object!
        """
        raise NotImplementedError

    def getData(self):
        """
        :return: dict with your mod settings (if they are stored elsewhere, otherwise you should use ConfigInterface instead)
        """
        raise NotImplementedError

    def loadLang(self):
        """
        self.i18n = {} - your mod texts for messages, setting labels, etc.
        """
        pass

    @property
    def tb(self):
        if self._tb is None:
            self._tb = DummyTemplateBuilder(self.i18n)
        return self._tb

    def createTemplate(self):
        """
        :return: dict representing your mod's settings template.
        """
        raise NotImplementedError

    def readCurrentSettings(self, quiet=True):
        """
        Is called upon mod loading and every time settings window is opened.
        Loading config data from files should be placed here.
        :param quiet: optional, if you have debug mode in your mod - this will be useful
        """
        raise NotImplementedError

    def onApplySettings(self, settings):
        """
        Is called when user clicks the "Apply" button in settings window.
        And also upon mod loading because vxSettings thinks that API is the only place to store mod settings.
        :param settings: new setting values.
        """
        raise NotImplementedError

    def updateMod(self):
        """
        A function to update mod template after config actions are complete.
        """
        # noinspection PyUnresolvedReferences
        from gui.vxSettingsApi import vxSettingsApi
        vxSettingsApi.updateMod(self.modSettingsID, self.ID, self.createTemplate)

    def onMSAPopulate(self):
        """
        Called when mod settings window is about to start opening.
        :return:
        """
        self.readCurrentSettings()
        self.updateMod()

    def onMSADestroy(self):
        """
        Is called when mod settings window has closed.
        """
        pass

    def onButtonPress(self, modSettingsID, ID, vName, value):
        """
        Is called when a "preview' button for corresponding setting is pressed.
        :param modSettingsID: settings container ID.
        :param ID: mod ID
        :param vName: settings value name
        :param value: currently selected setting value (may differ from currently applied. As said, used for settings preview)
        """
        pass

    def onDataChanged(self, modSettingsID, ID, vName, value):
        """
        Is called when something in settings window is changed. May be used to dynamically disable some controls, for example.
        :param modSettingsID: settings container ID.
        :param ID: mod ID
        :param vName: settings value name
        :param value: new setting value (this one is not yet applied!)
        """
        pass

    @property
    def containerClass(self):
        if self._containerClass is None:
            self._containerClass = DummySettingContainer
        return self._containerClass

    def registerSettings(self):
        from DriftkingsCore.utils.delayed.api import registerSettings
        registerSettings(self)

    def load(self):
        """
        Called after mod __init__() is complete.
        """
        self.readCurrentSettings(False)
        self.registerSettings()


class DummyConfBlockInterface(object):
    isMSAWindowOpen = property(lambda self: modSettingsContainers[self.modSettingsID].isMSAWindowOpen)

    def __init__(self):
        self.ID = ''
        self.modsGroup = ''
        self.i18n = {}
        self._blockIDs = []  # overwrite in init() of derived class
        self.lang = DEFAULT_LANGUAGE
        self.modSettingsID = self.ID + '_settings'
        self._tb = None
        self._containerClass = None
        self.init()
        self.configPath = './mods/configs/%s/%s/' % (self.modsGroup, self.ID)
        self.langPath = '%si18n/' % self.configPath
        self.loadLang()
        self.load()

    def init(self):
        raise NotImplementedError

    def getDataBlock(self, blockID):
        raise NotImplementedError('Data block for block %s is not defined' % blockID)

    def loadLang(self):
        pass

    @property
    def blockIDs(self):
        return self._blockIDs

    @property
    def tb(self):
        if self._tb is None:
            self._tb = DummyBlockTemplateBuilder(self.i18n)
        return self._tb

    def createTemplate(self, blockID):
        raise NotImplementedError('Template for block %s is not created' % blockID)

    def readCurrentSettings(self, quiet=True):
        raise NotImplementedError

    def onApplySettings(self, blockID, settings):
        raise NotImplementedError

    def updateMod(self, blockID):
        # noinspection PyUnresolvedReferences
        from gui.vxSettingsApi import vxSettingsApi
        vxSettingsApi.updateMod(self.modSettingsID, self.ID + blockID, partial(self.createTemplate, blockID))

    def onMSAPopulate(self):
        self.readCurrentSettings()
        for blockID in self.blockIDs:
            self.updateMod(blockID)

    def onMSADestroy(self):
        pass

    def onButtonPress(self, modSettingsID, ID, vName, value):
        pass

    def onDataChanged(self, modSettingsID, ID, vName, value):
        pass

    def load(self):
        self.readCurrentSettings(False)
        self.registerSettings()

    @property
    def containerClass(self):
        if self._containerClass is None:
            self._containerClass = DummySettingContainer
        return self._containerClass

    def registerSettings(self):
        from DriftkingsCore.utils.delayed.api import registerSettings
        registerSettings(self, 'block')


class DummySettingContainer(object):
    def __init__(self, ID, configPath):
        self.configPath = configPath
        self.ID = ID
        self.version = '3.0.0 (%(file_compile_date)s)'
        self.author = 'Driftkings'
        self.lang = DEFAULT_LANGUAGE
        self.i18n = {
            'gui_name': 'Mods settings',
            'gui_description': 'Modifications enabling and settings',
            'gui_windowTitle': 'Mods settings',
            'gui_buttonOK': 'OK',
            'gui_buttonCancel': 'Cancel',
            'gui_buttonApply': 'Apply',
            'gui_enableButtonTooltip': '{HEADER}ON/OFF{/HEADER}{BODY}Enable/disable this mod{/BODY}'
        }
        self.onMSAPopulate = Event.Event()
        self.onMSADestroy = Event.Event()
        self.isMSAWindowOpen = False
        self.load()

    def loadLang(self):
        pass

    def feedbackHandler(self, container, eventType, *_):
        if container != self.ID:
            return
        # noinspection PyUnresolvedReferences
        from gui.vxSettingsApi import vxSettingsApiEvents
        if eventType == vxSettingsApiEvents.WINDOW_CLOSED:
            self.isMSAWindowOpen = False
            self.onMSADestroy()

    def MSAPopulate(self):
        # noinspection PyUnresolvedReferences
        from gui.vxSettingsApi import vxSettingsApi
        self.isMSAWindowOpen = True
        self.onMSAPopulate()
        vxSettingsApi.loadWindow(self.ID)

    def modsListRegister(self):
        kwargs = dict(
            id=self.ID, name=self.i18n['gui_name'], description=self.i18n['gui_description'],
            icon='../mods/configs/Driftkings/Driftkings_GUI/Driftkings_GUI.png', enabled=True, login=True, lobby=True, callback=self.MSAPopulate)
        try:
            BigWorld.g_modsListApi.addModification(**kwargs)
        except AttributeError:
            BigWorld.g_modsListApi.addMod(**kwargs)

    def load(self):
        self.loadLang()
        self.registerContainer()

    def registerContainer(self):
        try:
            from helpers import getClientLanguage
            newLang = str(getClientLanguage()).lower()
            if newLang != self.lang:
                self.lang = newLang
                self.loadLang()
        except StandardError:
            traceback.print_exc()
        try:
            # noinspection PyUnresolvedReferences
            from gui.modsListApi import g_modsListApi
            if not hasattr(BigWorld, 'g_modsListApi'):
                BigWorld.g_modsListApi = g_modsListApi
            # noinspection PyUnresolvedReferences
            from gui.vxSettingsApi import vxSettingsApi
            keys = ('windowTitle', 'buttonOK', 'buttonCancel', 'buttonApply', 'enableButtonTooltip')
            userSettings = {key: self.i18n['gui_%s' % key] for key in keys}
            vxSettingsApi.addContainer(self.ID, userSettings)
            vxSettingsApi.onFeedbackReceived += self.feedbackHandler
            BigWorld.callback(0.0, self.modsListRegister)
        except ImportError:
            print '%s: no-GUI mode activated' % self.ID
        except StandardError:
            traceback.print_exc()
