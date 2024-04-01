# -*- coding: utf-8 -*-
import datetime
import json
import os
import re
from collections import defaultdict


class Base(object):
    _data = property(lambda self: self.data)
    _i18n = property(lambda self: self.i18n)
    version = defaultdict(lambda: 'ERROR', version='')

    def __init__(self, ID, folder, path, i18_path, author):
        self.ID = ID
        self.version = self.version
        self.author = author
        self.data = self._data
        self.i18n = self._i18n
        self.folder = folder
        self.path = path
        self.configs = None
        self.i18_path = i18_path
        self.fileTime = None
        self.i18n_fileTime = None
        self.appFile = '%s.json' % self.ID
        self.i18n_file = 'en.json'
        self.i18n_settings = None
        self.init()

    def init(self):
        self.getData()
        self.getLang()
        self.load_info()
        self.i18nLoad_info()
        self.loadJson(self.appFile, self.path)
        self.i18nLoadJson(self.i18n_file, self.i18_path)

    def getData(self):
        return self.data

    def load_info(self):
        self.configs = ['/'.join([self.path, self.appFile])]
        print ('-' * 74)
        print ('[NOTE] Loading mod: %s, [v.%s] by %s' % (self.ID, self.version, self.author))
        print ('-' * 74)

    @staticmethod
    def comments(data, strip_space=True):
        tokenizer = re.compile('"|(/\*)|(\*/)|(//)|\n|\r')
        endSlashes = re.compile(r'(\\)*$')
        inString = False
        inMultiString = False
        inSingle = False
        result = []
        index = 0
        for match in re.finditer(tokenizer, data):
            if not (inMultiString or inSingle):
                tmp = data[index:match.start()]
                if not inString and strip_space:
                    tmp = re.sub('[ \t\n\r]+', '', tmp)
                result.append(tmp)
            index = match.end()
            group = match.group()
            if group == '"' and not (inMultiString or inSingle):
                escaped = endSlashes.search(data, 0, match.start())
                if not inString or (escaped is None or len(escaped.group()) % 2 == 0):
                    inString = not inString
                index -= 1
            elif not (inString or inMultiString or inSingle):
                if group == '/*':
                    inMultiString = True
                elif group == '//':
                    inSingle = True
            elif group == '*/' and inMultiString and not (inString or inSingle):
                inMultiString = False
            elif group in '\r\n' and not (inMultiString or inString) and inSingle:
                inSingle = False
            elif not ((inMultiString or inSingle) or (group in ' \r\n\t' and strip_space)):
                result.append(group)

        result.append(data[index:])
        return ''.join(result)

    @staticmethod
    def jsonDumps(data):
        return json.dumps(data, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': '))

    def byteIfy(self, data):
        if data:
            if isinstance(data, dict):
                return {
                    self.byteIfy(key):
                        self.byteIfy(value) for key, value in data.iteritems()
                }
            elif isinstance(data, list):
                return [self.byteIfy(element) for element in data]
            elif isinstance(data, unicode):
                return data.encode('utf-8')
            else:
                return data
        return data

    def association(self, data):
        for i in data:
            if type(data[i]) is dict and self.data.get(i):
                self.data[i].update(data[i])
            else:
                self.data[i] = data[i]

    def load(self, new_path, mode='load'):
        if mode == 'load':
            for config in self.configs:
                with open(config, 'r') as json_file:
                    file_data = json_file.read().decode('utf-8-sig')
                    data = self.byteIfy(json.loads(self.comments(file_data)))
                    self.association(data)
                    json_file.close()
            return self.data
        if mode == 'read':
            with open(new_path, 'w+') as json_file:
                data = self.jsonDumps(self.data)
                json_file.write('%s' % data)
                json_file.close()
            return self.data

    def file_time(self):
        return datetime.datetime.fromtimestamp(os.stat('/'.join([self.path, self.appFile]))[8]).strftime('%H:%M:%S')

    def loadJson(self, name, path, mode='load'):
        new_path = '/'.join(['%s', '%s']) % (path, name)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isdir(path):
            if mode == 'load':
                if os.path.isfile(new_path):
                    try:
                        self.load(new_path)
                        print ('[%s]: Config file [%s] successfully loaded' % (self.ID, name))
                    except Exception as error:
                        print ('[%s]: Error: %s' % (self.ID, error))
                        print ('[%s]: Config file [%s] is not configured correctly' % (self.ID, name))
                        print ('[%s]: Loading of mod default config [%s]' % (self.ID, name.split('.')[0]))
                        return self.data
                else:
                    print ('[%s]: Config file [%s] not found, create a new' % (self.ID, name))
                    self.load(new_path, 'read')
                    print ('[%s]: Config file [%s] successfully created and loaded' % (self.ID, name))
                self.fileTime = self.file_time()
            elif mode == 'update':
                if os.path.isfile(new_path):
                    try:
                        self.load(new_path)
                        print ('[%s]: Config file [%s] successfully updated and loaded' % (self.ID, name))
                    except Exception as error:
                        print ('[%s]: Error: %s' % (self.ID, error))
                        print ('[%s]: Update failed, Config file [%s] is not configured correctly' % (self.ID, name))
                        print ('[%s]: Loading of mod default config [%s]' % (self.ID, name.split('.')[0]))
                        return self.data
                else:
                    print ('[%s]: Update failed, Config file [%s] not found, create a new' % (self.ID, name))
                    self.load(new_path, 'read')
                    print ('[%s]: Config file [%s] successfully created and loaded' % (self.ID, name))
            elif mode == 'read':
                try:
                    self.load(new_path, 'read')
                except Exception as error:
                    print('[%s]: Error: %s' % (self.ID, error))
                    print ('[%s]: Rewriting failed, Config file [%s] is not configured correctly' % (self.ID, name))
                    print ('[%s]: Loading of mod default config [%s]' % (self.ID, name.split('.')[0]))
                    return self.data

    def read_configs(self):
        self.loadJson(self.appFile, self.path, 'read')

    def update_configs(self):
        self.loadJson(self.appFile, self.path, 'update')

    # I18N
    def getLang(self):
        return self.i18n

    def i18nLoad_info(self):
        self.i18n_settings = ['/'.join([self.i18_path, self.i18n_file])]

    def i18nAssociation(self, data):
        for i in data:
            if type(data[i]) is dict and self.i18n.get(i):
                self.i18n[i].update(data[i])
            else:
                self.i18n[i] = data[i]

    def i18nLoad(self, new_path, mode='load'):
        if mode == 'load':
            for i18n in self.i18n_settings:
                with open(i18n, 'r') as json_file:
                    file_data = json_file.read().decode('utf-8-sig')
                    data = self.byteIfy(json.loads(self.comments(file_data)))
                    self.i18nAssociation(data)
                    json_file.close()
            return self.i18n
        if mode == 'read':
            with open(new_path, 'w+') as json_file:
                data = self.jsonDumps(self.i18n)
                json_file.write('%s' % data)
                json_file.close()
            return self.i18n

    def i18nFile_time(self):
        return datetime.datetime.fromtimestamp(os.stat('/'.join([self.i18_path, self.i18n_file]))[8]).strftime('%H:%M:%S')

    def i18nLoadJson(self, name, path, mode='load'):
        new_path = '/'.join(['%s', '%s']) % (path, name)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isdir(path):
            if mode == 'load':
                if os.path.isfile(new_path):
                    try:
                        self.i18nLoad(new_path)
                        print ('[%s]: Lang file [%s] successfully loaded' % (self.ID, name))
                        print ('-' * 74)
                    except Exception as error:
                        print ('[%s]: Error: %s' % (self.ID, error))
                        print ('[%s]: Lang File [%s] is not configured correctly' % (self.ID, name))
                        print ('[%s]: Loading of mod default lang [%s]' % (self.ID, name.split('.')[0]))
                        print ('-' * 74)
                        return self.i18n
                else:
                    print ('[%s]: Lang file [%s] not found, create a new' % (self.ID, name))
                    self.i18nLoad(new_path, 'read')
                    print ('[%s]: Lang file [%s] successfully created and loaded' % (self.ID, name))
                    print ('-' * 74)
                self.i18n_fileTime = self.i18nFile_time()
            elif mode == 'update':
                if os.path.isfile(new_path):
                    try:
                        self.i18nLoad(new_path)
                        print ('[%s]: Lang file [%s] successfully updated and loaded' % (self.ID, name))
                        print ('-' * 74)
                    except Exception as error:
                        print ('[%s]: Error: %s' % (self.ID, error))
                        print ('[%s]: Update failed, Lang file [%s] is not configured correctly' % (self.ID, name))
                        print ('[%s]: Loading of mod default lang [%s]' % (self.ID, name.split('.')[0]))
                        print ('-' * 74)
                        return self.i18n
                else:
                    print ('[%s]: Update failed, Lang file [%s] not found, create a new' % (self.ID, name))
                    self.i18nLoad(new_path, 'read')
                    print ('[%s]: Lang file [%s] successfully created and loaded' % (self.ID, name))
                    print ('-' * 74)
            elif mode == 'read':
                try:
                    self.i18nLoad(new_path, 'read')
                except Exception as error:
                    print('[%s]: Error: %s' % (self.ID, error))
                    print ('[%s]: Rewriting failed, Lang file [%s] is not configured correctly' % (self.ID, name))
                    print ('[%s]: Loading of mod default lang [%s]' % (self.ID, name.split('.')[0]))
                    print ('-' * 74)
                    return self.i18n

    def read_i18n(self):
        self.i18nLoadJson(self.i18n_file, self.i18_path, 'read')

    def update_i18n(self):
        self.i18nLoadJson(self.i18n_file, self.i18_path, 'update')

    def onApplySettings(self, settings):
        return NotImplementedError


class ConfigClass(Base):
    def __init__(self):
        self.ID = self.ID
        self.version = self.version
        self.author = self.author
        self.folder = self.ID
        self.path = '/'.join(['..', '..', '..', '..', '..', '..', 'res', 'configs', 'Driftkings', '%s']) % self.folder
        self.i18_path = '/'.join(['..', '..', '..', '..', '..', '..', 'res', 'configs', 'Driftkings', '%s', 'i18n']) % self.folder
        Base.__init__(self, self.ID, self.folder, self.path, self.i18_path, self.author)

    def onApplySettings(self, settings):
        try:
            print ('-' * 74)
            self.loadJson(name=self.ID, path=self.path, mode='write')
            print ('[%s]: Config file [%s] successfully updated' % (self.ID, settings))
            print ('-' * 74)
        except Exception as error:
            print ('-' * 74)
            print '[%s]: ERROR: %s' % self.ID, error
            print ('-' * 74)
