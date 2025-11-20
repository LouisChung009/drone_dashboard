"""AusTender historical dataset fetcher via data.gov.au CKAN API.

Data Source:
- Australia: data.gov.au Historical Australian Government Contract Notice Data
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from ..models import TenderRecord
from ..settings import settings
from .base import BaseFetcher


class AusTenderDataGovFetcher(BaseFetcher):
    source_name = "aus-data-gov"

    def fetch(self) -> Iterable[TenderRecord]:
        datastore_url: str = self.config["datastore_url"]
        resource_id: str = self.config["resource_id"]
        search_text: Optional[str] = self.config.get("search_text")
        max_records: int = int(self.config.get("max_records", 500))

        headers = {"User-Agent": "DroneTenderResearch/1.0"}
        if settings.austender_token:
            headers["Authorization"] = f"Bearer {settings.austender_token}"

        offset = 0
        fetched = 0
        batch_size = 100

        while fetched < max_records:
            params = {
                "resource_id": resource_id,
                "limit": min(batch_size, max_records - fetched),
                "offset": offset,
            }
            if search_text:
                params["q"] = search_text

            response = self._limited_request(
                self.source_name, "GET", datastore_url, params=params, headers=headers
            )
            result = response.json().get("result", {})
            records = result.get("records", [])
            if not records:
                break

            for record in records:
                normalized = self._normalize(record)
                if not normalized:
                    continue
                yield normalized
                fetched += 1
                if fetched >= max_records:
                    break

            offset += batch_size
            if len(records) < batch_size:
                break

    def _normalize(self, record: dict) -> Optional[TenderRecord]:
        contract_id = record.get("Contract ID")
        description = record.get("Description")
        if not contract_id or not description:
            return None

        award_date = self._parse_date(record.get("Publish Date"))
        award_amount = self._safe_float(record.get("Value"))

        return TenderRecord(
            source_name=self.source_name,
            source_record_id=str(contract_id),
            title=description,
            description=f"{record.get('UNSPSC Title') or ''}".strip() or None,
            agency=record.get("Agency Name"),
            buyer_country="Australia",
            award_amount=award_amount,
            currency="AUD",
            award_date=award_date,
            supplier_name=record.get("Supplier Name"),
            data_source_url=None,
            raw_payload=record,
            tags=[
                tag
                for tag in [
                    record.get("UNSPSC Code"),
                    record.get("Procurement Method"),
                ]
                if tag
            ],
        )

    @staticmethod
    def _parse_date(value: Optional[str]):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
