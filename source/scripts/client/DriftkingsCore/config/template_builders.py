# -*- coding: utf-8 -*-
# import copy


class CONTAINER(object):
    CheckBox = 'CheckBox'
    Label = 'Label'
    ColorChoice = 'TextInputColor'  # 'ColorChoice'
    TextInput = 'TextInputField'  # 'TextInput'
    Dropdown = 'Dropdown'
    RadioButtonGroup = 'RadioButtonGroup'
    HotKey = 'HotKey'
    NumericStepper = 'NumericStepper'
    Slider = 'Slider'
    RangeSlider = 'RangeSlider'


def makeTooltip(header=None, body=None, note=None, attention=None):
    res_str = ''
    if header is not None:
        res_str += '{HEADER}%s{/HEADER}' % header
    if body is not None:
        res_str += '{BODY}%s{/BODY}' % body
    if note is not None:
        res_str += '{NOTE}%s{/NOTE}' % note
    if attention is not None:
        res_str += '{ATTENTION}%s{/ATTENTION}' % attention
    return res_str


# class DummyTemplateBuilder(object):
#    types = CONTAINER

#    def __init__(self, i18n):
#        self.i18n = i18n
#        self._blockID = None

#    def __call__(self, blockID):
#        self._blockID = blockID
#        return self

#    def getValue(self, varName, value):
#        return value

#    @staticmethod
#    def createEmpty():
#        return {'type': 'Empty'}

#    def getLabel(self, varName, ctx='setting'):
#        return self.i18n['UI_%s_%s_text' % (ctx, varName)]

#    def createTooltip(self, varName, ctx='setting'):
#        return ('{HEADER}%s{/HEADER}{BODY}%s{/BODY}' % tuple(self.i18n['UI_%s_%s_%s' % (ctx, varName, strType)] for strType in ('text', 'tooltip'))) if self.i18n.get('UI_%s_%s_tooltip' % (ctx, varName), '') else ''

#    def createLabel(self, varName, ctx='setting'):
#        if self._blockID is not None:
#            varName = self._blockID + '_' + varName
#        return {'type': 'Label', 'text': self.getLabel(varName, ctx), 'tooltip': self.createTooltip(varName, ctx)}

#    def createControl(self, varName, contType=CONTAINER.CheckBox, width=200, empty=False, button=None, value=None):
#        result = self.createLabel(varName) if not empty else {}  # contType: 'ColorChoice', 'TextInput'
#        result.update({'type': contType, 'value': self.getValue(varName, value), 'varName': varName, 'width': width})
#        if button is not None:
#            result['button'] = button
#        return result

#    def createOptions(self, varName, options, contType=CONTAINER.Dropdown, width=200, empty=False, button=None, value=None):
#        result = self.createControl(varName, contType, width, empty, button, value)  # contType: 'RadioButtonGroup'
#        result['options'] = [{'label': x} for x in options]
#        return result

#    def createImageOptions(self, varName, field, optionsIcon, contType=CONTAINER.Dropdown, width=190, empty=False, button=None, value=None):
#        result = self.createControl(varName, contType, width, empty, button, value)
#        if result is not None:
#            image = '<img src=\'img://%s/{}\' width=\'180\' height=\'180\'>' % field
#            result['options'] = [{'label': x[:-4], 'tooltip': makeTooltip(body=image.format(x))} for x in optionsIcon]
#        return result

#    def createHotKey(self, varName, empty=False, value=None):
#        result = self.createControl(varName, CONTAINER.HotKey, empty=empty, value=value)
#        return result

#    def _createNumeric(self, varName, contType, step, vMin=0, vMax=0, width=200, empty=False, button=None, value=None):
#        result = self.createControl(varName, contType, width, empty, button, value)
#        result.update({'minimum': vMin, 'maximum': vMax, 'snapInterval': step})
#        return result

#    def createStepper(self, varName, vMin, vMax, step, manual=False, width=200, empty=False, button=None, value=None):
#        result = self._createNumeric(varName, CONTAINER.NumericStepper, step, vMin, vMax, width, empty, button, value)
#        result['canManualInput'] = manual
#        return result

