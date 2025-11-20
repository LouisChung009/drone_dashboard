"""Abstract fetcher with shared helpers."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Iterable

import requests
from requests import Response

from ..models import TenderRecord
from ..rate_limit import RateLimiter

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Common fetcher scaffolding."""

    source_name: str

    def __init__(self, config: Dict, rate_limiter: RateLimiter):
        self.config = config
        self._rate_limiter = rate_limiter

    def _limited_request(self, key: str, method: str, url: str, **kwargs) -> Response:
        """Execute a requests call with rate limiting and manual retry."""

        retries = 0
        while retries < 5:
            self._rate_limiter.wait(key)
            try:
                response = requests.request(method, url, timeout=30, **kwargs)
            except requests.RequestException as exc:
                wait_for = 2**retries
                logger.warning(
                    "%s request error (%s). Retrying in %ss",
                    key,
                    exc,
                    wait_for,
                )
                retries += 1
                time.sleep(wait_for)
                continue

            if response.status_code in {429, 503}:
                wait_for = 2**retries
                logger.warning(
                    "%s received %s. Backing off for %ss",
                    key,
                    response.status_code,
                    wait_for,
                )
                retries += 1
                time.sleep(wait_for)
                continue

            response.raise_for_status()
            return response

        raise RuntimeError(f"{key} failed repeatedly with 429/503 responses")

    @abstractmethod
    def fetch(self) -> Iterable[TenderRecord]:  # pragma: no cover - interface
        """Return normalized tender records."""
        raise NotImplementedError
