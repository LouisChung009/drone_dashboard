"""Data models shared across the ingestor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TenderRecord:
    """Normalized tender entry ready for persistence."""

    source_name: str
    source_record_id: str
    title: str
    description: Optional[str]
    agency: Optional[str]
    buyer_country: str
    award_amount: Optional[float]
    currency: Optional[str]
    award_date: Optional[datetime]
    supplier_name: Optional[str]
    data_source_url: Optional[str]
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


def as_db_tuple(record: TenderRecord) -> tuple:
    """Convert the dataclass to a tuple matching the DB schema."""

    return (
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
        record.tags,
        record.raw_payload,
    )
