"""Tests de unidad: contrato de escritura en precios_historicos (HU 2.4).

Sin red ni BD: validan la sentencia INSERT y los parametros, incluida la
columna `raw_presentation` (decision #6) que consume el detector de
reduflacion del Backend.
"""

from datetime import UTC, datetime
from decimal import Decimal

from src.models.observation import PriceObservation
from src.persistence.postgres import (
    _INSERT_OBSERVACION,
    _observation_params,
)


def _observacion(**overrides) -> PriceObservation:
    base = {
        "store": "carrefour",
        "producto_id": 3,
        "price": Decimal("500.00"),
        "precio_tachado": None,
        "en_oferta": False,
        "observed_at": datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
        "fx_rate": Decimal("1500.0000"),
        "price_usd": Decimal("0.33"),
        "source": "carrefour",
        "external_id": "123",
        "source_url": "https://www.carrefour.com.ar/p/123",
        "product_name": "Yerba 500 g",
        "raw_presentation": "Yerba 500 g",
        "brand": "Playadito",
        "category": "Yerba",
        "fetched_at": datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
        "currency_code": "ARS",
    }
    base.update(overrides)
    return PriceObservation.model_validate(base)


def test_insert_incluye_raw_presentation_y_disponible() -> None:
    assert "raw_presentation" in _INSERT_OBSERVACION
    assert "disponible" in _INSERT_OBSERVACION
    columnas = _INSERT_OBSERVACION.split("VALUES")[0]
    assert columnas.count(",") == 9  # 10 columnas
    assert _INSERT_OBSERVACION.count("%s") == 10


def test_params_llevan_presentacion_fx_y_disponible() -> None:
    obs = _observacion(disponible=True)
    params = _observation_params(obs, tienda_id=2)

    assert len(params) == 10
    assert params[1] == 3  # producto_id
    assert params[2] == 2  # tienda_id
    assert params[3] == Decimal("500.00")  # precio_local
    assert params[6] == Decimal("1500.0000")  # tipo_cambio_usado
    assert params[7] == Decimal("0.33")  # precio_usd
    assert params[8] == "Yerba 500 g"  # raw_presentation
    assert params[9] is True  # disponible (HU 2.1)


def test_params_disponible_desconocido_por_defecto() -> None:
    obs = _observacion(raw_presentation=None)
    params = _observation_params(obs, tienda_id=1)

    assert params[8] is None  # raw_presentation ausente
    assert params[9] is None  # disponible desconocido (ej. Coto)


def test_params_disponible_false_se_persiste() -> None:
    obs = _observacion(disponible=False)
    params = _observation_params(obs, tienda_id=1)

    assert params[9] is False

def test_upsert_store_product_sql() -> None:
    from src.persistence.postgres import _UPSERT_STORE_PRODUCT

    assert "ON CONFLICT (tienda_id, external_id)" in _UPSERT_STORE_PRODUCT
    assert "store_products" in _UPSERT_STORE_PRODUCT
    assert _UPSERT_STORE_PRODUCT.count("%s") == 7
