import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from cmdbroker.gui.config import Config, CONFIG_FILE, CONFIG_DIR

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

    def test_save_load(self):
        self.config.remotes = [{"name": "test", "address": "1.2.3.4"}]
        self.config.save()

        new_config = Config()
        self.assertEqual(new_config.remotes, [{"name": "test", "address": "1.2.3.4"}])

        # Check permissions
        self.assertEqual(oct(os.stat(CONFIG_DIR).st_mode & 0o777), '0o700')
        self.assertEqual(oct(os.stat(CONFIG_FILE).st_mode & 0o777), '0o600')

    @patch('keyring.set_password')
    @patch('keyring.get_password')
    @patch('keyring.delete_password')
    def test_keyring(self, mock_delete, mock_get, mock_set):
        mock_get.return_value = "secret"

        self.config.set_password("mykey", "secret")
        mock_set.assert_called_with("cmdbroker", "mykey", "secret")

        pw = self.config.get_password("mykey")
        self.assertEqual(pw, "secret")
        mock_get.assert_called_with("cmdbroker", "mykey")

        self.config.delete_password("mykey")
        mock_delete.assert_called_with("cmdbroker", "mykey")

if __name__ == '__main__':
    unittest.main()
