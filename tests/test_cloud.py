
import unittest
from unittest import mock

from cloud import config, sync


class TestMerge(unittest.TestCase):

    def test_union_and_local_wins(self):
        local = {
            "a": {"amount": 1},
            "b": {"amount": 2},
        }
        remote = {
            "b": {"amount": 999},
            "c": {"amount": 3},
        }

        self.assertEqual(
            sync.merge(local, remote),
            {
                "a": {"amount": 1},
                "b": {"amount": 2},
                "c": {"amount": 3},
            },
        )


class TestFirebaseSync(unittest.TestCase):
    """Проверка синхронизации без реальных запросов в Firebase."""

    @mock.patch("cloud.sync.authenticate")
    @mock.patch("cloud.sync.requests.get")
    def test_empty_cloud_returns_empty_dict(
        self, mock_get, mock_auth
    ):
        mock_auth.return_value = ("test_token", "test_uid")

        response = mock.Mock()
        response.json.return_value = None
        mock_get.return_value = response

        result = sync.download()

        self.assertEqual(result, {})
        mock_get.assert_called_once()

    @mock.patch("cloud.sync.authenticate")
    @mock.patch("cloud.sync.requests.put")
    @mock.patch("cloud.sync.requests.get")
    def test_two_devices_see_each_others_data(
        self, mock_get, mock_put, mock_auth
    ):
        mock_auth.return_value = ("test_token", "test_uid")

        cloud_data = {}

        def fake_get(*args, **kwargs):
            response = mock.Mock()
            response.json.return_value = dict(cloud_data)
            return response

        def fake_put(*args, **kwargs):
            cloud_data.clear()
            cloud_data.update(kwargs["json"])
            return mock.Mock()

        mock_get.side_effect = fake_get
        mock_put.side_effect = fake_put

        phone = {
            "t_1": {
                "kind": "income",
                "category": "Продажи",
                "description": "А",
                "amount": 100.0,
                "date": "1",
            }
        }

        laptop = {
            "t_2": {
                "kind": "expense",
                "category": "Офис",
                "description": "Б",
                "amount": 50.0,
                "date": "2",
            }
        }

        with mock.patch(
            "cloud.sync.is_configured", return_value=True
        ):
            sync.sync(phone)
            merged = sync.sync(laptop)

        self.assertEqual(set(merged), {"t_1", "t_2"})
        self.assertEqual(set(cloud_data), {"t_1", "t_2"})
        self.assertEqual(merged["t_1"]["description"], "А")

        self.assertEqual(mock_put.call_count, 2)


class TestErrors(unittest.TestCase):

    def test_not_configured(self):
        with mock.patch.object(config, "DATABASE_URL", ""):
            self.assertFalse(sync.is_configured())

    @mock.patch("cloud.sync.authenticate")
    @mock.patch("cloud.sync.requests.get")
    def test_unreachable_server_raises_clouderror(
        self, mock_get, mock_auth
    ):
        mock_auth.return_value = ("test_token", "test_uid")
        mock_get.side_effect = sync.requests.ConnectionError(
            "Server unavailable"
        )

        with self.assertRaises(sync.CloudError):
            sync.download()

    @mock.patch("cloud.sync.authenticate")
    @mock.patch("cloud.sync.requests.get")
    def test_bad_json_raises_clouderror(
        self, mock_get, mock_auth
    ):
        mock_auth.return_value = ("test_token", "test_uid")

        response = mock.Mock()
        response.json.side_effect = ValueError("not json")
        mock_get.return_value = response

        with self.assertRaises(sync.CloudError):
            sync.download()


if __name__ == "__main__":
    unittest.main()

