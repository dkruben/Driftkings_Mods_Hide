# -*- coding:utf-8 -*-
import os
import traceback

from json_load import loadJson, loadJsonOrdered


def smart_update(orig, new):
    """
    Recursively updates the values in the `orig` dictionary with the values from the `new` dictionary.
    Args:
        orig (dict): The original dictionary to be updated.
        new (dict): The dictionary containing the new values.
    Returns:
        bool: True if any values were updated, False otherwise.
    """
    changed = False
    # Iterate over each key in the original dictionary
    for k in orig:
        v = new.get(k)
        # If the value is a dictionary, recursively update it
        if isinstance(v, dict):
            changed |= smart_update(orig[k], v)
        # If the value is not None, update the original dictionary
        elif v is not None:
            # If the value is a unicode string, encode it to utf-8
            if isinstance(v, unicode):
                v = v.encode('utf-8')
            # Check if the value has changed
            changed |= orig[k] != v
            # Update the original dictionary with the new value
            orig[k] = v
    # Return True if any values were updated, False otherwise
    return changed


class DummyConfigInterface(object):
    def __init__(self):
        """Declaration for attribute placeholders, all attributes should be defined in init(), getData() and loadLang()"""
        self.ID = ''
        self.modsGroup = ''
        self.lang = 'en'
        self.modSettingsID = self.ID + '_settings'
        self.init()
        self.loadLang()
        self.load()

    def init(self):
        """
        self.ID = 'AwesomeMod'  - mod ID
        self.modSettingsID = 'AwesomeModSettings' - mod settings container ID.
            Be careful, this will be an alias for a ViewSettings Object!
        """
        pass

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

    def createTemplate(self):
        """
        :return: dict representing your mod's settings template.
        """
        raise NotImplementedError

    def migrateConfigs(self):
        """
        Called before initial config load. Should contain code that updates configs from old version
        """
        pass

    def readData(self, quiet=True):
        """
        Is called upon mod loading and every time settings window is opened.
        Loading main config data from main file should be placed here.
        :param quiet: optional, if you have debug mode in your mod - this will be useful
        """
        pass

    def readCurrentSettings(self, quiet=True):
        """
        Is called upon mod loading and every time settings window is opened.
        Loading additional config data should be placed here.
        :param quiet: optional, if you have debug mode in your mod - this will be useful
        """
        pass

    def onApplySettings(self, settings):
        """
        Is called when user clicks the "Apply" button in settings window.
        And also upon mod loading because settings API thinks that it is the only place to store mod settings.
        :param settings: new setting values.
        """
        raise NotImplementedError

    def updateMod(self):
        """
        A function to update mod template after config actions are complete.
        """
        pass

    def onMSAPopulate(self):
        """
        Called when mod settings window is about to start opening.
        :return:
        """
        self.readData()
        self.readCurrentSettings()
        self.updateMod()

    def onMSADestroy(self):
        """
        Is called when mod settings window has closed.
        """
        pass

    def onButtonPress(self, vName, value):
        """
        Called when a "preview' button for corresponding setting is pressed.
        :param vName: settings value name
        :param value: currently selected setting value (may differ from currently applied. As said, used for settings preview)
        """
        pass

    def registerSettings(self):
        pass

    def load(self):
        """
        Called after mod __init__() is complete.
        """
        self.migrateConfigs()
        self.registerSettings()
        self.readData(False)
        self.readCurrentSettings(False)
        self.updateMod()


class SimpleCreated(object):
    def __init__(self):
        self.ID = ''
        self.data = {}
        self.i18n = {}
        self.author = ''
        self.version = ''
        self.modsGroup = ''
        self.configPath = ''
        self.langPath = ''
        self.modSettingsID = ''

    LOG = property(lambda self: self.ID + ':')
    loadDataJson = lambda self, *a, **kw: loadJson(self.ID, self.ID, self.data, self.configPath, *a, **kw)
    writeDataJson = lambda self, *a, **kw: loadJson(self.ID, self.ID, self.data, self.configPath, True, False, *a, **kw)
    loadLangJson = lambda self, *a, **kw: loadJson(self.ID, self.lang, self.i18n, self.langPath, *a, **kw)

    def init(self):
        self.configPath = '../../../../../../res/configs/%s/%s/' % (self.modsGroup, self.ID)
        self.langPath = '%si18n/' % self.configPath

    def loadLang(self):
        smart_update(self.i18n, self.loadLangJson())

    def readData(self, quiet=True):
        smart_update(self.data, self.loadDataJson(quiet=quiet))

    def readConfigDir(self, quiet, recursive=False, dir_name='configs', error_not_exist=True, make_dir=True, ordered=False, encrypted=False, migrate=False, ext='.json'):
        configs_dir = self.configPath + dir_name + '/'
        if not os.path.isdir(configs_dir):
            if error_not_exist and not quiet:
                print '=' * 30
                print self.LOG, 'config directory not found:', configs_dir
                print '=' * 30
            if make_dir:
                os.makedirs(configs_dir)
        for dir_path, sub_dirs, names in os.walk(configs_dir):
            dir_path = dir_path.replace('\\', '/').decode('windows-1251').encode('utf-8')
            local_path = dir_path.replace(configs_dir, '')
            names = sorted([x for x in names if x.endswith(ext)], key=str.lower)
            if not recursive:
                sub_dirs[:] = []
            for name in names:
                name = os.path.splitext(name)[0].decode('windows-1251').encode('utf-8')
                json_data = {}
                try:
                    if ext == '.json':
                        if ordered:
                            json_data = loadJsonOrdered(self.ID, dir_path, name)
                        else:
                            json_data = loadJson(self.ID, name, json_data, dir_path, encrypted=encrypted)
                except StandardError:
                    traceback.print_exc()
                if not json_data:
                    print self.LOG, (dir_path and (dir_path + '/')) + name + ext, 'is invalid'
                    continue
                try:
                    if ext == '.json':
                        if migrate:
                            self.onMigrateConfig(quiet, dir_path, local_path, name, json_data, sub_dirs, names)
                        else:
                            self.onReadConfig(quiet, local_path, name, json_data, sub_dirs, names)
                except StandardError:
                    traceback.print_exc()

    def onMigrateConfig(self, quiet, path, dir_path, name, json_data, sub_dirs, names):
        """clearing sub_dirs and/or names using slice assignment breaks the corresponding loop"""
        pass

    def onReadConfig(self, quiet, dir_path, name, json_data, sub_dirs, names):
        """clearing sub_dirs and/or names using slice assignment breaks the corresponding loop"""
        pass

    def onReadDataSection(self, quiet, path, dir_path, name, data_section, sub_dirs, names):
        """clearing sub_dirs and/or names using slice assignment breaks the corresponding loop"""
        pass

    def onApplySettings(self, settings):
        smart_update(self.data, settings)
        self.writeDataJson()

    def message(self):
        return '%s v.%s %s' % (self.ID, self.version, self.author)

    def load(self):
        print '=' * 30
        print self.message() + ': initialised.'
        print '=' * 30


class ConfigInterface(SimpleCreated, DummyConfigInterface):
    def __init__(self):
        SimpleCreated.__init__(self)
        DummyConfigInterface.__init__(self)

    def getData(self):
        return self.data

    def createTemplate(self):
        pass
        # raise NotImplementedError

    def readData(self, quiet=True):
        smart_update(self.data, self.loadDataJson(quiet=quiet))

    def onApplySettings(self, settings):
        smart_update(self.data, settings)
        self.writeDataJson()

    def load(self):
        DummyConfigInterface.load(self)
        SimpleCreated.load(self)
