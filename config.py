import os
import logging
import zoneinfo
from dotenv import load_dotenv
import subprocess
import re

logger = logging.getLogger(__name__)


class Config:
    """Configuration object to hold application settings."""

    def __init__(self):
        try:
            self.name = None
            load_dotenv()

            self.port = 5006
            self.host = "0.0.0.0"
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
            raise

    def dot_env_exists(self):
        return os.path.exists(".env")

    def is_locked(self):
        return os.getenv("LOCK_SETTINGS", "off") == "on"

    def reset(self):
        """Reset the .env file to the example configuration and reload settings."""
        subprocess.run(["cp", ".env.example", ".env"], check=True)
        load_dotenv()
        self.load()

    def load(self):
        load_dotenv(override=True)
        """Load configuration settings from environment variables."""
        # Load environment variables
        self.my_tz = zoneinfo.ZoneInfo(os.getenv("TZ", "America/New_York"))
        self.name = os.getenv("NAME", "")
        self.display_on_hour = int(os.getenv("DISPLAY_ON_HOUR", 9))
        self.display_off_hour = int(os.getenv("DISPLAY_OFF_HOUR", 23))
        self.display_control = os.getenv("DISPLAY_CONTROL", "off")
        self.slideshow_enabled = os.getenv("SLIDESHOW", "on") == "on"
        self.slideshow_folder = os.getenv(
            "SLIDESHOW_FOLDER", os.path.join(os.getcwd(), "./pictures")
        )
        self.slideshow_transition_seconds = int(
            os.getenv("SLIDESHOW_TRANSITION_SECONDS", 15)
        )
        self.slideshow_clock_ratio = int(os.getenv("SLIDESHOW_CLOCK_RATIO", 0)) / 100
        self.clock_size = int(os.getenv("CLOCK_SIZE", 0))
        self.clock_offset = int(os.getenv("CLOCK_OFFSET", 0))
        self.index_file = os.getenv("INDEX_FILE", "index.html")
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", 5006))

        self._validate_config()
        logger.info("Configuration loaded successfully.")

    def _validate_config(self):
        """Validate critical environment variables."""
        if not self.name:
            logger.warning("NAME environment variable is not set.")
        if not os.path.isdir(self.slideshow_folder):
            logger.warning(f"Slideshow folder does not exist: {self.slideshow_folder}")

    def save(self, updates):
        """Update the .env file with new values."""
        logger.info("Updating .env file with new settings.")
        env_vars = self._read_env_file()
        env_vars.update(updates)
        self._write_env_file(env_vars)
        self.load()

    def migrage_legacy(self):
        """Migrate old environment variables from legacy files."""
        if os.path.exists("roon_token.txt") and os.path.exists(".env"):
            self._migrate_legacy_file("roon_token.txt", "ROON_API_TOKEN")
            self._migrate_legacy_file(os.getenv("ROON_CORE_ID_FNAME"), "ROON_CORE_ID")

            existing_env_vars = self._read_env_file(skip_keys=["^ROON.+FNAME$"])
            self._write_env_file(existing_env_vars)

    def _read_env_file(self, skip_keys=None):
        """Read the .env file into a dictionary."""
        env_vars = {}
        skip_keys = skip_keys or []
        try:
            with open(".env", "r") as env_file:
                for line in env_file:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        if any(re.match(exp, key) for exp in skip_keys):
                            continue
                        env_vars[key] = os.getenv(key, value)

        except FileNotFoundError:
            logger.warning(".env file not found. Creating a new one.")
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")

        if "LOCK_SETTINGS" not in env_vars:
            env_vars["LOCK_SETTINGS"] = "off"
            os.environ["LOCK_SETTINGS"] = env_vars["LOCK_SETTINGS"]

        return env_vars

    def _write_env_file(self, env_vars):
        """Write a dictionary of environment variables to the .env file."""
        try:
            if "LOCK_SETTINGS" not in env_vars:
                env_vars["LOCK_SETTINGS"] = "off"

            logger.info("Saving setup data to .env")
            with open(".env", "w") as env_file:
                for key, value in sorted(env_vars.items()):
                    env_file.write(f"{key}={value}\n")
        except Exception as e:
            logger.error(f"Error writing to .env file: {e}")

    def _migrate_legacy_file(self, file_path, env_var_name):
        """Migrate a legacy file's content to an environment variable."""
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                os.environ[env_var_name] = f.read().strip()
            os.remove(file_path)
