"""Cliente FX genérico (HU 3.1).

Decisión #2 pendiente (DolarAPI / Bluelytics / Open Exchange Rates): el proveedor
elegido debe poder devolver oficial + paralelo. Mientras tanto se asume este JSON:

    {"timestamp": "2026-10-25T12:00:00+00:00", "oficial": 1234.5, "paralelo": 1300.0}

`timestamp` opcional: si la fuente no lo expone, se usa el de la consulta.
Adaptar `_parse` a la respuesta real al resolverse la decisión #2.
"""

import logging
import time
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from pydantic import ValidationError

from src.models.fx import ExchangeRateObservation

logger = logging.getLogger(__name__)


class FXClientError(Exception):
    """La API de FX falló o devolvió algo inválido tras agotar reintentos."""


def fetch_rates(
    url: str,
    api_key: str | None = None,
    timeout: float = 10.0,
    retries: int = 2,
    backoff_base: float = 0.5,
    transport: httpx.BaseTransport | None = None,
) -> ExchangeRateObservation:
    """GET a la API FX con 2 reintentos + backoff (DOD HU 3.1)."""
    if not url:
        raise FXClientError("EXCHANGE_RATE_API_URL vacia")

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    last_error: Exception | None = None
    with httpx.Client(timeout=timeout, transport=transport, headers=headers) as client:
        for attempt in range(retries + 1):
            try:
                response = client.get(url)
                response.raise_for_status()
                return _parse(response.json())
            except (httpx.HTTPError, ValueError, KeyError, ValidationError) as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(backoff_base * (2**attempt))
    raise FXClientError(f"fx_fetch_fallido intentos={retries + 1} error={last_error}")


def _parse(payload: dict) -> ExchangeRateObservation:
    timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    return ExchangeRateObservation(
        timestamp=timestamp,
        tipo_cambio_oficial=Decimal(str(payload["oficial"])),
        tipo_cambio_paralelo=Decimal(str(payload["paralelo"])),
    )
