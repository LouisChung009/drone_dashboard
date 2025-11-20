"""Application settings and environment management."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    """Typed container for environment driven settings."""

    sam_gov_api_key: Optional[str]
    database_path: Path
    canada_token: Optional[str]
    austender_token: Optional[str]


def get_settings() -> Settings:
    """Return cached settings built from environment variables."""

    db_path = os.getenv("DRONE_TENDER_DB_PATH", BASE_DIR / "data" / "drone_tenders.db")
    if isinstance(db_path, str):
        db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        sam_gov_api_key=os.getenv("SAM_GOV_API_KEY"),
        database_path=db_path,
        canada_token=os.getenv("CANADA_OPEN_DATA_TOKEN"),
        austender_token=os.getenv("AUSTENDER_DATA_GOV_TOKEN"),
    )


settings = get_settings()
