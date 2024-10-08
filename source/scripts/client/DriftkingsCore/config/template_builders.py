# -*- coding: utf-8 -*-
import copy


class CONTAINER(object):
    CheckBox = 'CheckBox'
    Label = 'Label'
    ColorChoice = 'ColorChoice'
    TextInput = 'TextInput'
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


class DummyTemplateBuilder(object):
    types = CONTAINER

    def __init__(self, i18n):
        self.i18n = i18n
        self._blockID = None

    def __call__(self, blockID):
        self._blockID = blockID
        return self

    def getValue(self, var_name, value):
        return var_name

    @staticmethod
    def createEmpty():
        return {'type': 'Empty'}

    def getLabel(self, var_name, ctx='setting'):
        return self.i18n['UI_%s_%s_text' % (ctx, var_name)]

    def createTooltip(self, var_name, ctx='setting'):
        tooltip_key = 'UI_%s_%s_tooltip' % (ctx, var_name)
        if self.i18n.get(tooltip_key, ''):
            return '{HEADER}%s{/HEADER}{BODY}%s{/BODY}' % tuple(self.i18n['UI_%s_%s_%s' % (ctx, var_name, strType)] for strType in ('text', 'tooltip'))
        return ''

    def createLabel(self, var_name, ctx='setting'):
        if self._blockID is not None:
            var_name = self._blockID + '_' + var_name
        return {'type': 'Label', 'text': self.getLabel(var_name, ctx), 'tooltip': self.createTooltip(var_name, ctx)}

    def createControl(self, var_name, cont_type=CONTAINER.CheckBox, width=200, empty=False, button=None, value=None):
        result = self.createLabel(var_name) if not empty else {}
        result.update({'type': cont_type, 'value': self.getValue(var_name, value), 'varName': var_name, 'width': width})
        if button is not None:
            result['button'] = button
        return result

    def createOptions(self, var_name, options, cont_type=CONTAINER.Dropdown, width=200, empty=False, button=None, value=None):
        result = self.createControl(var_name, cont_type, width, empty, button, value)
        result['options'] = [{'label': x} for x in options]
        return result

    def createImageOptions(self, var_name, icons, cont_type=CONTAINER.Dropdown, width=200, empty=False, button=None, value=None):
        result = self.createControl(var_name, cont_type, width, empty, button, value)
        if result is not None:
            image = '<img src=\'img://gui/maps/icons/SixthSense/{}\' width=\'180\' height=\'180\'>'
            result['options'] = [{'label': x[:-4], 'tooltip': makeTooltip(body=image.format(x))} for x in icons]
        return result

    def createHotKey(self, var_name, empty=False, value=None):
        return self.createControl(var_name, CONTAINER.HotKey, empty=empty, value=value)

    def _createNumeric(self, var_name, cont_type, step, v_min=0, v_max=0, width=200, empty=False, button=None, value=None):
        result = self.createControl(var_name, cont_type, width, empty, button, value)
        result.update({'minimum': v_min, 'maximum': v_max, 'snapInterval': step})
        return result

    def createStepper(self, var_name, v_min, v_max, step, manual=False, width=200, empty=False, button=None, value=None):
        result = self._createNumeric(var_name, CONTAINER.NumericStepper, step, v_min, v_max, width, empty, button, value)
        result['canManualInput'] = manual
        return result

    def createSlider(self, var_name, v_min, v_max, step, format_str='{{value}}', width=200, empty=False, button=None, value=None):
        result = self._createNumeric(var_name, CONTAINER.Slider, step, v_min, v_max, width, empty, button, value)
        result['format'] = format_str
        return result

    def createRangeSlider(self, var_name, v_min, v_max, label_step, div_step, step, min_range, width=200, empty=False, button=None, value=None):
        result = self._createNumeric(var_name, CONTAINER.RangeSlider, step, v_min, v_max, width, empty, button, value)
        result.update({'divisionLabelStep': label_step, 'divisionStep': div_step, 'minRangeDistance': min_range})
        return result

    def createItem(self, var_name, list_steps, width=200):
        result = self.createControl(var_name, CONTAINER.TextInput, width)
        result['value'] = ', '.join(str(x) for x in list_steps)
        return result

class TemplateBuilder(DummyTemplateBuilder):
    def __init__(self, data, i18n):
        super(TemplateBuilder, self).__init__(i18n)
        self.data = copy.deepcopy(data)

    def getValue(self, var_name, value):
        return value if value is not None else (self.data[var_name] if self._blockID is None else self.data[self._blockID][var_name])
