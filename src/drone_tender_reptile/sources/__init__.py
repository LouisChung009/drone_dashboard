"""Source-specific fetchers that comply with each country's open data rules."""

from .sam_gov import SamGovFetcher
from .canada import CanadaOpenDataFetcher
from .canada_tenders import CanadaTenderCsvFetcher
from .canada_awards import CanadaAwardCsvFetcher
from .australia import AusTenderDataGovFetcher
from .japan import JapanGepsFetcher
from .taiwan import TaiwanPccFetcher
from .taiwan_tender import TaiwanTenderFetcher
from .taiwan_award import TaiwanAwardFetcher

__all__ = [
    "SamGovFetcher",
    "CanadaOpenDataFetcher",
    "CanadaTenderCsvFetcher",
    "CanadaAwardCsvFetcher",
    "AusTenderDataGovFetcher",
    "JapanGepsFetcher",
    "TaiwanPccFetcher",
    "TaiwanTenderFetcher",
    "TaiwanAwardFetcher",
]
