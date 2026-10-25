"""Cliente FX genérico (HU 3.1) — proveedor **Bluelytics** (decisión #2 ✅ 2026-10-25).

GET https://api.bluelytics.com.ar/v2/latest devuelve oficial + paralelo (blue) en una
sola respuesta, sin API key:

    {"oficial": {"value_buy": ..., "value_sell": ..., "value_avg": ...},
     "blue":    {"value_buy": ..., "value_sell": ..., "value_avg": ...},
     "last_update": "2026-10-23T19:45:56.466322-03:00"}

- `tipo_cambio_*` = `value_sell` (venta ARS por USD).
- `timestamp` = `last_update` de la fuente (efectivo); si no existe, el de la consulta.
  Como `last_update` cambia solo cuando la fuente actualiza, el upsert por PK de
  `historial_divisas` es idempotente entre corridas horarias.
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
    timestamp = payload.get("last_update") or datetime.now(timezone.utc).isoformat()
    return ExchangeRateObservation(
        timestamp=timestamp,
        tipo_cambio_oficial=Decimal(str(payload["oficial"]["value_sell"])),
        tipo_cambio_paralelo=Decimal(str(payload["blue"]["value_sell"])),
    )
