"""CanadaBuys award notice open-data fetcher (CSV downloads).

Data Source:
- Canada: CanadaBuys award notice CSV exports
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Iterable, List, Optional

import requests

from ..models import TenderRecord
from .base import BaseFetcher

logger = logging.getLogger(__name__)


class CanadaAwardCsvFetcher(BaseFetcher):
    source_name = "canada-awards"

    def fetch(self) -> Iterable[TenderRecord]:
        urls: List[str] = self.config.get("download_urls", [])
        if not urls:
            raise RuntimeError("Canada award configuration requires download_urls")

        keywords = self._normalize_terms(self.config.get("keywords"))
        max_records = int(self.config.get("max_records", 200))
        fetched = 0

        for url in urls:
            for row in self._iter_csv(url):
                if keywords and not self._matches(row, keywords):
                    continue
                record = self._normalize(row)
                if not record:
                    continue
                yield record
                fetched += 1
                if fetched >= max_records:
                    return

    def _iter_csv(self, url: str):
        logger.info("Downloading CanadaBuys award CSV %s", url)
        with requests.get(
            url,
            headers={"User-Agent": "DroneTenderResearch/1.0"},
            timeout=60,
        ) as resp:
            resp.raise_for_status()
            text_stream = io.StringIO(resp.content.decode("utf-8-sig"))
            reader = csv.DictReader(text_stream)
            for row in reader:
                yield row

    def _normalize(self, row: dict) -> Optional[TenderRecord]:
        reference = row.get("referenceNumber-numeroReference")
        title = row.get("title-titre-eng") or row.get("title-titre-fra")
        if not reference or not title:
            return None

        award_date = self._parse_date(row.get("contractAwardDate-dateAttributionContrat"))
        amount = self._safe_float(row.get("contractAmount-montantContrat"))

        return TenderRecord(
            source_name=self.source_name,
            source_record_id=str(reference),
            title=title,
            description=row.get("awardDescription-descriptionAttribution-eng")
            or row.get("awardDescription-descriptionAttribution-fra"),
            agency=row.get("contractingEntityName-nomEntitContractante-eng")
            or row.get("contractingEntityName-nomEntitContractante-fra"),
            buyer_country="Canada",
            award_amount=amount,
            currency=row.get("contractCurrency-contratMonnaie"),
            award_date=award_date,
            supplier_name=row.get("supplierLegalName-nomLegalFournisseur-eng")
            or row.get("supplierLegalName-nomLegalFournisseur-fra"),
            data_source_url=None,
            raw_payload=row,
            tags=[
                tag
                for tag in [
                    row.get("gsin-nibs"),
                    row.get("unspsc"),
                    row.get("procurementCategory-categorieApprovisionnement"),
                ]
                if tag
            ],
        )

    @staticmethod
    def _safe_float(value: Optional[str]) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _normalize_terms(value) -> List[str]:
        if not value:
            return []
        if isinstance(value, str):
            return [value.lower()]
        return [str(entry).lower() for entry in value if entry]

    def _matches(self, row: dict, keywords: List[str]) -> bool:
        hay_fields = [
            "title-titre-eng",
            "title-titre-fra",
            "awardDescription-descriptionAttribution-eng",
            "awardDescription-descriptionAttribution-fra",
            "gsinDescription-nibsDescription-eng",
            "gsinDescription-nibsDescription-fra",
            "unspscDescription-eng",
            "unspscDescription-fra",
            "supplierLegalName-nomLegalFournisseur-eng",
            "supplierLegalName-nomLegalFournisseur-fra",
        ]
        haystack = " ".join(str(row.get(field) or "") for field in hay_fields).lower()
        return any(term in haystack for term in keywords)
