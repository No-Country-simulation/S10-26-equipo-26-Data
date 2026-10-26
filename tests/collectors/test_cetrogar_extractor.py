"""Extractor de Cetrogar — tests sin red con fixtures HTML.

Fixture: fixtures/cetrogar/smart_tv_samsung_50.html, capturada el 26/10/2026 de
https://www.cetrogar.com.ar/tv-led-50--samsung-un50m60hagxzb-mini-led-t-8324/p
En la página se veía: $749.999, tachado $849.999, "12% off".
Restricción robots.txt: no rastrear /s? ni /api/.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from scrapy.http import HtmlResponse, Request

from src.collectors.extractors import ExtractionError, cetrogar
from src.models.observation import PriceObservation

URL_TV = "https://www.cetrogar.com.ar/tv-led-50--samsung-un50m60hagxzb-mini-led-t-8324/p"


def _response(url: str, body: str) -> HtmlResponse:
    return HtmlResponse(url=url, body=body, encoding="utf-8", request=Request(url))


def test_tv_en_oferta(load_fixture):
    response = _response(URL_TV, load_fixture("cetrogar/smart_tv_samsung_50.html"))

    data = cetrogar.parse_product(response, producto_id=8)

    assert data["source"] == "www.cetrogar.com.ar"
    assert data["external_id"] == "8324"
    assert data["product_name"] == 'Smart Tv Led Samsung UN50M60HAGXZB 50" Mini Led T'
    assert data["price"] == Decimal("749999")
    assert data["precio_tachado"] == Decimal("849999")
    assert data["en_oferta"] is True
    assert data["brand"] == "Samsung"
    assert data["category"] == "/Tecnología/Tv y Video/Smart TV/"


def test_cumple_el_contrato(load_fixture):
    response = _response(URL_TV, load_fixture("cetrogar/smart_tv_samsung_50.html"))
    data = cetrogar.parse_product(response, producto_id=8)
    ahora = datetime.now(timezone.utc)

    obs = PriceObservation(
        store="cetrogar", source_url=URL_TV, observed_at=ahora, fetched_at=ahora, **data
    )

    assert obs.precio_tachado > obs.price


def test_sku_distinto_al_de_targets_falla(load_fixture):
    response = _response(URL_TV, load_fixture("cetrogar/smart_tv_samsung_50.html"))

    with pytest.raises(ExtractionError):
        cetrogar.parse_product(response, producto_id=8, external_id="9999")


def test_pagina_sin_next_data_falla():
    response = _response("https://www.cetrogar.com.ar/x/p", "<html></html>")

    with pytest.raises(ExtractionError):
        cetrogar.parse_product(response, producto_id=1)
