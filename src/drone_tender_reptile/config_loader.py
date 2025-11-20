"""YAML configuration helpers."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict

from .settings import BASE_DIR

CONFIG_PATH = BASE_DIR / "config" / "sources.yaml"


def load_sources_config(path: Path | None = None) -> Dict[str, Any]:
    cfg_path = path or CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"Cannot find configuration file at {cfg_path}")

    with cfg_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}
