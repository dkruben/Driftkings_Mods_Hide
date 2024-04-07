# -*- coding: utf-8 -*-
import traceback

from gui.shared.utils.TimeInterval import TimeInterval

from ._constants import MACROS, COMPARE_MACROS
from .configs import g_config
from .views import g_events
from .containers import DataConstants

from DriftkingsCore import getPlayer, getTarget, callback, cancelCallback


def _isEntitySatisfiesConditions(entity):
    if (entity is None) or not hasattr(entity, 'publicInfo'):
        return False
    enabledFor = g_config.data['showFor']
    isAlly = 0 < getattr(entity.publicInfo, 'team', 0) == getPlayer().team
    showFor = (enabledFor == 0) or ((enabledFor == 1) and isAlly) or ((enabledFor == 2) and not isAlly)
    aliveOnly = (not g_config.data['aliveOnly']) or (g_config.data['aliveOnly'] and entity.isAlive())
    return showFor and aliveOnly


class Flash(object):
    def __init__(self):
        self.texts = []
        self.callbacks = []
        self.isTextAdding = False
        self.isTextRemoving = False
        self.setup()
        g_events.onUpdatePosition += self.onUpdatePosition

    @property
    def currentConfig(self):
        return {
            'textPosition': g_config.data['textPosition'],
            'textShadow': g_config.data['textShadow'],
            'textLock': g_config.data['textLock'],
        }

    def onUpdatePosition(self, position):
        self.currentConfig['textPosition'] = position
        g_config.onApplySettings({'textPosition': position})

    def setup(self):
        self.texts = []

    @staticmethod
    def removeBox(idx):
        g_events.hide(idx)

    def addText(self, text):
        styleConf = g_config.data['textStyle']
        text = '<font size=\'%s\' face=\'%s\'><p align=\'%s\'>%s</p></font>' % (styleConf['size'], styleConf['font'], styleConf['align'], text)
        if len(self.texts):
            self.removeFirstText()
        self.texts.append(text)
        g_events.onUpdateUI(self.currentConfig, text)
        self.isTextAdding = True
        callback(0.5, self.onTextAddingComplete)
        self.callbacks.append(callback(g_config.data['delay'] + 0.5, self.removeFirstText))

    def onTextAddingComplete(self):
        self.isTextAdding = False

    def onTextRemovalComplete(self):
        self.isTextRemoving = False
        for idx in xrange(len(self.texts)):
            g_events.onUpdateUI(self.currentConfig, self.texts[idx])
        idx = len(self.texts)
        self.removeBox(idx)

    def removeFirstText(self):
        if self.texts:
            del self.texts[0]
        if self.callbacks:
            try:
                cancelCallback(self.callbacks[0])
            except ValueError:
                pass
            except StandardError:
                traceback.print_exc()
            del self.callbacks[0]
        self.isTextRemoving = True
        for idx in xrange(1, len(self.texts) + 1):
            g_events.onUpdateUI(self.currentConfig, idx)
        callback(0.5, self.onTextRemovalComplete)


g_flash = Flash()


class CompareMacros(object):
    def __init__(self):
        self.value1 = None
        self.value2 = None

    def reset(self):
        self.__init__()

    def setData(self, value1, value2):
        self.value1 = float(value1)
        self.value2 = float(value2)

    @property
    def compareDelim(self):
        if self.value1 > self.value2:
            return g_config.data['compareValues']['moreThan']['delim']
        elif self.value1 == self.value2:
            return g_config.data['compareValues']['equal']['delim']
        elif self.value1 < self.value2:
            return g_config.data['compareValues']['lessThan']['delim']

    @property
    def compareColor(self):
        if self.value1 > self.value2:
            return g_config.data['compareValues']['moreThan']['color']
        elif self.value1 == self.value2:
            return g_config.data['compareValues']['equal']['color']
        elif self.value1 < self.value2:
            return g_config.data['compareValues']['lessThan']['color']

    @property
    def isTarget(self):
        return '' if ((getTarget() is None) or g_mod.hotKeyDown) else 'trg'

    @property
    def isPremium(self):
        _typeDescriptor = getTarget().getVehicleAttached().typeDescriptor if ((getTarget() is None) or g_mod.hotKeyDown) else getTarget().typeDescriptor
        return 'premium' if ('premium' in _typeDescriptor.type.tags) else ''


g_macros = CompareMacros()


class InfoPanel(DataConstants):
    def __init__(self):
        self.textFormats = g_config.data['format'] if g_config.data['enabled'] else None
        self.hotKeyDown = False
        self.visible = False
        self.timer = None
        super(InfoPanel, self).__init__()

    def reset(self):
        self.__init__()
        g_macros.reset()

    def getFuncResponse(self, funcName):
        if not hasattr(self, funcName):
            return None
        func = getattr(self, funcName, None)
        if (func is not None) and callable(func):
            result = func()
            return str(result) if result is not None else ''
        else:
            return None

    def setTextsFormatted(self):
        textFormat = self.textFormats
        for macro in MACROS:
            if macro in textFormat:
                funcName = macro.replace('{', '').replace('}', '')
                funcResponse = self.getFuncResponse(funcName)
                textFormat = textFormat.replace(macro, funcResponse)
        for macro in COMPARE_MACROS:
            if macro in textFormat:
                reader = textFormat[textFormat.find(macro + '('):textFormat.find(')', textFormat.index(macro + '(') + 6) + 1]
                func = reader[:reader.find('(')]
                arg1 = reader[reader.find('(') + 1:reader.find(',')]
                arg2 = reader[reader.find(',') + 2:reader.find(')') - 2]
                g_macros.setData(arg1, arg2)
                funcRes = getattr(g_macros, func)
                textFormat = textFormat.replace('{{' + reader + '}}', str(funcRes))

        return textFormat

    def handleKey(self, isDown):
        if isDown:
            self.update(getPlayer().getVehicleAttached())
            self.hotKeyDown = True
        elif not isDown:
            self.hotKeyDown = False
            target = getTarget()
            if _isEntitySatisfiesConditions(target):
                self.update(target)
            else:
                self.hide()

    def hide(self):
        if self.timer is not None and self.timer.isStarted():
            self.timer.stop()
            self.timer = None
        self.visible = False

    def updateBlur(self):
        if self.hotKeyDown or (getPlayer().getVehicleAttached() is None):
            return
        else:
            if self.timer is not None and self.timer.isStarted():
                self.timer.stop()
                self.timer = None
        self.timer = TimeInterval(g_config.data['delay'], self, 'hide')
        self.timer.start()

    def update(self, vehicle):
        player = getPlayer()
        if self.hotKeyDown:
            return
        else:
            playerVehicle = player.getVehicleAttached()
            if playerVehicle is not None:
                self.visible = True
                if hasattr(vehicle, 'typeDescriptor'):
                    self.init(vehicle, playerVehicle)
                elif hasattr(playerVehicle, 'typeDescriptor'):
                    self.init(None, playerVehicle)

                g_flash.addText(self.setTextsFormatted())


g_mod = InfoPanel()
