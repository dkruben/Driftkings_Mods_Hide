# -*- coding: utf-8 -*-
import BigWorld

from DriftkingsCore.utils.delayed import api
from DriftkingsCore.config.interfaces import DummyConfigInterface


class ConfigInterface(DummyConfigInterface):
    def __init__(self):
        # noinspection SpellCheckingInspection
        self.links = {
            'patreon': 'https://www.patreon.com/driftkings_mods/',
            'boosty': '',
            #
            'webmoney': '',
            'qiwi': '',
            #
            'youtube': 'https://www.youtube.com/channel/UC6MQdDXf-sX5UNJoUf87e3w',
            'streamlabs_twitch': '',
        }
        super(ConfigInterface, self).__init__()

    def init(self):
        self.ID = 'Support'
        self.modsGroup = 'Driftkings'
        self.modSettingsID = 'Driftkings_GUI'
        self.i18n = {}
        super(ConfigInterface, self).init()

    def loadLang(self):
        # noinspection SpellCheckingInspection
        self.i18n = {
            'header': 'Поддержать автора',
            #
            'UI_setting_subscription_text': 'Подписка:',
            'patreon_button_text': 'Patreon:', 'patreon_button_label': 'Открыть в браузере',
            'boosty_button_text': 'Boosty:', 'boosty_button_label': 'Открыть в браузере',
            #
            'UI_setting_streamlabs_text': 'PayPal + оповещение на стриме:',
            'youtube_button_text': 'YouTube:', 'youtube_button_label': 'Открыть в браузере',
            'streamlabs_twitch_button_text': 'Twitch:', 'streamlabs_twitch_button_label': 'Открыть в браузере',
        } if self.lang in ('ru', 'uk') else {
            'header': 'Support the author',
            #
            'UI_setting_subscription_text': 'Subscription:',
            'patreon_button_text': 'Patreon:', 'patreon_button_label': 'Open browser',
            'boosty_button_text': 'Boosty:', 'boosty_button_label': 'Open browser',
            #
            'UI_setting_streamlabs_text': 'PayPal + stream shout-out:',
            'youtube_button_text': 'YouTube:', 'youtube_button_label': 'Open browser',
            'streamlabs_twitch_button_text': 'Twitch:', 'streamlabs_twitch_button_label': 'Open browser',
        }

    # noinspection SpellCheckingInspection
    def createTemplate(self):
        make_button = lambda _id: self.tb.createOptions(
            _id, [self.i18n[_id + '_button_text']],
            self.tb.types.RadioButtonGroup,
            200,
            True,
            {
                'text': self.i18n[_id + '_button_label'],
                'width': 150
            },
            0
        )
        return {
            'modDisplayName': self.i18n['header'],
            'column1':
                [
                    self.tb.createLabel('subscription'),
                ] + [
                    make_button(_id)
                    for _id in 'patreon'
                ],
            'column2':
                [self.tb.createLabel('donation'),
                 ] + [
                    self.tb.createLabel('streamlabs'),
                ] + [
                    make_button(_id)
                    for _id in ('youtube', 'streamlabs_twitch')
                ]}

    def onApplySettings(self, settings):
        pass

    def getData(self):
        return dict.fromkeys(self.links, 0)

    def onButtonPress(self, vName, value):
        link = self.links.get(vName)
        if link:
            BigWorld.wg_openWebBrowser(link)


def delayed():
    global g_config
    if api.MSA_Orig is not None and 'Driftkings_GUI' in ConfigInterface.modSettingsContainers:
        g_config = ConfigInterface()


g_config = None
BigWorld.callback(0, delayed)
