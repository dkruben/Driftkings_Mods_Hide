# -*- coding:utf-8 -*-
import os
import traceback

from json_load import loadJson, loadJsonOrdered


def smart_update(orig, new):
    changed = False
    for k in orig:
        v = new.get(k)
        if isinstance(v, dict):
            changed |= smart_update(orig[k], v)
        elif v is not None:
            if isinstance(v, unicode):
                v = v.encode('utf-8')
            changed |= orig[k] != v
            orig[k] = v
    return changed


class DummyConfigInterface(object):
    def __init__(self):
        self.ID = ''
        self.modsGroup = ''
        self.lang = 'en'
        self.modSettingsID = self.ID + '_settings'
        self.init()
        self.loadLang()
        self.load()

    def init(self):
        pass

    def getData(self):
        raise NotImplementedError

    def loadLang(self):
        pass

    def createTemplate(self):
        raise NotImplementedError

    def migrateConfigs(self):
        pass

    def readData(self, quiet=True):
        pass

    def readCurrentSettings(self, quiet=True):
        pass

    def onApplySettings(self, settings):
        raise NotImplementedError

    def updateMod(self):
        pass

    def onMSAPopulate(self):
        self.readData()
        self.readCurrentSettings()
        self.updateMod()

    def onMSADestroy(self):
        pass

    def onButtonPress(self, vName, value):
        pass

    def registerSettings(self):
        pass

    def load(self):
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
                print('=' * 30)
                print(self.LOG, 'config directory not found:', configs_dir)
                print('=' * 30)
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
                    print(self.LOG, (dir_path and (dir_path + '/')) + name + ext, 'is invalid')
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
        pass

    def onReadConfig(self, quiet, dir_path, name, json_data, sub_dirs, names):
        pass

    def onReadDataSection(self, quiet, path, dir_path, name, data_section, sub_dirs, names):
        pass

    def onApplySettings(self, settings):
        smart_update(self.data, settings)
        self.writeDataJson()

    def message(self):
        return '%s v.%s %s' % (self.ID, self.version, self.author)

    def load(self):
        print('=' * 30)
        print(self.message() + ': Initialised.')
        print('=' * 30)


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
