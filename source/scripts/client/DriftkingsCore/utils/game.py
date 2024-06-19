# -*- coding: utf-8 -*-
import BigWorld
import Keys

from functools import partial

__all__ = ('BigWorld_callback', 'sendPanelMessage', 'checkKeys', 'refreshCurrentVehicle', 'Sound',)


def BigWorld_callback(delay, func, *args, **kwargs):
    return BigWorld.callback(delay, partial(func, *args, **kwargs))


def checkKeys(keys, key=None):  # thx to P0LIR0ID
    keySets = [data if not isinstance(data, int) else (data,) for data in keys]
    return (bool(keys) and all(any(BigWorld.isKeyDown(item) for item in keySet) for keySet in keySets) and (key is None or any(key in keySet for keySet in keySets)))


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
    Args:
        text (str): The text of the message.
        colour (str): The color of the message. Default is 'Green'.
        panel (str): The panel to display the message in. Default is 'Player'.
    Returns:
        None
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
    # Import the necessary modules
    from gui.Scaleform.framework import WindowLayer
    from gui.shared.personality import ServicesLocator
    # Get the battle page
    battle_page = ServicesLocator.appLoader.getDefBattleApp().containerManager.getContainer(WindowLayer.VIEW).getView()
    # If the battle page is not None, show the message
    if battle_page is not None:
        # Get the method to show the message based on the panel and color
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
