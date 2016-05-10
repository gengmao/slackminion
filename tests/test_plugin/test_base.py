import pytest

from slackclient._channel import Channel
from slackclient._user import User
from slackclient._util import SearchList
from slackminion.bot import Bot
from slackminion.plugin import BasePlugin
from slackminion.slack import SlackIM, SlackChannel, SlackGroup, SlackUser


def dummy_func(self):
    self.xyzzy = True


test_channel_id = 'C12345678'
test_channel_name = 'testchannel'
test_group_id = 'G12345678'
test_group_name = 'testgroup'
test_user_id = 'U12345678'
test_user_name = 'testuser'
str_format = '<#{id}|{name}>'

test_mapping = {
    test_channel_name: test_channel_id,
    test_group_name: test_group_id,
    test_user_name: test_user_id,
}

# Channel, result
test_message_data = [
    (SlackIM('D12345678'), 'send_im'),
    (SlackUser('U12345678'), 'send_im'),
    (SlackChannel('C12345678'), 'send_message'),
    (SlackGroup('G12345678'), 'send_message'),
    ('@testuser', 'send_im'),
    ('#testchannel', 'send_message'),
    ('testchannel', 'send_message'),
    (None, 'send_message'),
]

class DummyServer(object):
    def __init__(self):
        self.channels = SearchList()
        self.users = SearchList()


class DummySlackConnection(object):
    def __init__(self):
        self.server = DummyServer()
        self.server.channels.append(Channel(None, test_channel_name, test_channel_id))
        self.server.channels.append(Channel(None, test_group_name, test_group_id))
        self.server.users.append(User(None, test_user_name, test_user_id, test_user_name, None))

    def api_call(self, name, *args, **kwargs):
        api_responses = {
            'channels.info': {
                'channel': {
                    'name': test_channel_name,
                    'creator': test_user_id,
                    'topic': {
                        'value': 'Test Topic',
                    },
                },
            },
            'groups.info': {
                'group': {
                    'name': test_group_name,
                    'creator': test_user_id,
                    'topic': {
                        'value': 'Test Topic',
                    },
                },
            },
            'users.info': {
                'user': {
                    'id': test_user_id,
                    'name': test_user_name,
                },
            }
        }
        return api_responses[name]


class TestBasePlugin(object):

    def setup(self):
        self.object = BasePlugin(None)
        self.timer_started = False

    def teardown(self):
        self.object = None

    def test_on_load(self):
        assert hasattr(self.object, 'on_load')
        assert self.object.on_load() is True

    def test_on_unload(self):
        assert hasattr(self.object, 'on_unload')
        assert self.object.on_unload() is True

    def test_on_connect(self):
        assert hasattr(self.object, 'on_connect')
        assert self.object.on_connect() is True

    def test_start_timer(self, monkeypatch):
        def safe_start(self):
            assert self.interval == 30
            assert isinstance(self.args[1][0][0], TestBasePlugin)
            self.args[1][0][0].timer_started = True

        monkeypatch.setattr('threading.Thread.start', safe_start)
        self.object.start_timer(30, lambda: None, (self,))
        assert self.timer_started

    def test_stop_timer(self, monkeypatch):
        def safe_start(self):
            pass

        def safe_cancel(self):
            pass

        monkeypatch.setattr('threading.Thread.start', safe_start)
        monkeypatch.setattr('threading._Timer.cancel', safe_cancel)
        self.object.start_timer(30, dummy_func, self.object)
        assert dummy_func in self.object._timer_callbacks
        self.object.stop_timer(dummy_func)
        assert dummy_func not in self.object._timer_callbacks

    def test_run_timer(self, monkeypatch):
        def safe_start(self):
            self.function(*self.args)

        monkeypatch.setattr('threading.Thread.start', safe_start)
        self.object.start_timer(30, dummy_func, self.object)
        assert hasattr(self.object, 'xyzzy')

    def test_get_channel(self):
        self.object._bot = Bot(None)
        self.object._bot.sc = DummySlackConnection()
        channel = self.object.get_channel(test_channel_name)
        assert channel.id == test_channel_id
        assert channel.name == test_channel_name

    def test_get_user(self):
        self.object._bot = Bot(None)
        self.object._bot.sc = DummySlackConnection()
        user = self.object.get_user(test_user_name)
        assert user.id == test_user_id
        assert user.username == test_user_name

    @pytest.mark.parametrize('channel,result', test_message_data)
    def test_send_message(self, channel, result):
        class Bot(object):
            def __init__(self):
                self.method = ''

            def send_im(self, channel, text):
                self.method = 'send_im'

            def send_message(self, channel, text):
                self.method = 'send_message'

        self.object._bot = Bot()
        self.object.send_message(channel, 'Yet another test string')
        assert self.object._bot.method == result

