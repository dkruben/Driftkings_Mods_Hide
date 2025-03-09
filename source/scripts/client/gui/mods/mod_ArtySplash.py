# -*- coding: utf-8 -*-
import BigWorld
import Keys
import Math
import VehicleGunRotator
from Avatar import PlayerAvatar
from AvatarInputHandler.aih_global_binding import CTRL_MODE_NAME
from gui import InputHandler
from gui.shared.gui_items import Vehicle
from gui.shared.gui_items.Vehicle import VEHICLE_CLASS_NAME

from DriftkingsCore import DriftkingsConfigInterface, override, Analytics, checkKeys, getPlayer, sendPanelMessage, logException, calculate_version
from DriftkingsInject.common.markers import StaticWorldObjectMarker3D


class ConfigInterface(DriftkingsConfigInterface):
    def __init__(self):
        super(ConfigInterface, self).__init__()
        if hasattr(BigWorld.Model, 'sacle') and not hasattr(BigWorld.Model, 'scale'):
            BigWorld.Model.scale = BigWorld.Model.sacle

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.5.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.defaultKeys = {
            'buttonShowDot': [Keys.KEY_C, [Keys.KEY_LALT, Keys.KEY_RALT]],
            'buttonShowSplash': [Keys.KEY_Z, [Keys.KEY_LALT, Keys.KEY_RALT]]
        }

        self.data = {
            'enabled': True,
            'buttonShowDot': self.defaultKeys['buttonShowDot'],
            'buttonShowSplash': self.defaultKeys['buttonShowSplash'],
            'showSplashOnDefault': True,
            'showDotOnDefault': True,
            'showModeArcade': False,
            'showModeSniper': True,
            'showModeArty': True,
            'modelPathSplash': 'objects/artySplash.model',
            'modelPathDot': 'objects/artyDot.model'
        }

        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_buttonShowDot_text': 'Button: show|hide Dot',
            'UI_setting_buttonShowDot_tooltip': '',
            'UI_setting_buttonShowSplash_text': 'Button: show|hide Splash',
            'UI_setting_buttonShowSplash_tooltip': '',
            'UI_setting_showSplashOnDefault_text': 'Show Splash on default',
            'UI_setting_showSplashOnDefault_tooltip': '',
            'UI_setting_showDotOnDefault_text': 'Show Dot on default',
            'UI_setting_showDotOnDefault_tooltip': '',
            'UI_setting_showModeArcade_text': 'Arcade mode available',
            'UI_setting_showModeArcade_tooltip': '',
            'UI_setting_showModeSniper_text': 'Sniper mode available',
            'UI_setting_showModeSniper_tooltip': '',
            'UI_setting_showModeArty_text': 'Arty mode available',
            'UI_setting_showModeArty_tooltip': '',
            'UI_artySplash_name': 'HE Splash',
            'UI_artySplash_messageSplashOn': 'HE Splash: Show Splash',
            'UI_artySplash_messageSplashOff': 'HE Splash: Hide Splash',
            'UI_artySplash_messageDotOn': 'HE Splash: Show Dot',
            'UI_artySplash_messageDotOff': 'HE Splash: Hide Dot'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('showSplashOnDefault'),
                self.tb.createControl('showDotOnDefault'),
                self.tb.createControl('showModeArcade'),
                self.tb.createControl('showModeSniper'),
                self.tb.createControl('showModeArty')],
            'column2': [
                self.tb.createHotKey('buttonShowSplash'),
                self.tb.createHotKey('buttonShowDot')
            ]
        }


