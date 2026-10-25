"""Opción B (recomendada, decisión #1): ingesta vía API del Backend.

Endpoints por confirmar con Backend al resolverse la decisión #1:
    POST {API_URL}/ingest/prices
    POST {API_URL}/ingest/exchange-rates
"""

import logging

import httpx

from src.models.fx import ExchangeRateObservation
from src.models.observation import PriceObservation

logger = logging.getLogger(__name__)


class ApiWriter:
    def __init__(
        self,
        api_url: str,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        headers = {"X-API-Key": api_key} if api_key else {}
        self._base_url = api_url.rstrip("/") + "/"
        self._client = httpx.Client(base_url=self._base_url, headers=headers, timeout=15.0)

    def _post(self, path: str, payload: dict) -> None:
        response = self._client.post(path, json=payload)
        response.raise_for_status()

    def write(self, obs: PriceObservation) -> None:
        self._post("ingest/prices", obs.model_dump(mode="json"))

    def upsert(self, rate: ExchangeRateObservation) -> None:
        self._post("ingest/exchange-rates", rate.model_dump(mode="json"))

    def close(self) -> None:
        self._client.close()
