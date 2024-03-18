# -*- coding: utf-8 -*-
import GUI
import BigWorld
from Vehicle import Vehicle

from .abstract import AbstractIndicator
from DriftkingsCore import override


class BoundingBox(AbstractIndicator):

    def __init__(self, controller, isEnabled):
        super(BoundingBox, self).__init__(controller, isEnabled)
        self.indicator = None
        self.vehicleChassis = {}
        override(Vehicle, 'startVisual', self._Vehicle_startVisual)

    def create(self):
        self.vehicleChassis = {}
        self.indicator = GUI.AABB(self.controller.colour['texture'])
        self.indicator.size = (0.01, 0.01)
        self.indicator.colour = self.controller.colour['colour']
        self.indicator.visible = False
        GUI.addRoot(self.indicator)

    def destroy(self):
        self.vehicleChassis = {}
        GUI.delRoot(self.indicator)
        self.indicator = None

    def show(self, vehicle):
        if vehicle and hasattr(vehicle, 'isStarted') and vehicle.isStarted and self.indicator is not None:
            self.indicator.source = self.vehicleChassis[vehicle.id].bounds
            self.indicator.visible = True

    def hide(self):
        if self.indicator:
            self.indicator.source = None
            self.indicator.visible = False

    def _Vehicle_startVisual(self, baseFunc, baseSelf):
        baseFunc(baseSelf)
        self.vehicleChassis[baseSelf.id] = BigWorld.Model(baseSelf.typeDescriptor.chassis.models.undamaged)
        self.vehicleChassis[baseSelf.id].visible = False
        baseSelf.model.node('chassis').attach(self.vehicleChassis[baseSelf.id])