class ArtyBall(object):
    def __init__(self):
        self.modelSplash = None
        self.modelDot = None
        self.modelSplashCircle = None
        self.modelSplashVisible = False
        self.modelDotVisible = False
        self.modelSplashKeyPressed = False
        self.modelDotKeyPressed = False
        self.scaleSplash = None
        self.player = None

    def startBattle(self):
        InputHandler.g_instance.onKeyDown += self.injectButton
        if config.data['enabled']:
            self.player = getPlayer()
            self.modelSplashVisible = config.data['showSplashOnDefault']
            self.modelDotVisible = config.data['showDotOnDefault']
            self.scaleSplash = None
            self.modelSplash = StaticWorldObjectMarker3D({'path': config.data['modelPathSplash']}, (0, 0, 0))
            self.modelDot = StaticWorldObjectMarker3D({'path': config.data['modelPathDot']}, (0, 0, 0))
            self.modelDot.model.scale = (0.1, 0.1, 0.1)
            if Vehicle.getVehicleClassTag(self.player.vehicleTypeDescriptor.type.tags) == VEHICLE_CLASS_NAME.SPG:
                self.modelDot.model.scale = (0.5, 0.5, 0.5)
            self.modelSplash.model.visible = False
            self.modelDot.model.visible = False
            self.modelSplashCircle = BigWorld.PyTerrainSelectedArea()
            self.modelSplashCircle.setup('content/Interface/CheckPoint/CheckPoint_yellow_black.model', Math.Vector2(2.0, 2.0), 0.5, 4294967295L, BigWorld.player().spaceID) # old
            self.modelSplash.model.root.attach(self.modelSplashCircle)
            self.modelSplashCircle.enableAccurateCollision(False)

    def stopBattle(self):
        InputHandler.g_instance.onKeyDown -= self.injectButton
        self.modelSplashVisible = False
        self.modelDotVisible = False
        self.modelSplashKeyPressed = False
        self.modelDotKeyPressed = False
        if self.modelSplash is not None:
            if self.modelSplashCircle.attached:
                self.modelSplash.model.root.detach(self.modelSplashCircle)
            self.modelSplash.clear()
        if self.modelDot is not None:
            self.modelDot.clear()
        self.modelSplash = None
        self.modelDot = None
        self.scaleSplash = None
        self.modelSplashCircle = None

    def working(self):
        if not config.data['enabled'] or self.player is None:
            self.hideVisible()
            return
        if not hasattr(self.player, 'vehicleTypeDescriptor') or not hasattr(self.player, 'gunRotator'):
            self.hideVisible()
            return
        if Vehicle.getVehicleClassTag(self.player.getVehicleDescriptor().type.tags) != VEHICLE_CLASS_NAME.SPG:
            self.hideVisible()
            return
        shell = self.player.getVehicleDescriptor().shot.shell
        if 'HIGH_EXPLOSIVE' not in shell.kind:
            self.hideVisible()
            return
        if not config.data['showModeArcade'] and self.player.inputHandler.ctrlModeName == CTRL_MODE_NAME.ARCADE:
            self.hideVisible()
            return
        if not config.data['showModeSniper'] and self.player.inputHandler.ctrlModeName == CTRL_MODE_NAME.SNIPER:
            self.hideVisible()
            return
        if not config.data['showModeArty'] and self.player.inputHandler.ctrlModeName in [CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.ARTY]:
            self.hideVisible()
            return

        if self.modelSplash is not None and self.modelSplash.model:
            if not self.scaleSplash or self.scaleSplash != shell.type.explosionRadius:
                self.scaleSplash = shell.type.explosionRadius
                self.modelSplash.model.scale = (self.scaleSplash, self.scaleSplash, self.scaleSplash)
            if not self.modelSplashKeyPressed:
                self.modelSplashVisible = config.data['showSplashOnDefault']
            self.modelSplash.model.position = self.player.gunRotator.markerInfo[0]
            self.modelSplashCircle.updateHeights()
        if self.modelDot is not None and self.modelDot.model:
            if not self.modelDotKeyPressed:
                self.modelDotVisible = config.data['showDotOnDefault']
            self.modelDot.model.position = self.player.gunRotator.markerInfo[0]
        self.setVisible()

    def setVisible(self):
        if self.modelSplash is not None and self.modelSplash.model:
            if self.modelSplash.model.visible != self.modelSplashVisible:
                self.modelSplash.model.visible = self.modelSplashVisible
        if self.modelDot is not None and self.modelDot.model:
            if self.modelDot.model.visible != self.modelDotVisible:
                self.modelDot.model.visible = self.modelDotVisible

    def hideVisible(self):
        if self.modelSplash is not None and self.modelSplash.model and self.modelSplash.model.visible:
            self.modelSplash.model.visible = False
        if self.modelDot is not None and self.modelDot.model and self.modelDot.model.visible:
            self.modelDot.model.visible = False

    @logException
    def injectButton(self, event):
        if checkKeys(config.data['buttonShowSplash']) and event.isKeyDown():
            self.modelSplashKeyPressed = True
            self.modelSplashVisible = not self.modelSplashVisible
            sendPanelMessage(config.i18n['UI_artySplash_messageSplashOn'] if self.modelSplashVisible else config.i18n['UI_artySplash_messageSplashOff'], 'Green' if self.modelSplashVisible else 'Red')
            self.setVisible()

        if checkKeys(config.data['buttonShowDot']) and event.isKeyDown():
            self.modelDotKeyPressed = True
            self.modelDotVisible = not self.modelDotVisible
            sendPanelMessage(config.i18n['UI_artySplash_messageDotOn'] if self.modelDotVisible else config.i18n['UI_artySplash_messageDotOff'], 'Green' if self.modelDotVisible else 'Red')
            self.setVisible()


config = ConfigInterface()
artySplash = ArtyBall()
analytics = Analytics(config.ID, config.version, 'G-B7Z425MJ3L')


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    artySplash.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    artySplash.stopBattle()


@override(VehicleGunRotator.VehicleGunRotator, '_VehicleGunRotator__updateGunMarker')
def new_updateMarkerPos(func, *args):
    func(*args)
    artySplash.working()
