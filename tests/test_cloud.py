import threading
import unittest
from unittest import mock

from cloud import config, sync
from cloud.fake_server import make_server


class TestMerge(unittest.TestCase):
    def test_union_and_local_wins(self):
        local = {'a': {'amount': 1}, 'b': {'amount': 2}}
        remote = {'b': {'amount': 999}, 'c': {'amount': 3}}
        self.assertEqual(sync.merge(local, remote),
                         {'a': {'amount': 1}, 'b': {'amount': 2}, 'c': {'amount': 3}})


class TestWithFakeServer(unittest.TestCase):
    """Настоящие HTTP-запросы к локальному серверу, имитирующему Firebase."""

    def setUp(self):
        self.server = make_server(port=0)           # 0 = свободный порт
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self._old_url = config.DATABASE_URL
        config.DATABASE_URL = f'http://127.0.0.1:{self.server.server_address[1]}'

    def tearDown(self):
        config.DATABASE_URL = self._old_url
        self.server.shutdown()
        self.server.server_close()

    def test_empty_cloud_returns_empty_dict(self):
        self.assertEqual(sync.download(), {})

    def test_two_devices_see_each_others_data(self):
        phone = {'t_1': {'kind': 'income', 'category': 'Продажи', 'description': 'А', 'amount': 100.0, 'date': '1'}}
        laptop = {'t_2': {'kind': 'expense', 'category': 'Офис', 'description': 'Б', 'amount': 50.0, 'date': '2'}}

        sync.sync(phone)                      # телефон отправил свои данные
        merged = sync.sync(laptop)            # ноутбук получил чужие и добавил свои
        self.assertEqual(set(merged), {'t_1', 't_2'})
        self.assertEqual(set(sync.download()), {'t_1', 't_2'})   # в облаке есть всё
        self.assertEqual(merged['t_1']['description'], 'А')      # русский текст не испортился


class TestErrors(unittest.TestCase):
    def test_not_configured(self):
        old = config.DATABASE_URL
        config.DATABASE_URL = ''
        try:
            self.assertFalse(sync.is_configured())
        finally:
            config.DATABASE_URL = old

    def test_unreachable_server_raises_clouderror(self):
        old = config.DATABASE_URL
        config.DATABASE_URL = 'http://127.0.0.1:1'       # там никто не слушает
        try:
            with self.assertRaises(sync.CloudError):
                sync.download()
        finally:
            config.DATABASE_URL = old

    def test_bad_json_raises_clouderror(self):
        old = config.DATABASE_URL
        config.DATABASE_URL = 'http://example.invalid'
        fake = mock.Mock()
        fake.raise_for_status.return_value = None
        fake.json.side_effect = ValueError('not json')
        try:
            with mock.patch('cloud.sync.requests.get', return_value=fake):
                with self.assertRaises(sync.CloudError):
                    sync.download()
        finally:
            config.DATABASE_URL = old


if __name__ == '__main__':
    unittest.main()
