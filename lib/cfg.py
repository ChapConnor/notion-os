"""Load config/config.yml and the notion.env secret. Repo-root aware."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "config.yml"
SECRETS_DIR = Path.home() / ".config" / "notion-os"


def load() -> dict[str, Any]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise SystemExit(f"config file {CONFIG_PATH} did not parse to a mapping")
    return config


def notion_token() -> str:
    load_dotenv(SECRETS_DIR / "notion.env")
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise SystemExit(
            f"NOTION_TOKEN missing/empty in {SECRETS_DIR / 'notion.env'} "
            "(600). Paste the notion-os-mac secret there."
        )
    return token
