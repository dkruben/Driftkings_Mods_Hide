# -*- coding: utf-8 -*-
import Keys
from Avatar import PlayerAvatar
from PlayerEvents import g_playerEvents
from frameworks.wulf import WindowLayer
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.shared.personality import ServicesLocator
from helpers import dependency
from messenger.MessengerEntry import g_instance
from skeletons.gui.battle_session import IBattleSessionProvider

from DriftkingsCore import SimpleConfigInterface, Analytics, override, getPlayer


class ConfigInterface(SimpleConfigInterface):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        g_playerEvents.onAvatarReady += self.onEnterBattlePage
        g_playerEvents.onAvatarBecomeNonPlayer += self.onExitBattlePage
        self.enabled = False
        self.unlockShoot = False
        self.vehicleErrorComponent = None
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.5.0 (%(file_compile_date)s)'
        self.defaultKeys = {'disableKey': [Keys.KEY_Q]}
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.data = {
            'enabled': True,
            'format': 'Save Shot: Shot in {} blocked',
        }
        self.i18n = {
            'UI_description': self.ID,
            'UI_setting_format_text': 'Format Message',
            'UI_setting_format_tooltip': ''
        }
        super(ConfigInterface, self).init()

    def createTemplate(self):
        return {
            'modDisplayName': self.ID,
            'enabled': self.data['enabled'],
            'column1': [
                self.tb.createControl('format', 'TextInput', 350)
            ],
            'column2': []}

    def onEnterBattlePage(self):
        if self.enabled:
            # g_keysListener.registerComponent(self.keyEvent)
            app = ServicesLocator.appLoader.getApp()
            if app is None:
                return
            battlePage = app.containerManager.getContainer(WindowLayer.VIEW).getView()
            if battlePage is None:
                return
            self.vehicleErrorComponent = battlePage.components.get(BATTLE_VIEW_ALIASES.VEHICLE_ERROR_MESSAGES)

    def onExitBattlePage(self):
        self.unlockShoot = False
        self.vehicleErrorComponent = None

    @staticmethod
    def is_targetAllyOrDeath(avatar):
        if avatar.target is not None and avatar.target.__class__.__name__ == 'Vehicle':
            return not avatar.target.isAlive() or avatar.target.publicInfo['team'] == avatar.team
        return False

    def keyEvent(self, isKeyDown):
        self.unlockShoot = isKeyDown

    def onHotkeyPressed(self, event):
        if not hasattr(getPlayer(), 'arena') or not self.data['enabled']:
            return
        isDown = self.unlockShoot
        if isDown != self.unlockShoot:
            self.unlockShoot = isDown
        if not event.isKeyDown():
            return


config = ConfigInterface()
analytics = Analytics(config.ID, config.version, 'UA-121940539-1')


@override(PlayerAvatar, 'shoot')
def shoot(func, self, isRepeat=False):
    if not config.data['enabled'] or config.unlockShoot or self.autoAimVehicle or not self.is_targetAllyOrDeath(self):
        return func(self, isRepeat=isRepeat)
    if isRepeat:
        return
    vehicleInfoVO = config.sessionProvider.getArenaDP().getVehicleInfo(self.target.id)
    message = config.data['format'].format(vehicleInfoVO.vehicleType.shortName)
    g_instance.gui.addClientMessage(message)
    if config.vehicleErrorComponent is not None:
        config.vehicleErrorComponent.as_showYellowMessageS(None, message)
