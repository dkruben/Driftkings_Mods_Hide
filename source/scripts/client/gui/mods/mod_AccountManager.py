# -*- coding: utf-8 -*-
import hashlib
import json
import os
import time

import BigWorld
from external_strings_utils import unicode_from_utf8
from frameworks.wulf import WindowLayer
from gui import DialogsInterface
from gui.Scaleform.daapi.view.dialogs import SimpleDialogMeta, DIALOG_BUTTON_ID
from gui.Scaleform.daapi.view.lobby.LobbyView import LobbyView
from gui.Scaleform.daapi.view.login.LoginView import LoginView
from gui.Scaleform.daapi.view.login.login_modes import createLoginMode
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.entities.abstract.AbstractWindowView import AbstractWindowView
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.shared.personality import ServicesLocator
from predefined_hosts import g_preDefinedHosts
from skeletons.gui.app_loader import GuiGlobalSpaceID

from DriftkingsCore import DriftkingsConfigInterface, ConfigNoInterface, Analytics, override, callback, calculate_version


def getPreferencesDir():
    preferences_file_path = unicode_from_utf8(BigWorld.wg_getPreferencesFilePath())[1]
    return os.path.normpath(os.path.dirname(preferences_file_path))


def loadWindow(alias):
    app = ServicesLocator.appLoader.getApp()
    app.loadView(SFViewLoadParams(alias))


class ConfigsInterface(ConfigNoInterface, DriftkingsConfigInterface):
    def init(self):
        self.ID = '%(mod_ID)s'
        self.version = '1.0.5 (%(file_compile_date)s)'
        self.author = '[by: S0me0ne, reworked by ShadowHunterRUS & spoter & Driftkings]'
        self.data = {'version': calculate_version(self.version)}
        self.i18n = {
            'UI_description': self.ID,
            'UI_version': calculate_version(self.version),
            'UI_setting_delete': 'Delete',
            'UI_setting_cancel': 'Cancel',
            'UI_setting_enter': '<font color=\'#FFFF33\' size=\'18\'>Enter</font>',
            'UI_setting_edit': '<font color=\'#9ACD32\' size=\'18\'>Edit</font>',
            'UI_setting_deleteAccount': '<font color=\'#FF4500\' size=\'18\'>Delete</font>',
            'UI_setting_accountManager': 'Account manager',
            'UI_setting_add': 'Add',
            'UI_setting_autoEnter': 'Auto Enter',
            'UI_setting_acceptDeleteAccount': 'Accept delete account',
            'UI_setting_accountDelete': 'Delete Account',
            'UI_setting_save': 'Save',
            'UI_setting_server': 'Server:',
            'UI_setting_showPassword': 'Show password',
            'UI_setting_nick': 'Nick:',
            'UI_setting_manageYourAccount': 'Manage Your account'
        }
        super(ConfigsInterface, self).init()


config = ConfigsInterface()
analytics = Analytics(config.ID, config.version)


class AM_MODES:
    def __init__(self):
        pass
    ADD = 'add'
    EDIT = 'edit'
    DELETE = 'delete'


class M_obj:
    def __init__(self):
        pass


class UserAccounts:
    __accounts_manager = None

    def __init__(self):
        self.__accounts_manager = os.path.join(getPreferencesDir(), 'Driftkings', 'accounts.manager')
        if not os.path.isfile(self.__accounts_manager):
            self.accounts = []
            self.write_accounts()
        self.renew_accounts()

    def renew_accounts(self):
        try:
            with open(self.__accounts_manager, 'r') as f:
                filedata = f.read()
            filedata = BigWorld.wg_ucpdata(filedata)
            self.accounts = json.loads(filedata.decode('base64').decode('zlib'))
        except StandardError:
            self.accounts = []

    def write_accounts(self):
        data = BigWorld.wg_cpdata(json.dumps(self.accounts).encode('zlib').encode('base64'))
        with open(self.__accounts_manager, 'w') as f:
            f.write(data)


class RemoveConfirmDialogButtons:
    def __init__(self):
        pass

    def getLabels(self):
        return [
            {'id': DIALOG_BUTTON_ID.SUBMIT, 'label': config.i18n['UI_setting_delete'], 'focused': True},
            {'id': DIALOG_BUTTON_ID.CLOSE, 'label': config.i18n['UI_setting_cancel'], 'focused': False}
        ]


