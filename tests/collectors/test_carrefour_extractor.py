"""Extractor de Carrefour — tests sin red con fixtures HTML.

Fixture: fixtures/carrefour/aceite_natura.html, capturada con `scrapy shell`
de https://www.carrefour.com.ar/aceite-de-girasol-natura-15-l/p (sin oferta).
Restricción decisión #5: no rastrear /busca/*.
"""

from decimal import Decimal

import pytest
from scrapy.http import HtmlResponse, Request

from src.collectors.extractors import ExtractionError, carrefour
from src.models.observation import PriceObservation
from src.normalizers.presentation import parse_presentation

URL_ACEITE = "https://www.carrefour.com.ar/aceite-de-girasol-natura-15-l/p"


def _response(url: str, body: str) -> HtmlResponse:
    return HtmlResponse(url=url, body=body, encoding="utf-8", request=Request(url))


def test_parse_product_aceite_sin_oferta(load_fixture):
    response = _response(URL_ACEITE, load_fixture("carrefour/aceite_natura.html"))

    data = carrefour.parse_product(response, producto_id=2)

    assert data["producto_id"] == 2
    assert data["source"] == "www.carrefour.com.ar"
    assert data["external_id"] == "9423"
    assert data["product_name"] == "Aceite de girasol Natura 1.5 l."
    assert data["price"] == Decimal("7469")
    assert data["precio_tachado"] is None
    assert data["en_oferta"] is False
    assert data["disponible"] is True  # HU 2.1: AvailableQuantity > 0
    assert data["brand"] == "Natura"
    assert data["category"] == "/Almacén/Aceites y vinagres/Aceites comunes/"


def test_sin_stock_registra_disponible_false(load_fixture):
    """HU 2.1: cantidad 0 → observación con disponible=False (no se descarta)."""
    import re

    body = re.sub(
        r'"AvailableQuantity":\d+', '"AvailableQuantity":0', load_fixture("carrefour/aceite_natura.html")
    )
    response = _response(URL_ACEITE, body)

    data = carrefour.parse_product(response, producto_id=2)

    assert data["disponible"] is False
    assert data["price"] == Decimal("7469")


def test_presentacion_se_puede_normalizar(load_fixture):
    response = _response(URL_ACEITE, load_fixture("carrefour/aceite_natura.html"))

    data = carrefour.parse_product(response, producto_id=2)

    assert parse_presentation(data["raw_presentation"]) == (Decimal("1.5"), "l")


def test_cumple_el_contrato(load_fixture):
    from datetime import datetime, timezone

    response = _response(URL_ACEITE, load_fixture("carrefour/aceite_natura.html"))
    data = carrefour.parse_product(response, producto_id=2)
    ahora = datetime.now(timezone.utc)

    obs = PriceObservation(
        store="carrefour", source_url=URL_ACEITE, observed_at=ahora, fetched_at=ahora, **data
    )

    assert obs.price == Decimal("7469")


def test_external_id_inexistente_falla(load_fixture):
    response = _response(URL_ACEITE, load_fixture("carrefour/aceite_natura.html"))

    with pytest.raises(ExtractionError):
        carrefour.parse_product(response, producto_id=2, external_id="no-existe")


def test_pagina_sin_state_falla():
    response = _response("https://www.carrefour.com.ar/x/p", "<html></html>")

    with pytest.raises(ExtractionError):
        carrefour.parse_product(response, producto_id=1)


URL_PROMO = "https://www.carrefour.com.ar/tapas-para-pastelitos-carrefour-classic-24-u/p"


def test_promo_con_precio_tachado(load_fixture):
    """Fixture real CON oferta: list 3990 -> selling 3591 (10% off)."""
    response = _response(URL_PROMO, load_fixture("carrefour/promo.html"))

    data = carrefour.parse_product(response, producto_id=1)

    assert data["price"] == Decimal("3591")
    assert data["precio_tachado"] == Decimal("3990")
    assert data["en_oferta"] is True
    assert data["precio_tachado"] > data["price"]


def test_pagina_404_sin_producto_falla(load_fixture):
    response = _response(
        "https://www.carrefour.com.ar/producto-que-no-existe-123456/p",
        load_fixture("carrefour/empty.html"),
    )

    with pytest.raises(ExtractionError):
        carrefour.parse_product(response, producto_id=1)
