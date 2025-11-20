"""Taiwan PCC OpenData XML fetcher.

Data Source:
- Taiwan: PCC OpenData XML/CSV downloads via data.gov.tw
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Iterable, Optional

from ..models import TenderRecord
from .base import BaseFetcher


class TaiwanPccFetcher(BaseFetcher):
    source_name = "taiwan-pcc"

    def fetch(self) -> Iterable[TenderRecord]:
        if not self.config.get("enabled"):
            return []

        download_url: str = self.config["download_url"]
        xml_cfg = self.config.get("xml", {})
        record_path = xml_cfg.get("record_path", ".//row")
        field_map = xml_cfg.get("field_map", {})

        response = self._limited_request(
            self.source_name,
            "GET",
            download_url,
            headers={"User-Agent": "DroneTenderResearch/1.0"},
        )
        root = ET.fromstring(response.content)
        for node in root.findall(record_path):
            record_dict = {child.tag: child.text for child in node}
            normalized = self._normalize(record_dict, field_map)
            if normalized:
                yield normalized

    def _normalize(self, row: dict, field_map: dict) -> Optional[TenderRecord]:
        notice_id = row.get(field_map.get("notice_id", "品項編號"))
        title = row.get(field_map.get("title", "標案名稱"))
        if not notice_id or not title:
            return None

        amount = self._safe_float(row.get(field_map.get("award_amount", "得標金額")))
        award_date = self._parse_date(row.get(field_map.get("award_date", "決標日期")))
        currency = field_map.get("currency", "TWD")

        return TenderRecord(
            source_name=self.source_name,
            source_record_id=str(notice_id),
            title=title,
            description=row.get(field_map.get("description", "標案摘要")),
            agency=row.get(field_map.get("agency", "標案機關名稱")),
            buyer_country="Taiwan",
            award_amount=amount,
            currency=currency,
            award_date=award_date,
            supplier_name=row.get(field_map.get("supplier_name", "得標廠商名稱")),
            data_source_url=self.config.get("download_url"),
            raw_payload=row,
            tags=[],
        )

    @staticmethod
    def _parse_date(value: Optional[str]):
        if not value:
            return None
        for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
