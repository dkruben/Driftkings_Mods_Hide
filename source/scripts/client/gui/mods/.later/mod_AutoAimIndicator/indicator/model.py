# -*- coding: utf-8 -*-
import BigWorld

from .abstract import AbstractIndicator


class Model(AbstractIndicator):

    def __init__(self, controller, isEnabled):
        super(Model, self).__init__(controller, isEnabled)
        self.vehicle = None
        self.indicator = None

    def create(self):
        self.indicator = BigWorld.Model(self.controller.colour['model'])
        self.indicator.visible = False

    def destroy(self):
        self.indicator = None

    def show(self, vehicle):
        if self.indicator:
            self.hide()
            self.vehicle = vehicle
            self.vehicle.model.root.attach(self.indicator)
            self.indicator.visible = True

    def hide(self):
        if self.indicator and self.indicator.visible:
            self.indicator.visible = False
            if self.vehicle and hasattr(self.vehicle, 'isStarted') and self.vehicle.isStarted:
                node = self.vehicle.model.root
                if hasattr(node, 'attachments') and self.indicator in node.attachments:
                    node.detach(self.indicator)