class AccountsManager(AbstractWindowView):
    def __init__(self):
        AbstractWindowView.__init__(self)
        self._loginMode = createLoginMode(self)

    def py_log(self, text):
        print('[AccountsManager]: %s' % text)

    def py_setLoginDataById(self, id, form):
        for account in BigWorld.wh_data.accounts:
            if str(account['id']) != id:
                continue
            form.login.text = BigWorld.wg_ucpdata(account['email'])
            getattr(form, 'pass').text = BigWorld.wg_ucpdata(account['password'])
            form.server.selectedIndex = int(account['cluster'])
            form.submit.enabled = True
            self._loginMode.resetToken()
            self.destroy()

    def py_getTranslate(self):
        return {
            'submit_l10n': config.i18n['UI_setting_enter'],
            'edit_l10n': config.i18n['UI_setting_edit'],
            'delete_l10n': config.i18n['UI_setting_deleteAccount'],
            'window_title_l10n': config.i18n['UI_setting_accountManager'],
            'add_l10n': config.i18n['UI_setting_add'],
            'auto_enter_l10n': config.i18n['UI_setting_autoEnter']
        }

    def _populate(self):
        # noinspection PyProtectedMember
        AbstractWindowView._populate(self)
        z_data = []
        clusters = g_preDefinedHosts.shortList()
        for account in BigWorld.wh_data.accounts:
            account['cluster'] = int(account['cluster'])
            if len(clusters) - 1 < account['cluster']:
                account['cluster'] = 0
            cluster_name = clusters[account['cluster']][1].split().pop()
            z_data.append({'id': account['id'], 'user': account['title'], 'cluster': cluster_name})
        self.callToFlash(z_data)

    def py_openAddAccountWindow(self):
        BigWorld.wh_current = M_obj()
        BigWorld.wh_current.mode = 'add'
        loadWindow('AccountsManagerSubWindow')
        self.destroy()

    def callFromFlash(self, data):
        BigWorld.wh_current = M_obj()
        if data.action == AM_MODES.EDIT:
            for account in BigWorld.wh_data.accounts:
                if str(account['id']) != str(data.id):
                    continue
                BigWorld.wh_current.accId = account['id']
                BigWorld.wh_current.mode = data.action
                BigWorld.wh_current.title = account['title']
                BigWorld.wh_current.email = BigWorld.wg_ucpdata(account['email'])
                BigWorld.wh_current.password = BigWorld.wg_ucpdata(account['password'])
                BigWorld.wh_current.cluster = account['cluster']
                loadWindow('AccountsManagerSubWindow')
                self.destroy()
                return
        elif data.action == AM_MODES.DELETE:
            _buttons = RemoveConfirmDialogButtons()
            meta = SimpleDialogMeta(message=config.i18n['UI_setting_acceptDeleteAccount'], title=config.i18n['UI_setting_accountDelete'], buttons=_buttons)

            def onClickAction(result):
                if not result:
                    return
                for it in BigWorld.wh_data.accounts:
                    if str(it['id']) != str(data.id):
                        continue
                    BigWorld.wh_data.accounts.remove(it)
                    BigWorld.wh_data.write_accounts()
                    BigWorld.wh_data.renew_accounts()
                    self.destroy()
                    loadWindow('AccountsManager')
                    return
            DialogsInterface.showDialog(meta, onClickAction)

    def callToFlash(self, data):
        if self._isDAAPIInited():
            self.flashObject.as_callToFlash(data)

    def as_isModalS(self):
        return True

    def onWindowClose(self):
        self.destroy()

    def onModuleDispose(self):
        pass


