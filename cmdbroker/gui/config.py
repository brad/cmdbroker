import json
import os
from pathlib import Path

import keyring

CONFIG_DIR = Path.home() / ".config" / "cmdbroker"
CONFIG_FILE = CONFIG_DIR / "gui_config.json"
SERVICE_NAME = "cmdbroker"


class Config:
    def __init__(self):
        self.remotes = []
        self.listeners = []
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.remotes = data.get("remotes", [])
                    self.listeners = data.get("listeners", [])
            except Exception:
                pass

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Ensure directory is secure
        os.chmod(CONFIG_DIR, 0o700)

        data = {"remotes": self.remotes, "listeners": self.listeners}
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

        # Ensure file is secure
        os.chmod(CONFIG_FILE, 0o600)

    def set_password(self, key_path, password):
        keyring.set_password(SERVICE_NAME, str(key_path), password)

    def get_password(self, key_path):
        return keyring.get_password(SERVICE_NAME, str(key_path))

    def delete_password(self, key_path):
        try:
            keyring.delete_password(SERVICE_NAME, str(key_path))
        except keyring.errors.PasswordDeleteError:
            pass
