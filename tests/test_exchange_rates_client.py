from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest

from src.exchange_rates.client import FXClientError, fetch_rates

URL = "https://fx.test/rates"

# Respuesta real de Bluelytics /v2/latest (decisión #2 ✅)
BLUELYTICS_OK = {
    "last_update": "2026-10-25T12:00:00+00:00",
    "oficial": {"value_buy": 990, "value_sell": 1000, "value_avg": 995},
    "blue": {"value_buy": 1190, "value_sell": 1200, "value_avg": 1195},
}


def test_respuesta_valida():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=BLUELYTICS_OK)

    observation = fetch_rates(URL, transport=httpx.MockTransport(handler))
    assert observation.tipo_cambio_oficial == Decimal("1000")
    assert observation.tipo_cambio_paralelo == Decimal("1200")
    assert observation.timestamp == datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def test_sin_timestamp_usa_el_de_la_consulta():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "oficial": {"value_sell": 1},
                "blue": {"value_sell": 1.5},
            },
        )

    observation = fetch_rates(URL, transport=httpx.MockTransport(handler))
    assert observation.timestamp.tzinfo is not None


def test_reintentos_agotados():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(500)

    with pytest.raises(FXClientError):
        fetch_rates(
            URL,
            retries=2,
            backoff_base=0,
            transport=httpx.MockTransport(handler),
        )
    assert calls["count"] == 3


def test_falta_una_tasa():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"oficial": {"value_sell": 1000}})

    with pytest.raises(FXClientError):
        fetch_rates(
            URL,
            retries=0,
            backoff_base=0,
            transport=httpx.MockTransport(handler),
        )


def test_url_vacia():
    with pytest.raises(FXClientError):
        fetch_rates("")
