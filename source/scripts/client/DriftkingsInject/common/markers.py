# -*- coding: utf-8 -*-
import BigWorld
import Math


class _StaticWorldObjectMarker3D(object):
    def __init__(self, data, position):
        self.__path = data.get('path')
        offset = data.get('offset', Math.Vector3(0, 0, 0))
        self.model = None
        self.__isMarkerVisible = True
        self.modelOwner = None
        self.__destroyed = False
        if self.__path is not None:
            modelPosition = Math.Vector3(position[:]) + offset
            refs = BigWorld.loadResourceListFG([self.__path])
            self.__onModelLoaded(refs, modelPosition)

    def addMarkerModel(self):
        if self.model is None or self.modelOwner is not None:
            return
        self.modelOwner = BigWorld.player()
        self.modelOwner.addModel(self.model)

    def clear(self):
        self.setVisible(False)
        self.model = None
        self.__destroyed = True

    def setVisible(self, isVisible):
        if not self.__isMarkerVisible and isVisible:
            self.__isMarkerVisible = True
            self.addMarkerModel()
        elif not isVisible:
            self.__isMarkerVisible = False
            if self.modelOwner is not None and not self.modelOwner.isDestroyed:
                self.modelOwner.delModel(self.model)
            self.modelOwner = None

    def __onModelLoaded(self, refs, position):
        if self.__destroyed:
            return
        if self.__path not in refs.failedIDs:
            self.model = refs[self.__path]
            self.model.position = position
            self.model.castsShadow = False
            if self.__isMarkerVisible:
                self.addMarkerModel()
