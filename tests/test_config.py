import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
from config import Config


class TestConfig(unittest.TestCase):
    def setUp(self):
        """Set up a clean environment for each test."""
        self.config = Config()
        self.mock_env = {
            "NAME": "TestFrame",
            "DISPLAY_ON_HOUR": "9",
            "DISPLAY_OFF_HOUR": "23",
            "DISPLAY_CONTROL": "on",
            "SLIDESHOW": "on",
            "SLIDESHOW_FOLDER": "./pictures",
            "SLIDESHOW_TRANSITION_SECONDS": "15",
            "SLIDESHOW_CLOCK_RATIO": "10",
            "CLOCK_SIZE": "100",
            "CLOCK_OFFSET": "50",
            "PORT": "5006",
            "HOST": "127.0.0.1",
            "LOCK_SETTINGS": "off",
        }

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="NAME=TestFrame\nPORT=5006\n")
    def test_dot_env_exists(self, mock_open, mock_exists):
        """Test if the .env file exists."""
        self.assertTrue(self.config.dot_env_exists())
        mock_exists.assert_called_with(".env")

    @patch("os.getenv", side_effect=lambda key, default=None: {"LOCK_SETTINGS": "on"}.get(key, default))
    def test_is_locked(self, mock_getenv):
        """Test if the configuration is locked."""
        self.assertTrue(self.config.is_locked())
        mock_getenv.assert_called_with("LOCK_SETTINGS", "off")

    @patch("subprocess.run")
    @patch("config.Config.load")
    def test_reset(self, mock_load, mock_run):
        """Test resetting the .env file."""
        self.config.reset()
        mock_run.assert_called_with(["cp", ".env.example", ".env"], check=True)
        mock_load.assert_called_once()

    @patch("os.getenv", side_effect=lambda key, default=None: {"NAME": "TestFrame", "PORT": "5006"}.get(key, default))
    def test_load(self, mock_getenv):
        """Test loading environment variables."""
        self.config.load()
        self.assertEqual(self.config.name, "TestFrame")
        self.assertEqual(self.config.port, 5006)

    @patch("os.getenv", side_effect=lambda key, default=None: {"NAME": "TestFrame", "PORT": "5006"}.get(key, default))
    @patch("builtins.open", new_callable=mock_open, read_data="NAME=TestFrame\nPORT=5006\n")
    def test_read_env_file(self,mock_getenv,  mock_open):
        """Test reading the .env file into a dictionary."""
        env_vars = self.config._read_env_file()
        self.assertEqual(env_vars["NAME"], "TestFrame")
        self.assertEqual(env_vars["PORT"], "5006")

    @patch("builtins.open", new_callable=mock_open)
    def test_write_env_file(self, mock_open):
        """Test writing environment variables to the .env file."""
        env_vars = {"NAME": "TestFrame", "PORT": "5006"}
        self.config._write_env_file(env_vars)
        mock_open.assert_called_with(".env", "w")
        mock_open().write.assert_any_call("NAME=TestFrame\n")
        mock_open().write.assert_any_call("PORT=5006\n")

    @patch("os.path.isdir", return_value=False)
    @patch("logging.Logger.warning")
    def test_validate_config(self, mock_warning, mock_isdir):
        """Test validating the configuration."""
        self.config._validate_config()
        mock_warning.assert_any_call("NAME environment variable is not set.")
        mock_warning.assert_any_call("Slideshow folder does not exist: None")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="legacy_token")
    @patch("os.remove")
    def test_migrate_legacy_file(self, mock_remove, mock_open, mock_exists):
        """Test migrating a legacy file to an environment variable."""
        self.config._migrate_legacy_file("legacy_file.txt", "LEGACY_ENV_VAR")
        self.assertEqual(os.environ["LEGACY_ENV_VAR"], "legacy_token")
        mock_remove.assert_called_with("legacy_file.txt")

    @patch("config.Config._read_env_file", return_value={"NAME": "TestFrame", "PORT": "5006"})
    @patch("config.Config._write_env_file")
    @patch("config.Config.load")
    def test_save(self, mock_load, mock_write_env_file, mock_read_env_file):
        """Test saving updates to the .env file."""
        updates = {"NAME": "UpdatedFrame", "HOST": "127.0.0.1"}
        self.config.save(updates)
        mock_read_env_file.assert_called_once()
        mock_write_env_file.assert_called_once_with({"NAME": "UpdatedFrame", "PORT": "5006", "HOST": "127.0.0.1"})
        mock_load.assert_called_once()


if __name__ == "__main__":
    unittest.main()