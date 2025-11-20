"""Taiwan PCC award (決標公告) XML fetcher."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Iterable, List, Optional

from ..models import TenderRecord
from .base import BaseFetcher


class TaiwanAwardFetcher(BaseFetcher):
    source_name = "taiwan-awards"

    def fetch(self) -> Iterable[TenderRecord]:
        urls: List[str] = self.config.get("download_urls", [])
        if not urls:
            return []

        keywords = self._normalize_terms(self.config.get("keywords"))
        max_records = int(self.config.get("max_records", 200))
        fetched = 0

        for url in urls:
            root = self._download_xml(url)
            for tender in root.findall(".//TENDER"):
                title = self._text(tender, "TENDER_NAME")
                if not title:
                    continue
                if keywords and not self._matches([title, self._text(tender, "TENDER_CASE_NO")], keywords):
                    continue
                record = self._normalize_award(tender, url)
                if record:
                    yield record
                    fetched += 1
                    if fetched >= max_records:
                        return

    def _download_xml(self, url: str) -> ET.Element:
        response = self._limited_request(
            self.source_name,
            "GET",
            url,
            headers={"User-Agent": "DroneTenderResearch/1.0"},
        )
        return ET.fromstring(response.content)

    def _normalize_award(self, node: ET.Element, source_url: str) -> Optional[TenderRecord]:
        case_no = self._text(node, "TENDER_CASE_NO")
        title = self._text(node, "TENDER_NAME")
        if not case_no or not title:
            return None

        supplier = self._text(node.find("BIDDER_LIST"), "BIDDER_SUPP_NAME") if node.find("BIDDER_LIST") is not None else None

        amount = self._safe_float(self._text(node, "TENDER_AWARD_PRICE"))
        award_date = self._parse_date(self._text(node, "AWARD_DATE"))

        payload = {}
        for child in node:
            if list(child):
                payload[child.tag] = {sub.tag: (sub.text or "").strip() for sub in child}
            else:
                payload[child.tag] = (child.text or "").strip()

        return TenderRecord(
            source_name=self.source_name,
            source_record_id=f"{case_no}",
            title=title,
            description=None,
            agency=self._text(node, "TENDER_ORG_NAME"),
            buyer_country="Taiwan",
            award_amount=amount,
            currency="TWD",
            award_date=award_date,
            supplier_name=supplier,
            data_source_url=source_url,
            raw_payload=payload,
            tags=[
                tag
                for tag in [
                    self._text(node, "PROCUREMENT_TYPE"),
                    self._text(node, "PROCUREMENT_ATTR"),
                    self._text(node, "TENDER_AWARD_WAY"),
                ]
                if tag
            ],
        )

    @staticmethod
    def _text(node: Optional[ET.Element], tag: str) -> Optional[str]:
        if node is None:
            return None
        child = node.find(tag)
        if child is None or child.text is None:
            return None
        return child.text.strip()

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _safe_float(value: Optional[str]) -> Optional[float]:
        try:
            return float(value.replace(",", "")) if value else None
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
    def _matches(values: List[Optional[str]], keywords: List[str]) -> bool:
        haystack = " ".join(v.lower() for v in values if v)
        if not haystack:
            return False
        return any(term in haystack for term in keywords)
