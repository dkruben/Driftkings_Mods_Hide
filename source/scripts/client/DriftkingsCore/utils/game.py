# -*- coding: utf-8 -*-
import BigWorld
import Keys

from functools import partial

__all__ = ('BigWorld_callback', 'sendPanelMessage', 'checkKeys', 'refreshCurrentVehicle', 'Sound',)


def BigWorld_callback(delay, func, *args, **kwargs):
    return BigWorld.callback(delay, partial(func, *args, **kwargs))


def checkKeys(keys, key=None):
    if not keys:
        return False
    keySets = [data if isinstance(data, tuple) else (data,) for data in keys]
    keys_pressed = any(any(BigWorld.isKeyDown(item) for item in keySet) for keySet in keySets)
    if key is not None:
        key_found = any(key in keySet for keySet in keySets)
        return keys_pressed and key_found
    return keys_pressed


VKEY_ALT, VKEY_CONTROL, VKEY_SHIFT = range(-1, -4, -1)
VKEYS_MAP = {
    VKEY_ALT: (Keys.KEY_LALT, Keys.KEY_RALT),
    VKEY_CONTROL: (Keys.KEY_LCONTROL, Keys.KEY_RCONTROL),
    VKEY_SHIFT: (Keys.KEY_LSHIFT, Keys.KEY_RSHIFT),
}


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
    """
    This function sends a message to the specified panel in the game interface.
    :param text: The text of the message.
    :param colour: The color of the message. Default is 'Green'.
    :param panel: The panel to display the message in. Default is 'Player'.
    :return: None
    The panel can be one of the following:
        - 'Player': The player's message panel.
        - 'Vehicle': The vehicle's message panel.
        - 'VehicleError': The vehicle error message panel.
    The colour can be one of the following:
        - 'Red': Red color.
        - 'Purple': Purple color.
        - 'Green': Green color.
        - 'Gold': Gold color.
        - 'Yellow': Yellow color.
        - 'Self': Self color.
    """
    from gui.Scaleform.framework import WindowLayer
    from gui.shared.personality import ServicesLocator
    battle_page = ServicesLocator.appLoader.getDefBattleApp().containerManager.getContainer(WindowLayer.VIEW).getView()
    if battle_page is not None:
        getattr(battle_page.components['battle%sMessages' % panel], 'as_show%sMessageS' % colour, None)(None, text)
    else:
        BigWorld.callback(0.5, partial(sendPanelMessage, text, colour, panel))


class Sound(object):
    def __init__(self, sound_path):
        import SoundGroups
        self.__sndPath = sound_path
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
