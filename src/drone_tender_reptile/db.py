"""SQLite helper storing normalized tender records."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import TenderRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS drone_tenders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    agency TEXT,
    buyer_country TEXT NOT NULL,
    award_amount REAL,
    currency TEXT,
    award_date TEXT,
    supplier_name TEXT,
    data_source_url TEXT,
    tags TEXT,
    raw_payload TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name, source_record_id)
);
"""


class TenderRepository:
    """Lightweight repository handling persistence."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def upsert(self, record: TenderRecord) -> None:
        """Insert or update a tender row."""

        payload = json.dumps(record.raw_payload or {}, ensure_ascii=False)
        tags = json.dumps(record.tags or [], ensure_ascii=False)

        self.conn.execute(
            """
            INSERT INTO drone_tenders (
                source_name, source_record_id, title, description, agency,
                buyer_country, award_amount, currency, award_date, supplier_name,
                data_source_url, tags, raw_payload, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(source_name, source_record_id)
            DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                agency=excluded.agency,
                buyer_country=excluded.buyer_country,
                award_amount=excluded.award_amount,
                currency=excluded.currency,
                award_date=excluded.award_date,
                supplier_name=excluded.supplier_name,
                data_source_url=excluded.data_source_url,
                tags=excluded.tags,
                raw_payload=excluded.raw_payload,
                updated_at=CURRENT_TIMESTAMP;
            """,
            (
                record.source_name,
                record.source_record_id,
                record.title,
                record.description,
                record.agency,
                record.buyer_country,
                record.award_amount,
                record.currency,
                record.award_date.isoformat() if record.award_date else None,
                record.supplier_name,
                record.data_source_url,
                tags,
                payload,
            ),
        )
        self.conn.commit()

    def bulk_upsert(self, records: Iterable[TenderRecord]) -> None:
        for record in records:
            self.upsert(record)

    def close(self) -> None:
        self.conn.close()
