import os
import unittest
from unittest.mock import patch

from medaudit.config import Settings


class SettingsTest(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_settings_load_defaults(self) -> None:
        self.assertEqual(Settings.from_env(), Settings())

    @patch.dict(
        os.environ,
        {"MEDAUDIT_ENV": "test", "MEDAUDIT_LOG_LEVEL": "debug"},
        clear=True,
    )
    def test_settings_load_environment(self) -> None:
        settings = Settings.from_env()

        self.assertEqual(settings.environment, "test")
        self.assertEqual(settings.log_level, "DEBUG")
