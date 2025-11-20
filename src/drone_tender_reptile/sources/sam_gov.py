"""SAM.gov Public Contract Opportunities API fetcher.

Data Source:
- USA: SAM.gov Public API (https://api.sam.gov/opportunities/v2/search)
"""

from __future__ import annotations

import logging
import json
from datetime import datetime, timedelta
from typing import Iterable, List, Optional

from ..models import TenderRecord
from ..settings import settings
from .base import BaseFetcher

logger = logging.getLogger(__name__)


class SamGovFetcher(BaseFetcher):
    source_name = "sam.gov"

    def fetch(self) -> Iterable[TenderRecord]:
        if not settings.sam_gov_api_key:
            raise RuntimeError("SAM_GOV_API_KEY is required to query SAM.gov")

        api_url: str = self.config["api_url"]
        keywords: List[str] = self.config.get("keywords", [])
        notice_types: List[str] = self.config.get("notice_types", [])
        min_amount: Optional[float] = self.config.get("min_award_amount_usd")
        max_records: int = int(self.config.get("max_records", 200))
        lookback_days: int = int(self.config.get("posted_within_days", 180))
        posted_to = datetime.utcnow()
        posted_from = posted_to - timedelta(days=lookback_days)
        posted_to_str = posted_to.strftime("%m/%d/%Y")
        posted_from_str = posted_from.strftime("%m/%d/%Y")

        batch_size = 100
        fetched = 0
        offset = 0

        while fetched < max_records:
            params = {
                "api_key": settings.sam_gov_api_key,
                "limit": min(batch_size, max_records - fetched),
                "offset": offset,
                "keywords": ",".join(keywords),
                "postedFrom": posted_from_str,
                "postedTo": posted_to_str,
            }
            if notice_types:
                params["notice_type"] = ",".join(notice_types)
            response = self._limited_request(
                self.source_name, "GET", api_url, params=params
            )
            payload = response.json()
            data = payload.get("opportunitiesData") or payload.get("data", [])
            if not data:
                break

            for item in data:
                record = self._normalize_item(item)
                if not record:
                    continue
                if min_amount and record.award_amount and record.award_amount < float(
                    min_amount
                ):
                    continue
                yield record
                fetched += 1
                if fetched >= max_records:
                    break

            offset += batch_size
            if len(data) < batch_size:
                break

    def _normalize_item(self, item: dict) -> Optional[TenderRecord]:
        notice_id = item.get("noticeId")
        title = item.get("title") or item.get("solicitationNumber")
        if not notice_id or not title:
            return None

        award = item.get("award", {}) or {}
        award_amount = self._safe_float(award.get("awardAmount"))
        currency = award.get("awardAmountCurrency") or "USD"
        award_date = self._parse_date(award.get("awardDate"))
        supplier = self._stringify(award.get("recipientName") or award.get("awardee"))

        return TenderRecord(
            source_name=self.source_name,
            source_record_id=str(notice_id),
            title=title.strip(),
            description=item.get("description"),
            agency=item.get("department") or item.get("organization"),
            buyer_country="USA",
            award_amount=award_amount,
            currency=currency,
            award_date=award_date,
            supplier_name=supplier,
            data_source_url=item.get("uiLink"),
            raw_payload=item,
            tags=[
                entry
                for entry in [
                    item.get("typeOfSetAsideDescription"),
                    item.get("naics"),
                ]
                if entry
            ],
        )

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        logger.debug("SAM.gov award date parse failure for %s", value)
        return None

    @staticmethod
    def _safe_float(value: Optional[str]) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _stringify(value):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
