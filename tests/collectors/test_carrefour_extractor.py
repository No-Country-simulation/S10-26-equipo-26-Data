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
    assert data["brand"] == "Natura"
    assert data["category"] == "/Almacén/Aceites y vinagres/Aceites comunes/"


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
