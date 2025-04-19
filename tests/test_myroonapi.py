import os
import unittest
from unittest.mock import patch, MagicMock
from myroonapi import MyRoonApi


class TestMyRoonApi(unittest.TestCase):
    def setUp(self):
        os.environ["NAME"] = "TestDevice"
        os.environ["ROON_ZONE"] = "TestZone"
        os.environ["ROON_CORE_ID"] = "test_core_id"
        os.environ["ROON_API_TOKEN"] = "test_token"

    def tearDown(self):
        os.environ.pop("NAME", None)
        os.environ.pop("ROON_ZONE", None)
        os.environ.pop("ROON_CORE_ID", None)
        os.environ.pop("ROON_API_TOKEN", None)

    @patch("myroonapi.RoonDiscovery")
    def test_register(self, mock_discovery):
        mock_discovery_instance = MagicMock()
        mock_discovery_instance.first.return_value = ("127.0.0.1", "test_core")
        mock_discovery.return_value = mock_discovery_instance

        with patch("myroonapi.RoonApi") as mock_roonapi:
            mock_roonapi_instance = MagicMock()
            mock_roonapi_instance.token = "test_token"
            mock_roonapi_instance.core_id = "test_core_id"  # Set core_id to a string
            mock_roonapi.return_value = mock_roonapi_instance

            api = MyRoonApi()
            zones = api.register()

            self.assertIsInstance(zones, list)
            self.assertEqual(os.environ["ROON_API_TOKEN"], "test_token")
            self.assertEqual(os.environ["ROON_CORE_ID"], "test_core_id")


    @patch("os.environ", new_callable=dict)
    def test_init_raises_exception_when_name_not_set(self, mock_environ):
        mock_environ.pop("NAME", None)  # Simulate NAME not being set
        with self.assertRaises(KeyError) as context:
            MyRoonApi()
        print(context.exception)
        self.assertEqual(str(context.exception), "'NAME environment variable must be set and have unique name for this device'")

    @patch("myroonapi.RoonDiscovery")
    def test_register(self, mock_discovery):
        mock_discovery_instance = MagicMock()
        mock_discovery_instance.first.return_value = ("127.0.0.1", "test_core")
        mock_discovery.return_value = mock_discovery_instance

        with patch("myroonapi.RoonApi") as mock_roonapi:
            mock_roonapi_instance = MagicMock()
            mock_roonapi_instance.token = "test_token"
            mock_roonapi_instance.core_id = "test_core_id"  # Set core_id to a string
            mock_roonapi.return_value = mock_roonapi_instance

            api = MyRoonApi()
            zones = api.register()

            self.assertIsInstance(zones, list)
            self.assertEqual(os.environ["ROON_API_TOKEN"], "test_token")

    @patch("myroonapi.RoonDiscovery")
    def test_connect_success(self, mock_discovery):
        mock_discovery_instance = MagicMock()
        mock_discovery_instance.first.return_value = ("127.0.0.1", "test_core")
        mock_discovery.return_value = mock_discovery_instance

        with patch("myroonapi.RoonApi") as mock_roonapi:
            mock_roonapi_instance = MagicMock()
            mock_roonapi_instance.zones = {
                "zone1": {"display_name": "TestZone", "state": "playing"}
            }
            mock_roonapi.return_value = mock_roonapi_instance

            api = MyRoonApi()
            connected = api.connect()

            self.assertTrue(connected)
            self.assertTrue(api.is_connected())

    @patch("myroonapi.RoonDiscovery")
    def test_connect_failure_no_server(self, mock_discovery):
        mock_discovery_instance = MagicMock()
        mock_discovery_instance.first.return_value = (None, None)
        mock_discovery.return_value = mock_discovery_instance

        api = MyRoonApi()
        connected = api.connect()

        self.assertFalse(connected)
        self.assertFalse(api.is_connected())

    def test_check_auth(self):
        api = MyRoonApi()
        self.assertTrue(api.check_auth())

        os.environ["ROON_API_TOKEN"] = ""
        self.assertFalse(api.check_auth())

    @patch("myroonapi.RoonApi")
    def test_get_zone_list(self, mock_roonapi):
        mock_roonapi_instance = MagicMock()
        mock_roonapi_instance.zones = {
            "zone1": {"display_name": "Zone1"},
            "zone2": {"display_name": "Zone2"},
        }
        mock_roonapi.return_value = mock_roonapi_instance

        api = MyRoonApi()
        api.roonapi = mock_roonapi_instance
        zones = api.get_zone_list()

        self.assertEqual(zones, ["Zone1", "Zone2"])

    @patch("myroonapi.RoonApi")
    def test_get_zone_data(self, mock_roonapi):
        mock_roonapi_instance = MagicMock()
        mock_roonapi_instance.zones = {
            "zone1": {
                "display_name": "TestZone",
                "state": "playing",
                "now_playing": {
                    "three_line": {
                        "line1": "Track1",
                        "line2": "Artist1",
                        "line3": "Album1",
                    },
                    "image_key": "image1",
                },
            }
        }
        mock_roonapi.return_value = mock_roonapi_instance

        api = MyRoonApi()
        api.roonapi = mock_roonapi_instance
        data = api.get_zone_data()

        self.assertIsNotNone(data)
        self.assertEqual(data["state"], "playing")
        self.assertEqual(data["artist"], "Artist1")
        self.assertEqual(data["title"], "Album1")
        self.assertEqual(data["track"], "Track1")


if __name__ == "__main__":
    unittest.main()
