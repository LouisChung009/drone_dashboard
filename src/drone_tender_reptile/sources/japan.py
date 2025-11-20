"""Japanese GEPS / JGP open data fetcher.

Data Source:
- Japan: GEPS/JGP published CSV/PDF datasets (download_url configured via YAML)
"""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime
from typing import Iterable, Optional

from ..models import TenderRecord
from .base import BaseFetcher


class JapanGepsFetcher(BaseFetcher):
    source_name = "japan-geps"

    def fetch(self) -> Iterable[TenderRecord]:
        if not self.config.get("enabled"):
            return []

        download_url: str = self.config["download_url"]
        file_type = self.config.get("file_type", "zip_csv")
        if file_type != "zip_csv":
            raise ValueError("Japan fetcher currently supports only zip-wrapped CSVs.")

        csv_cfg = self.config.get("csv", {})
        encoding = csv_cfg.get("encoding", "utf-8")
        delimiter = csv_cfg.get("delimiter", ",")
        field_map = csv_cfg.get("field_map", {})

        response = self._limited_request(
            self.source_name,
            "GET",
            download_url,
            headers={"User-Agent": "DroneTenderResearch/1.0"},
        )
        content = io.BytesIO(response.content)
        with zipfile.ZipFile(content) as archive:
            csv_name = next(
                (
                    name
                    for name in archive.namelist()
                    if name.lower().endswith(".csv")
                ),
                None,
            )
            if not csv_name:
                raise RuntimeError("No CSV file found inside GEPS zip archive.")
            with archive.open(csv_name) as csv_file:
                text_stream = io.TextIOWrapper(csv_file, encoding=encoding, newline="")
                reader = csv.DictReader(text_stream, delimiter=delimiter)
                for row in reader:
                    record = self._normalize_row(row, field_map)
                    if record:
                        yield record

    def _normalize_row(self, row: dict, field_map: dict) -> Optional[TenderRecord]:
        notice_id = row.get(field_map.get("notice_id", "NoticeID"))
        title = row.get(field_map.get("title", "ItemName"))
        if not notice_id or not title:
            return None

        amount = self._safe_float(row.get(field_map.get("award_amount", "AwardAmount")))
        currency = field_map.get("currency", "JPY")
        award_date = self._parse_date(
            row.get(field_map.get("award_date", "ContractDate"))
        )

        return TenderRecord(
            source_name=self.source_name,
            source_record_id=str(notice_id),
            title=title,
            description=row.get(field_map.get("description", "Summary")),
            agency=row.get(field_map.get("agency", "ProcuringEntity")),
            buyer_country="Japan",
            award_amount=amount,
            currency=currency,
            award_date=award_date,
            supplier_name=row.get(field_map.get("supplier_name", "Winner")),
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
