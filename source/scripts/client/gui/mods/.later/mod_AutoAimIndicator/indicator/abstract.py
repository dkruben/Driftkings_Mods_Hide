# -*- coding: utf-8 -*-
from helpers.CallbackDelayer import CallbackDelayer


class AbstractIndicator(CallbackDelayer):

    def __init__(self, controller, isEnabled):
        super(AbstractIndicator, self).__init__()
        self.controller = controller
        self.isEnabled = isEnabled
        self.isStarted = False
        self.controller.onStart += self.start
        self.controller.onStop += self.stop

    def start(self):
        self.isStarted = self.isEnabled()
        if self.isStarted:
            self.controller.onCreate += self.create
            self.controller.onDestroy += self.destroy
            self.controller.onShow += self.show
            self.controller.onHide += self.hide

    def stop(self):
        if self.isStarted:
            self.isStarted = False
            self.controller.onCreate -= self.create
            self.controller.onDestroy -= self.destroy
            self.controller.onShow -= self.show
            self.controller.onHide -= self.hide

    def create(self):
        raise NotImplemented

    def destroy(self):
        raise NotImplemented

    def show(self, vehicle):
        raise NotImplemented

    def hide(self):
        raise NotImplemented
