"""Configuration management for Hive CLI."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".hive-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text())


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    # Restrict permissions - config contains API secrets
    os.chmod(CONFIG_FILE, 0o600)


def get_client():
    """Build an authenticated HiveClient from saved config."""
    from hive_cli.client import HiveClient

    config = get_config()
    url = config.get("url")
    api_key = config.get("api_key")
    api_secret = config.get("api_secret")

    if not all([url, api_key, api_secret]):
        raise SystemExit("Not logged in. Run: hive login")

    return HiveClient(url=url, api_key=api_key, api_secret=api_secret)