#    def createSlider(self, varName, vMin, vMax, step, formatStr='{{value}}', width=200, empty=False, button=None, value=None):
#        result = self._createNumeric(varName, CONTAINER.Slider, step, vMin, vMax, width, empty, button, value)
#        result['format'] = formatStr
#        return result

#    def createRangeSlider(self, varName, vMin, vMax, labelStep, divStep, step, minRange, width=200, empty=False, button=None, value=None):
#        result = self._createNumeric(varName, CONTAINER.RangeSlider, step, vMin, vMax, width, empty, button, value)
#        result.update({'divisionLabelStep': labelStep, 'divisionStep': divStep, 'minRangeDistance': minRange})
#        return result


# class TemplateBuilder(DummyTemplateBuilder):
#    def __init__(self, data, i18n):
#        super(TemplateBuilder, self).__init__(i18n)
#        self.data = copy.deepcopy(data)
#
#    def getValue(self, varName, value):
#        return value if value is not None else (self.data[varName] if self._blockID is None else self.data[self._blockID][varName])


# VX

class Getter(object):
    __slots__ = ()

    @staticmethod
    def getLinkToParam(settings_block, settingPath):
        path = settingPath.split('*')
        for fragment in path:
            if fragment in settings_block and isinstance(settings_block[fragment], dict):
                settings_block = settings_block[fragment]
        return settings_block, path[-1]

    @staticmethod
    def getCollectionIndex(value, collection):
        index = 0
        if value in collection:
            index = collection.index(value)
        return collection, index

    def getKeyPath(self, settings_block, path=()):
        for key, value in settings_block.iteritems():
            key_path = path + (key,)
            if isinstance(value, dict):
                for _path in self.getKeyPath(value, key_path):
                    yield _path
            else:
                yield key_path


class DummyTemplateBuilder(object):
    types = CONTAINER
    getter = Getter()

    def __init__(self, i18n):
        self.i18n = i18n

    @staticmethod
    def createEmpty():
        return {'type': 'Empty'}

    def getLabel(self, varName, ctx='setting'):
        return self.i18n['UI_%s_%s_text' % (ctx, varName)]

    def createTooltip(self, varName, ctx='setting'):
        return ('{HEADER}%s{/HEADER}{BODY}%s{/BODY}' % tuple(self.i18n['UI_%s_%s_%s' % (ctx, varName, strType)] for strType in ('text', 'tooltip'))) if self.i18n.get('UI_%s_%s_tooltip' % (ctx, varName), '') else ''

    def createLabel(self, varName, ctx='setting'):
        return {'type': 'Label', 'text': self.getLabel(varName, ctx), 'tooltip': self.createTooltip(varName, ctx), 'label': self.getLabel(varName, ctx)}  # because Stepper needs label instead of text

    def createControl(self, varName, value, contType=CONTAINER.CheckBox, width=200, empty=False, button=None):
        result = self.createLabel(varName) if not empty else {}
        result.update({'type': contType, 'value': value, 'varName': varName, 'width': width})
        if button is not None:
            result['button'] = button
        return result

    def createOptions(self, varName, options, value, contType=CONTAINER.Dropdown, width=200, empty=False, button=None):
        result = self.createControl(varName, value, contType, width, empty, button)
        result.update({'width': width, 'itemRenderer': 'DropDownListItemRendererSound', 'options': [{'label': x} for x in options]})
        return result

    def createImageOptions(self, varName, icons, icon):
        result = self.createControl(varName, icon, contType=CONTAINER.Dropdown)
        if result is not None:
            image = '<img src=\'img://gui/maps/icons/SixthSense/{}\' width=\'180\' height=\'180\'>'
            result.update({'itemRenderer': 'DropDownListItemRendererSound', 'options': [{'label': x[:-4], 'tooltip': makeTooltip(body=image.format(x))} for x in icons], 'width': 180})
        return result

    def createHotKey(self, varName, value, defaultValue, empty=False):
        result = self.createControl(varName, value, 'HotKey', empty=empty)
        result['defaultValue'] = defaultValue
        return result

    def _createNumeric(self, varName, contType, value, vMin=0, vMax=0, width=200, empty=False, button=None):
        result = self.createControl(varName, value, contType, width, empty, button)
        result.update({'minimum': vMin, 'maximum': vMax})
        return result

    def createStepper(self, varName, vMin, vMax, step, value, manual=False, width=200, empty=False, button=None):
        result = self._createNumeric(varName, 'NumericStepper', value, vMin, vMax, width, empty, button)
        result.update({'stepSize': step, 'canManualInput': manual})
        return result

    def createSlider(self, varName, vMin, vMax, step, value, formatStr='{{value}}', width=200, empty=False, button=None):
        result = self._createNumeric(varName, 'Slider', value, vMin, vMax, width, empty, button)
        result.update({'snapInterval': step, 'format': formatStr})
        return result

    def createRangeSlider(self, varName, vMin, vMax, labelStep, divStep, step, minRange, value, width=200, empty=False, button=None):
        result = self._createNumeric(varName, 'RangeSlider', value, vMin, vMax, width, empty, button)
        result.update({'snapInterval': step, 'divisionLabelStep': labelStep, 'divisionStep': divStep, 'minRangeDistance': minRange})
        return result


