# -*- coding: utf-8 -*-
from flash import GUIFlash

GUI_FLASH_VERSION = '0.6.1b'
GUI_FLASH_AUTHOR = 'GambitER'
GUI_FLASH_FORKED = '(maintained by CHAMPi - fork: https://github.com/CH4MPi/GUIFlash)'
GUI_FLASH_NAMED = 'Driftkings'


def getVersion():
    return GUI_FLASH_VERSION, GUI_FLASH_AUTHOR, GUI_FLASH_FORKED, GUI_FLASH_NAMED


g_guiFlash = GUIFlash()

print 'GUIFlash v%s by %s initialized. %s.\nUpdated for %s' % getVersion()