class AccountsManagerSubWindow(AbstractWindowView):
    __clusters = []

    def __init__(self):
        if not self.__clusters:
            for cluster in g_preDefinedHosts.shortList():
                self.__clusters.append({'label': cluster[1], 'data': cluster[1]})
        AbstractWindowView.__init__(self)

    def py_log(self, text):
        print('[AccountsManagerSubWindow]: %s' % text)

    def py_get_clusters(self):
        return self.__clusters

    def py_getTranslate(self):
        return {
            'save_l10n': config.i18n['UI_setting_save'],
            'cancel_l10n': '#settings:cancel_button',
            'server_l10n': config.i18n['UI_setting_server'],
            'show_password_l10n': config.i18n['UI_setting_showPassword'],
            'password_l10n': '#menu:login/password',
            'nick_l10n': config.i18n['UI_setting_nick'],
            'window_title_l10n': config.i18n['UI_setting_manageYourAccount']
        }

    def _populate(self):
        # noinspection PyProtectedMember
        AbstractWindowView._populate(self)
        if not self._isDAAPIInited():
            return
        acc = BigWorld.wh_current
        if BigWorld.wh_current.mode == AM_MODES.EDIT:
            self.flashObject.as_setEditAccountData(acc.accId, acc.title, acc.email, acc.password, min(int(acc.cluster), len(self.__clusters) - 1))
        elif BigWorld.wh_current.mode == AM_MODES.ADD:
            self.flashObject.as_setAddAccount()

    def py_setAddAccount(self, title, email, password, cluster):
        BigWorld.wh_data.accounts.append({
            'title': title,
            'cluster': cluster,
            'email': BigWorld.wg_cpdata(email),
            'password': BigWorld.wg_cpdata(password),
            'id': hashlib.md5('id = %s' % time.time()).hexdigest()
        })
        BigWorld.wh_data.write_accounts()
        BigWorld.wh_data.renew_accounts()
        self.destroy()
        loadWindow('AccountsManager')

    def py_setEditAccount(self, id, title, email, password, cluster):
        for it in BigWorld.wh_data.accounts:
            if str(it['id']) != str(id):
                continue
            it['title'] = title
            it['cluster'] = cluster
            it['email'] = BigWorld.wg_cpdata(email)
            it['password'] = BigWorld.wg_cpdata(password)
            break
        BigWorld.wh_data.write_accounts()
        BigWorld.wh_data.renew_accounts()
        self.destroy()
        loadWindow('AccountsManager')

    def as_isModalS(self):
        return True

    def onWindowClose(self):
        self.destroy()
        loadWindow('AccountsManager')


BigWorld.wh_data = UserAccounts()
g_entitiesFactories.addSettings(ViewSettings('AccountsManager', AccountsManager, 'AccountsManager.swf', WindowLayer.WINDOW, None, ScopeTemplates.DEFAULT_SCOPE))
g_entitiesFactories.addSettings(ViewSettings('AccountsManagerSubWindow', AccountsManagerSubWindow, 'AccountsManagerWindow.swf', WindowLayer.WINDOW, None, ScopeTemplates.DEFAULT_SCOPE))


class AccountsManagerButtonController(object):
    def __init__(self):
        ServicesLocator.appLoader.onGUISpaceEntered += self.onGUISpaceEntered
        self.isLobby = False
        self.flash = None

        override(LoginView, '_populate', self.new__loginPopulate)
        override(LobbyView, '_populate', self.new__lobbyPopulate)

    @staticmethod
    def onGUISpaceEntered(spaceID):
        if spaceID == GuiGlobalSpaceID.LOBBY:
            app = ServicesLocator.appLoader.getApp()
            if app is not None:
                callback(0.0, lambda: app.loadView(SFViewLoadParams('AccountsManagerLoginButton')))

    def new__loginPopulate(self, func, b_self):
        func(b_self)
        self.isLobby = False
        if self.flash is not None:
            self.flash.processPopulate()

    def new__lobbyPopulate(self, func, b_self):
        func(b_self)
        self.isLobby = True
        if self.flash is not None:
            self.flash.processPopulate()


class AccountsManagerLoginButton(View):
    def _populate(self):
        g_AccMngr.flash = self
        # noinspection PyProtectedMember
        super(AccountsManagerLoginButton, self)._populate()
        self.processPopulate()

    def _dispose(self):
        # noinspection PyProtectedMember
        super(AccountsManagerLoginButton, self)._dispose()

    def processPopulate(self):
        if self._isDAAPIInited():
            if g_AccMngr.isLobby:
                self.flashObject.as_populateLobby()
            else:
                self.flashObject.as_populateLogin()

    def processLoginMode(self, enabled=False):
        if self._isDAAPIInited():
            self.flashObject.as_setLoginMode(enabled)

    def py_log(self, text):
        print('[AccountsManagerLoginButton]: %s' % text)

    def py_openAccMngr(self):
        app = ServicesLocator.appLoader.getApp()
        app.loadView(SFViewLoadParams('AccountsManager'))

    def py_getTranslate(self):
        return {'tooltip_l10n': config.i18n['UI_description']}


g_AccMngr = AccountsManagerButtonController()
g_entitiesFactories.addSettings(ViewSettings('AccountsManagerLoginButton', AccountsManagerLoginButton, 'AccountsManagerLoginButton.swf', WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