class TemplateBuilder(object):
    types = CONTAINER
    getter = Getter()

    def __init__(self, data, i18n, defaultKeys):
        self.dummy = DummyTemplateBuilder(i18n)
        self.data = data
        self.defaultKeys = defaultKeys

    def createEmpty(self):
        return self.dummy.createEmpty()

    def getLabel(self, varName, ctx='setting'):
        return self.dummy.getLabel(varName, ctx)

    def createLabel(self, varName, ctx='setting'):
        return self.dummy.createLabel(varName, ctx)

    def createTooltip(self, varName, ctx='setting'):
        return self.dummy.createTooltip(varName, ctx)

    def createControl(self, varName, contType=CONTAINER.CheckBox, width=200, empty=False, button=None):
        return self.dummy.createControl(varName, self.data[varName], contType, width, empty, button)

    def createOptions(self, varName, options, contType=CONTAINER.Dropdown, width=200, empty=False, button=None):
        return self.dummy.createOptions(varName, options, self.data[varName], contType, width, empty, button)

    def createImageOptions(self, varName, icons):
        return self.dummy.createImageOptions(varName, icons, icon=None)

    def createHotKey(self, varName, empty=False):
        return self.dummy.createHotKey(varName, self.data[varName], self.defaultKeys[varName], empty)

    def _createNumeric(self, varName, contType, vMin=0, vMax=0, width=200, empty=False, button=None):
        return self.dummy._createNumeric(varName, contType, self.data[varName], vMin, vMax, width, empty, button)

    def createStepper(self, varName, vMin, vMax, step, manual=False, width=200, empty=False, button=None):
        return self.dummy.createStepper(varName, vMin, vMax, step, self.data[varName], manual, width, empty, button)

    def createSlider(self, varName, vMin, vMax, step, formatStr='{{value}}', width=200, empty=False, button=None):
        return self.dummy.createSlider(varName, vMin, vMax, step, self.data[varName], formatStr, width, empty, button)

    def createRangeSlider(self, varName, vMin, vMax, labelStep, divStep, step, minRange, width=200, empty=False, button=None):
        return self.dummy.createRangeSlider(varName, vMin, vMax, labelStep, divStep, step, minRange, self.data[varName], width, empty, button)


