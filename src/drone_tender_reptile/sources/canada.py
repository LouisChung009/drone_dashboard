"""Canada Open Government CKAN dataset fetcher.

Data Source:
- Canada: Open Government Portal CKAN API
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from ..models import TenderRecord
from ..settings import settings
from .base import BaseFetcher


class CanadaOpenDataFetcher(BaseFetcher):
    source_name = "canada-open-data"

    def fetch(self) -> Iterable[TenderRecord]:
        resource_id: str = self.config["resource_id"]
        datastore_url: str = self.config["datastore_url"]
        max_records: int = int(self.config.get("max_records", 500))
        search_terms = self._normalize_terms(self.config.get("search_text"))
        scan_limit = int(self.config.get("scan_limit", max_records * 10))
        owner_org_whitelist = {
            entry.lower() for entry in self.config.get("owner_org_whitelist", [])
        }

        sort_field: Optional[str] = self.config.get("sort_field")
        sort_order: str = str(self.config.get("sort_order", "desc"))

        batch_size = 100
        offset = 0
        fetched = 0

        headers = {"User-Agent": "DroneTenderResearch/1.0"}
        if settings.canada_token:
            headers["Authorization"] = f"Bearer {settings.canada_token}"

        scanned = 0
        while fetched < max_records and scanned < scan_limit:
            limit = min(batch_size, scan_limit - scanned)
            params = {
                "resource_id": resource_id,
                "limit": limit,
                "offset": offset,
            }
            if sort_field:
                params["sort"] = f"{sort_field} {sort_order}".strip()
            response = self._limited_request(
                self.source_name,
                "GET",
                datastore_url,
                params=params,
                headers=headers,
            )
            payload = response.json()
            result = payload.get("result", {})
            records = result.get("records", [])
            if not records:
                break

            for record in records:
                if owner_org_whitelist and (
                    (record.get("owner_org") or "").lower() not in owner_org_whitelist
                ):
                    continue
                if search_terms and not self._matches_terms(record, search_terms):
                    continue
                normalized = self._normalize_record(record)
                if not normalized:
                    continue
                yield normalized
                fetched += 1
                if fetched >= max_records:
                    break

            offset += limit
            scanned += len(records)
            if len(records) < limit:
                break

    def _normalize_record(self, record: dict) -> Optional[TenderRecord]:
        reference = record.get("reference_number")
        descriptor = record.get("description_en") or record.get("description_fr")
        if not reference or not descriptor:
            return None

        contract_value = self._safe_float(record.get("contract_value"))
        award_date = self._parse_date(record.get("contract_date"))

        return TenderRecord(
            source_name=self.source_name,
            source_record_id=str(reference),
            title=descriptor,
            description=record.get("comments_en") or record.get("comments_fr"),
            agency=record.get("owner_org_title"),
            buyer_country="Canada",
            award_amount=contract_value,
            currency="CAD",
            award_date=award_date,
            supplier_name=record.get("vendor_name"),
            data_source_url=record.get("record_url"),
            raw_payload=record,
            tags=[
                tag
                for tag in [
                    record.get("commodity_code"),
                    record.get("trade_agreement"),
                ]
                if tag
            ],
        )

    @staticmethod
    def _parse_date(value: Optional[str]):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None

    @staticmethod
    def _safe_float(value: Optional[str]) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_terms(value) -> List[str]:
        if not value:
            return []
        if isinstance(value, str):
            return [value.lower()]
        return [str(entry).lower() for entry in value if entry]

    @staticmethod
    def _matches_terms(record: dict, terms: List[str]) -> bool:
        search_fields = [
            "description_en",
            "description_fr",
            "comments_en",
            "comments_fr",
            "vendor_name",
            "commodity_code",
        ]
        haystack = " ".join(str(record.get(field) or "") for field in search_fields).lower()
        if not haystack.strip():
            return False
        return any(term in haystack for term in terms)
