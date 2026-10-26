"""Extractor de Coto — tests sin red con fixtures JSON.

Coto es una app de Angular: el HTML llega vacío, así que el extractor lee la
versión `?format=json` de la página de producto (ver extractors/coto.py).
Los casos con y sin oferta están en test_coto_promo_extractor.py (HU 2.1).
"""

import pytest
from scrapy.http import Request, TextResponse

from src.collectors.extractors import ExtractionError, coto

URL = "https://www.coto.com.ar/sitios/cdigi/productos/x/_/R-1-1-200?format=json"


def _response(body: str) -> TextResponse:
    return TextResponse(url=URL, body=body, encoding="utf-8", request=Request(URL))


def test_html_vacio_de_angular_falla():
    # Esto es lo que devuelve la página normal (sin ?format=json).
    with pytest.raises(ExtractionError):
        coto.parse_product(_response("<html><app-root></app-root></html>"), producto_id=1)


def test_json_sin_producto_falla():
    with pytest.raises(ExtractionError):
        coto.parse_product(_response('{"contents": [{"Main": [{}]}]}'), producto_id=1)


def test_sku_distinto_al_de_targets_falla(load_fixture):
    response = _response(load_fixture("coto/promo/aceite_natura.json"))

    with pytest.raises(ExtractionError):
        coto.parse_product(response, producto_id=2, external_id="sku99999999")
