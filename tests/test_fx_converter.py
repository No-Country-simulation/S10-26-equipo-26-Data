from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.fx.converter import (
    FXUnavailableError,
    MemoryRateProvider,
    get_rate_as_of,
    to_usd,
)

T0 = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
ROWS = [
    (T0, Decimal("1000"), Decimal("1200")),
    (T0 + timedelta(hours=1), Decimal("1100"), Decimal("1300")),
]


@pytest.fixture
def provider():
    return MemoryRateProvider(ROWS)


def test_timestamp_exacto(provider):
    assert get_rate_as_of(T0 + timedelta(hours=1), provider) == Decimal("1100")


def test_timestamp_intermedio_toma_la_anterior(provider):
    assert get_rate_as_of(T0 + timedelta(minutes=30), provider) == Decimal("1000")


def test_anterior_al_primero_usa_la_mas_antigua(provider):
    assert get_rate_as_of(T0 - timedelta(minutes=1), provider) == Decimal("1000")


def test_tipo_paralelo(provider):
    assert (
        get_rate_as_of(T0 + timedelta(hours=1), provider, tipo="paralelo")
        == Decimal("1300")
    )


def test_proveedor_vacio_lanza_error():
    with pytest.raises(FXUnavailableError):
        get_rate_as_of(T0, MemoryRateProvider([]))


def test_tipo_desconocido(provider):
    with pytest.raises(ValueError):
        get_rate_as_of(T0, provider, tipo="blue")


def test_to_usd_divide_y_redondea():
    assert to_usd(Decimal("2000"), Decimal("1000")) == Decimal("2.00")


def test_to_usd_rechaza_fx_no_positiva():
    with pytest.raises(ValueError):
        to_usd(Decimal("100"), Decimal("0"))
