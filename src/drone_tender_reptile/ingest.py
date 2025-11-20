"""Command line entry point for the compliant ingestor."""

from __future__ import annotations

import argparse
import logging
from typing import Dict, Iterable, List, Type

from .config_loader import load_sources_config
from .db import TenderRepository
from .models import TenderRecord
from .rate_limit import RateLimiter
from .settings import settings
from .sources import (
    AusTenderDataGovFetcher,
    CanadaAwardCsvFetcher,
    CanadaOpenDataFetcher,
    CanadaTenderCsvFetcher,
    JapanGepsFetcher,
    SamGovFetcher,
    TaiwanAwardFetcher,
    TaiwanPccFetcher,
    TaiwanTenderFetcher,
)
from .sources.base import BaseFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("drone-tender-ingest")

FETCHER_MAP: Dict[str, Type[BaseFetcher]] = {
    "usa": SamGovFetcher,
    "canada": CanadaOpenDataFetcher,
    "canada_tenders": CanadaTenderCsvFetcher,
    "canada_awards": CanadaAwardCsvFetcher,
    "australia": AusTenderDataGovFetcher,
    "japan": JapanGepsFetcher,
    "taiwan": TaiwanPccFetcher,
    "taiwan_tenders": TaiwanTenderFetcher,
    "taiwan_awards": TaiwanAwardFetcher,
}


def run_ingest(selected_sources: List[str] | None = None) -> None:
    config = load_sources_config()
    repo = TenderRepository(settings.database_path)
    limiter = RateLimiter(interval_seconds=1.0)

    try:
        for source_key, source_cfg in config.items():
            if selected_sources and source_key not in selected_sources:
                continue
            if not source_cfg.get("enabled"):
                logger.info("Skipping %s (disabled in config)", source_key)
                continue
            fetcher_cls = FETCHER_MAP.get(source_key)
            if not fetcher_cls:
                logger.warning("No fetcher registered for %s", source_key)
                continue
            fetcher = fetcher_cls(source_cfg, limiter)
            logger.info("Fetching %s tenders...", source_key)
            count = 0
            for record in fetcher.fetch():
                repo.upsert(record)
                count += 1
            logger.info("Stored %s records for %s", count, source_key)
    finally:
        repo.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local drone procurement database using only permitted open data APIs."
        )
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        help="Optional subset of source keys to ingest (usa canada australia japan taiwan)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_ingest(args.sources)


if __name__ == "__main__":
    main()