# noinspection PyMethodOverriding
class DummyBlockTemplateBuilder(DummyTemplateBuilder):
    types = CONTAINER

    def __init__(self, i18n):
        super(DummyBlockTemplateBuilder, self).__init__(i18n)
        self.dummy = DummyTemplateBuilder(i18n)

    def createLabel(self, blockID, varName, ctx='setting'):
        return self.dummy.createLabel(blockID + '_' + varName, ctx)

    def createControl(self, blockID, varName, value, contType=CONTAINER.CheckBox, width=200, empty=False, button=None):
        result = self.createLabel(blockID, varName) if not empty else {}
        result.update(self.dummy.createControl(varName, value, contType, width, True, button))
        return result

    def createOptions(self, blockID, varName, options, value, contType=CONTAINER.Dropdown, width=200, empty=False, button=None):
        result = self.createLabel(blockID, varName) if not empty else {}
        result.update(self.dummy.createOptions(varName, options, value, contType, width, True, button))
        return result

    def createHotKey(self, blockID, varName, value, defaultValue, empty=False):
        result = self.createLabel(blockID, varName) if not empty else {}
        result.update(self.dummy.createHotKey(varName, value, defaultValue, True))
        return result

    def _createNumeric(self, blockID, varName, contType, value, vMin=0, vMax=0, width=200, empty=False, button=None):
        result = self.createLabel(blockID, varName) if not empty else {}
        result.update(self.dummy._createNumeric(varName, contType, value, vMin, vMax, width, True, button))
        return result

    def createStepper(self, blockID, varName, vMin, vMax, step, value, manual=False, width=200, empty=False, button=None):
        result = self.createLabel(blockID, varName) if not empty else {}
        result.update(self.dummy.createStepper(varName, vMin, vMax, step, value, manual, width, True, button))
        return result

    def createSlider(self, blockID, varName, vMin, vMax, step, value, formatStr='{{value}}', width=200, empty=False, button=None):
        result = self.createLabel(blockID, varName) if not empty else {}
        result.update(self.dummy.createSlider(varName, vMin, vMax, step, value, formatStr, width, True, button))
        return result

    def createRangeSlider(self, blockID, varName, vMin, vMax, labelStep, divStep, step, minRange, value, width=200, empty=False, button=None):
        result = self.createLabel(blockID, varName) if not empty else {}
        result.update(self.dummy.createRangeSlider(varName, vMin, vMax, labelStep, divStep, step, minRange, value, width, True, button))
        return result


# noinspection PyMethodOverriding
class BlockTemplateBuilder(object):
    types = CONTAINER

    def __init__(self, data, i18n, defaultKeys):
        self.dummy = DummyBlockTemplateBuilder(i18n)
        self.data = data
        self.defaultKeys = defaultKeys

    def createEmpty(self):
        return self.dummy.createEmpty()

    def getLabel(self, varName, ctx='setting'):
        return self.dummy.getLabel(varName, ctx)

    def createLabel(self, varName, ctx='setting'):
        return self.dummy.createLabel(varName, ctx)

    def createTooltip(self, varName, ctx='setting'):
        return self.dummy.createTooltip(varName, ctx)

    def createControl(self, blockID, varName, contType=CONTAINER.CheckBox, width=200, empty=False, button=None):
        return self.dummy.createControl(blockID, varName, self.data[blockID][varName], contType, width, empty, button)

    def createOptions(self, blockID, varName, options, contType=CONTAINER.Dropdown, width=200, empty=False, button=None):
        return self.dummy.createOptions(blockID, varName, options, self.data[blockID][varName], contType, width, empty, button)

    def createHotKey(self, blockID, varName, empty=False):
        return self.dummy.createHotKey(blockID, varName, self.data[blockID][varName], self.defaultKeys[varName], empty)

    def _createNumeric(self, blockID, varName, contType, vMin=0, vMax=0, width=200, empty=False, button=None):
        return self.dummy._createNumeric(blockID, varName, contType, self.data[blockID][varName], vMin, vMax, width, empty, button)

    def createStepper(self, blockID, varName, vMin, vMax, step, manual=False, width=200, empty=False, button=None):
        return self.dummy.createStepper(blockID, varName, vMin, vMax, step, self.data[blockID][varName], manual, width, empty, button)

    def createSlider(self, blockID, varName, vMin, vMax, step, formatStr='{{value}}', width=200, empty=False, button=None):
        return self.dummy.createSlider(blockID, varName, vMin, vMax, step, self.data[blockID][varName], formatStr, width, empty, button)

    def createRangeSlider(self, blockID, varName, vMin, vMax, labelStep, divStep, step, minRange, width=200, empty=False, button=None):
        return self.dummy.createRangeSlider(blockID, varName, vMin, vMax, labelStep, divStep, step, minRange, self.data[blockID][varName], width, empty, button)
