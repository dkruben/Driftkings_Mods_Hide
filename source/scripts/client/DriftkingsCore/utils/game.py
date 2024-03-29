# -*- coding: utf-8 -*-
import BigWorld
import Keys

from functools import partial

__all__ = ('BigWorld_callback', 'sendPanelMessage', 'checkKeys', 'refreshCurrentVehicle', 'Sound', 'checkKeySet',)


def BigWorld_callback(delay, func, *a, **k):
    return BigWorld.callback(delay, partial(func, *a, **k))


def checkKeys(keys, key=None):  # thx to P0LIR0ID
    keySets = [data if not isinstance(data, int) else (data,) for data in keys]
    return (bool(keys) and all(any(BigWorld.isKeyDown(item) for item in keySet) for keySet in keySets) and (key is None or any(key in keySet for keySet in keySets)))


VKEY_ALT, VKEY_CONTROL, VKEY_SHIFT = range(-1, -4, -1)
VKEYS_MAP = {
    VKEY_ALT: (Keys.KEY_LALT, Keys.KEY_RALT),
    VKEY_CONTROL: (Keys.KEY_LCONTROL, Keys.KEY_RCONTROL),
    VKEY_SHIFT: (Keys.KEY_LSHIFT, Keys.KEY_RSHIFT),
}


def checkKeySet(keys, keyCode=None):
    """Verify is keys is pressed
    :param keys: list of keys to be checked
    :param keyCode: pressed keyCode"""
    result, fromSet = True, False
    if not keys:
        result = False
    for key in keys:
        if isinstance(key, int):
            # virtual special keys
            if key in (VKEY_ALT, VKEY_CONTROL, VKEY_SHIFT):
                result &= any(map(BigWorld.isKeyDown, VKEYS_MAP[key]))
                fromSet |= keyCode in VKEYS_MAP[key]
            # BW Keys
            elif not BigWorld.isKeyDown(key):
                result = False
                fromSet |= keyCode == key
        # old special keys
        if isinstance(key, list):
            result &= any(map(BigWorld.isKeyDown, key))
            fromSet |= keyCode in key
        if keyCode is not None:
            return result, fromSet
        return result


def _checkKeySet(keySet):
    """Verify is keys is pressed
    :param keySet: list of keys to be checked"""
    result = True
    if not keySet:
        result = False
    for item in keySet:
        if isinstance(item, int) and not BigWorld.isKeyDown(item):
            result = False
        if isinstance(item, list):
            result = result and any(map(BigWorld.isKeyDown, item))
    return result


def refreshCurrentVehicle():
    from CurrentVehicle import g_currentPreviewVehicle, g_currentVehicle
    if g_currentPreviewVehicle.item:
        from gui.shared.personality import ServicesLocator as SL
        outfit = None
        entity = SL.hangarSpace.getVehicleEntity()
        if entity and entity.appearance:
            outfit = entity.appearance.outfit
        g_currentPreviewVehicle.hangarSpace.updatePreviewVehicle(g_currentPreviewVehicle.item, outfit)
    else:
        g_currentVehicle.refreshModel()
    from HeroTank import HeroTank
    for entity in HeroTank.allCameraObjects:
        if isinstance(entity, HeroTank):
            entity.recreateVehicle()


def sendPanelMessage(text='', colour='Green', panel='Player'):
    from gui.Scaleform.framework import WindowLayer
    from gui.shared.personality import ServicesLocator
    """
    panel = 'Player', 'Vehicle', 'VehicleError'
    colour = 'Red', 'Purple', 'Green', 'Gold', 'Yellow', 'Self'
    """
    battle_page = ServicesLocator.appLoader.getDefBattleApp().containerManager.getContainer(WindowLayer.VIEW).getView()
    if battle_page is not None:
        getattr(battle_page.components['battle%sMessages' % panel], 'as_show%sMessageS' % colour, None)(None, text)
    else:
        BigWorld.callback(0.5, partial(sendPanelMessage, text, colour, panel))


class Sound(object):
    def __init__(self, soundPath):
        import SoundGroups
        self.__sndPath = soundPath
        self.__sndTick = SoundGroups.g_instance.getSound2D(self.__sndPath)
        self.__isPlaying = True
        self.stop()

    @property
    def isPlaying(self):
        return self.__isPlaying

    @property
    def sound(self):
        return self.__sndTick

    def play(self):
        self.stop()
        if self.__sndTick:
            self.__sndTick.play()
        self.__isPlaying = True

    def stop(self):
        if self.__sndTick:
            self.__sndTick.stop()
        self.__isPlaying = False
