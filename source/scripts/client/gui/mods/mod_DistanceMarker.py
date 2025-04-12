# -*- coding: utf-8 -*-
import BigWorld
import GUI
import Keys
import Math
import SCALEFORM
from AvatarInputHandler import AvatarInputHandler
from Event import EventManager, Event
from gui import DEPTH_OF_VehicleMarker, InputHandler
from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin
from gui.Scaleform.daapi.view.external_components import ExternalFlashComponent, ExternalFlashSettings
from gui.Scaleform.flash_wrapper import InputKeyMode
from gui.Scaleform.framework.entities.BaseDAAPIModule import BaseDAAPIModule

from DriftkingsCore import DriftkingsConfigInterface, calculate_version, override, logError, logWarning, Analytics

g_distanceMarkerFlash = None


class ConfigInterface(DriftkingsConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.0 (%(file_compile_date)s)'
        self.author = 'Maintenance by: _DKRuben_EU'
        self.data = {
            'enabled': True,
            'displayMode': 0,
            'markerTarget': 1,
            'anchorPosition': 0,
            'lockPositionOffsets': False,
            'anchorHorizontalOffset': 24,
            'anchorVerticalOffset': 16,
            'decimalPrecision': 0,
            'textSize': 11,
            'textColor': 'FFFFFF',
            'textAlpha': 1.0,
            'drawTextShadow': True
        }
        self.i18n = {
            'modDisplayName': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_displayMode_text': 'Display Mode',
            'UI_setting_displayMode_tooltip': 'Defines when the distance marker will be displayed',
            'UI_setting_markerTarget_text': 'Marker Targets',
            'UI_setting_markerTarget_tooltip': 'Defines which vehicles will receive the distance marker',
            'UI_setting_anchorPosition_text': 'Anchor Position',
            'UI_setting_anchorPosition_tooltip': 'Defines where the marker will be positioned relative to the vehicle',
            'UI_setting_lockPositionOffsets_text': 'Lock Position Offsets',
            'UI_setting_lockPositionOffsets_tooltip': 'Prevents changes to marker positions during gameplay',
            'UI_setting_anchorHorizontalOffset_text': 'Horizontal Offset',
            'UI_setting_anchorHorizontalOffset_tooltip': 'Adjusts the horizontal position of the marker',
            'UI_setting_anchorVerticalOffset_text': 'Vertical Offset',
            'UI_setting_anchorVerticalOffset_tooltip': 'Adjusts the vertical position of the marker',
            #
            'UI_setting_displayMode_always': 'Always',
            'UI_setting_displayMode_onAltPressed': 'When Alt is pressed',
            'UI_setting_markerTarget_allyAndEnemy': 'Allies and enemies',
            'UI_setting_markerTarget_onlyEnemy': 'Only enemies',
            'UI_setting_anchorPosition_tankMarker': 'Tank marker',
            'UI_setting_anchorPosition_tankCenter': 'Tank center',
            'UI_setting_anchorPosition_tankBottom': 'Tank bottom',
            # Column 2 settings
            'UI_setting_decimalPrecision_text': 'Decimal Precision',
            'UI_setting_decimalPrecision_tooltip': 'Defines how many decimal places will be displayed in the distance',
            'UI_setting_textSize_text': 'Text Size',
            'UI_setting_textSize_tooltip': 'Adjusts the font size of the marker',
            'UI_setting_textColor_text': 'Text Color',
            'UI_setting_textColor_tooltip': 'Sets the text color of the marker',
            'UI_setting_textAlpha_text': 'Text Transparency',
            'UI_setting_textAlpha_tooltip': 'Adjusts the transparency of the marker text',
            'UI_setting_drawTextShadow_text': 'Text Shadow',
            'UI_setting_drawTextShadow_tooltip': 'Adds shadow to the text to improve visibility'
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            "modDisplayName": self.ID,
            "enabled": self.data['enabled'],
            "column1": [
                self.tb.createOptions('displayMode', ['always', 'onAltPressed']),
                self.tb.createOptions('markerTarget', ['allyAndEnemy', 'onlyEnemy']),
                self.tb.createOptions('anchorPosition', ['tankMarker', 'tankCenter', 'tankBottom']),
                self.tb.createControl('lockPositionOffsets'),
                self.tb.createStepper('anchorHorizontalOffset', -150, 150, 1),
                self.tb.createStepper('anchorVerticalOffset', -150, 150, 1)
            ],
            "column2": [
                self.tb.createSlider('decimalPrecision', 0, 3, 1),
                self.tb.createSlider('textSize', 6, 24, 1),
                self.tb.createControl('textColor', self.tb.types.ColorChoice),
                self.tb.createSlider('textAlpha', 0.0, 1.0, 0.01),
                self.tb.createControl('drawTextShadow')
            ]
        }


config = ConfigInterface()
analytics = Analytics(config.ID, config.version)


def serializeConfigParams():
    textColor = config.data['textColor']
    if isinstance(textColor, str):
        if textColor.startswith('#'):
            textColor = textColor[1:]
        hex_color = '0x' + textColor
    else:
        r, g, b = textColor
        hex_color = '0x{:02X}{:02X}{:02X}'.format(r, g, b)
    return {
        'decimalPrecision': config.data['decimalPrecision'],
        'textSize': config.data['textSize'],
        'textColor': hex_color,  # Send properly formatted hex color
        'textAlpha': config.data['textAlpha'],
        'drawTextShadow': config.data['drawTextShadow']
    }


class _SimpleDictPool(object):
    def __init__(self):
        self.pool = []

    def __getitem__(self, item):
        return self.pool[item]

    def ensureLength(self, length):
        lackingCount = length - len(self.pool)
        if lackingCount <= 0:
            return
        for i in range(lackingCount):
            self.pool.append({})


class DistanceMarkerFlashMeta(BaseDAAPIModule):
    def as_applyConfig(self, serializedConfig):
        if self._isDAAPIInited():
            return self.flashObject.as_applyConfig(serializedConfig)

    def as_isPointInMarker(self, mouseX, mouseY):
        if self._isDAAPIInited():
            return self.flashObject.as_isPointInMarker(mouseX, mouseY)


class DistanceMarkerFlash(ExternalFlashComponent, DistanceMarkerFlashMeta):
    _eventManager = EventManager()
    onMouseEvent = Event(_eventManager)

    def __init__(self, vehicleMarkerClass):
        super(DistanceMarkerFlash, self).__init__(ExternalFlashSettings('DistanceMarkerFlash', 'DistanceMarkerFlash.swf', 'root', None))
        self._vehicleMarkerClass = vehicleMarkerClass
        self.createExternalComponent()
        self._configureApp()
        self._currentHorizontalAnchorOffset = config.data['anchorHorizontalOffset']
        self._currentVerticalAnchorOffset = -1 * config.data['anchorVerticalOffset']
        self._wereOffsetsEdited = False
        self._isDisplayingMarkers = config.data['displayMode'] == 0
        self._isMarkerDragging = False
        anchorPosition = config.data['anchorPosition']
        if anchorPosition == 0:
            self._markerPositionProvider = self._vehicleMarkerPositionProvider
        elif anchorPosition == 1:
            self._markerPositionProvider = self._vehicleCenterPositionProvider
        else:
            self._markerPositionProvider = self._vehicleBottomPositionProvider
        self._currentViewProjectionMatrix = Math.Matrix()
        self._tempMatrix = Math.Matrix()
        self._emptyList = []
        self._dictPool = _SimpleDictPool()
        screenResolution = GUI.screenResolution()
        self._currentScreenWidth = screenResolution[0]
        self._currentScreenHeight = screenResolution[1]
        self._currentFrameData = {'screenWidth': self._currentScreenWidth, 'screenHeight': self._currentScreenHeight, 'observedVehicles': self._emptyList}
        InputHandler.g_instance.onKeyUp += self._onKeyUp
        InputHandler.g_instance.onKeyDown += self._onKeyDown
        serializedConfig = serializeConfigParams()
        self.as_applyConfig(serializedConfig)

    def close(self):
        if self._isMarkerDragging:
            self.onMouseEvent -= self._onMarkerDragging
            self._isMarkerDragging = False
        InputHandler.g_instance.onKeyUp -= self._onKeyUp
        InputHandler.g_instance.onKeyDown -= self._onKeyDown
        super(DistanceMarkerFlash, self).close()
        if self._wereOffsetsEdited:
            config.data['anchorHorizontalOffset'] = self._currentHorizontalAnchorOffset
            config.data['anchorVerticalOffset'] = -1 * self._currentVerticalAnchorOffset

    def _configureApp(self):
        self.movie.backgroundAlpha = 0.0
        self.movie.scaleMode = SCALEFORM.eMovieScaleMode.NO_SCALE
        self.component.wg_inputKeyMode = InputKeyMode.NO_HANDLE
        self.component.position.z = DEPTH_OF_VehicleMarker - 0.02
        self.component.focus = False
        self.component.moveFocus = False

    def _onKeyUp(self, event):
        if config.data['displayMode'] == 1:
            self._isDisplayingMarkers = event.isAltDown()
        if self._isMarkerDragging and self._isLeftMouseButton(event):
            self._isMarkerDragging = False
            self.onMouseEvent -= self._onMarkerDragging

    def _onKeyDown(self, event):
        if config.data['displayMode'] == 1:
            self._isDisplayingMarkers = event.isAltDown()
        cursor = GUI.mcursor()
        isOffsetChangeAllowed = not config.data['lockPositionOffsets']
        if self._isDisplayingMarkers and isOffsetChangeAllowed and event.isCtrlDown() and self._isLeftMouseButton(
                event) and cursor.inWindow and cursor.inFocus:
            mouseX, mouseY = cursor.position
            screenX, screenY = self._toScreenPixelPosition(mouseX, mouseY)
            if self.as_isPointInMarker(screenX, screenY):
                self._isMarkerDragging = True
                self.onMouseEvent += self._onMarkerDragging

    @staticmethod
    def _isLeftMouseButton(event):
        return event.isMouseButton() and event.key == Keys.KEY_LEFTMOUSE

    def _onMarkerDragging(self, dx, dy):
        self._currentHorizontalAnchorOffset += dx
        self._currentVerticalAnchorOffset += dy
        self._wereOffsetsEdited = True

    def py_requestFrameData(self):
        try:
            screenResolution = GUI.screenResolution()
            self._currentFrameData['screenWidth'] = self._currentScreenWidth = screenResolution[0]
            self._currentFrameData['screenHeight'] = self._currentScreenHeight = screenResolution[1]
            self._currentFrameData['observedVehicles'] = self._emptyList
            return self._requestFrameData()
        except Exception as e:
            logWarning(config.ID, 'Occurred on requesting frame data by DistanceMarkerFlash, safely skipping frame rendering: {}', e, exc_info=True)
            self._currentFrameData['observedVehicles'] = self._emptyList
            return self._currentFrameData

    def _requestFrameData(self):
        if not self._isDisplayingMarkers:
            return self._currentFrameData
        player = BigWorld.player()
        if player is None:
            return self._currentFrameData
        avatarInputHandler = player.inputHandler
        if avatarInputHandler is not None and not avatarInputHandler.isGuiVisible:
            return self._currentFrameData
        currentVehicleID = -1
        currentVehicle = player.getVehicleAttached()
        if self._isVehicleSafeToUse(currentVehicle):
            currentVehicleID = currentVehicle.id
            playerPositionProvider = currentVehicle.matrix
        elif BigWorld.camera() is not None:
            playerPositionProvider = BigWorld.camera().matrix
        else:
            return self._currentFrameData
        self._tempMatrix.set(playerPositionProvider)
        currentPlayerPosition = self._tempMatrix.translation
        self._updateViewProjectionMatrix()
        vehicles = BigWorld.player().vehicles
        self._dictPool.ensureLength(len(vehicles))
        # Performance improvement: Use list comprehension with pre-filtering
        observed_vehicles = []
        for poolIndex, vehicle in enumerate(vehicles):
            if self._shouldDisplayForVehicle(vehicle, currentVehicleID):
                vehicle_data = self._serializeObservedVehicle(currentPlayerPosition, vehicle, self._dictPool[poolIndex])
                observed_vehicles.append(vehicle_data)

        self._currentFrameData['observedVehicles'] = observed_vehicles
        return self._currentFrameData

    def _shouldDisplayForVehicle(self, vehicle, currentVehicleID):
        if not self._isVehicleSafeToUse(vehicle) or vehicle.id == currentVehicleID:
            return False
        if not vehicle.isAlive():
            return False
        if config.data['markerTarget'] == 0:
            return True
        return BigWorld.player().team != vehicle.publicInfo['team']

    @staticmethod
    def _isVehicleSafeToUse(vehicle):
        return vehicle is not None and getattr(vehicle, 'isStarted', False)

    def _updateViewProjectionMatrix(self):
        proj = BigWorld.projection()
        aspect = BigWorld.getAspectRatio()
        self._currentViewProjectionMatrix.perspectiveProjection(proj.fov, aspect, proj.nearPlane, proj.farPlane)
        self._currentViewProjectionMatrix.preMultiply(BigWorld.camera().matrix)

    def _serializeObservedVehicle(self, currentPlayerPosition, vehicle, pooledVehicleDict):
        self._tempMatrix.set(vehicle.matrix)
        vehiclePosition = self._tempMatrix.translation
        currentDistance = (vehiclePosition - currentPlayerPosition).length
        markerPosition3d = self._markerPositionProvider(vehicle)
        projectedMarkerPosition2d, isPointOnScreen = self._projectPointWithVisibilityResult(markerPosition3d)
        x, y = self._toScreenPixelPosition(projectedMarkerPosition2d.x, projectedMarkerPosition2d.y)
        pooledVehicleDict['id'] = str(vehicle.id)
        pooledVehicleDict['currentDistance'] = currentDistance
        pooledVehicleDict['x'] = x + self._currentHorizontalAnchorOffset
        pooledVehicleDict['y'] = y + self._currentVerticalAnchorOffset
        pooledVehicleDict['isVisible'] = isPointOnScreen
        return pooledVehicleDict

    def _vehicleMarkerPositionProvider(self, vehicle):
        try:
            vehicleMarkerMatrixProvider = self._vehicleMarkerClass.fetchMatrixProvider(vehicle)
            self._tempMatrix.set(vehicleMarkerMatrixProvider)
            return self._tempMatrix.translation
        except Exception as e:
            logWarning(config.ID, 'Error in _vehicleMarkerPositionProvider: {}'.format(e))
            return self._vehicleCenterPositionProvider(vehicle)

    def _vehicleCenterPositionProvider(self, vehicle):
        self._tempMatrix.set(vehicle.matrix)
        vehicleCenterPosition = self._tempMatrix.translation
        vehicleCenterPosition.y += 2.0
        return vehicleCenterPosition

    def _vehicleBottomPositionProvider(self, vehicle):
        self._tempMatrix.set(vehicle.matrix)
        vehicleCenterPosition = self._tempMatrix.translation
        vehicleCenterPosition.y -= 1.0
        return vehicleCenterPosition

    def _projectPointWithVisibilityResult(self, point):
        posInClip = Math.Vector4(point.x, point.y, point.z, 1)
        posInClip = self._currentViewProjectionMatrix.applyV4Point(posInClip)
        if point.lengthSquared != 0.0:
            visible = posInClip.w > 0 and -1 <= posInClip.x / posInClip.w <= 1 and -1 <= posInClip.y / posInClip.w <= 1
        else:
            visible = False
        if posInClip.w != 0:
            posInClip = posInClip.scale(1 / posInClip.w)
        return posInClip, visible

    def _toScreenPixelPosition(self, x, y):
        normalizedX = 0.5 + 0.5 * x
        normalizedY = 0.5 - 0.5 * y
        return normalizedX * self._currentScreenWidth, normalizedY * self._currentScreenHeight


@override(AvatarInputHandler, 'handleMouseEvent')
def handleMouseEvent(func, self, dx, dy, dz):
    result = func(self, dx, dy, dz)
    if g_distanceMarkerFlash is not None:
        DistanceMarkerFlash.onMouseEvent(dx, dy)
    return result


@override(VehicleMarkerPlugin, 'start')
def start(func, self):
    func(self)
    try:
        global g_distanceMarkerFlash
        if g_distanceMarkerFlash is None and config.data['enabled']:
            g_distanceMarkerFlash = DistanceMarkerFlash(self._clazz)
            g_distanceMarkerFlash.active(True)
    except Exception as e:
        logError(config.ID, 'Failed to create distance marker app: {}', e, exc_info=True)


@override(VehicleMarkerPlugin, 'stop')
def stop(func, self):
    func(self)
    try:
        global g_distanceMarkerFlash
        if g_distanceMarkerFlash is not None:
            g_distanceMarkerFlash.close()
            g_distanceMarkerFlash = None
    except Exception as e:
        logError(config.ID, 'Failed to close distance marker app: {}', e, exc_info=True)
