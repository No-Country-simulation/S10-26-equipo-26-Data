"""Extractor de Carrefour — tests sin red con fixtures HTML.

Pendiente (DOR HU 1.3): capturar fixtures/carrefour/*.html.
Restricción decisión #5: no rastrear /busca/*.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="fixture HTML pendiente: capturar con scrapy shell (DOR HU 1.3)"
)


def test_parse_product_stub():
    from scrapy.http import HtmlResponse, Request

    from src.collectors.extractors import ExtractionError, carrefour

    request = Request("https://www.carrefour.com.ar/p/1")
    response = HtmlResponse(url=request.url, body="<html></html>", request=request)
    with pytest.raises(ExtractionError):
        carrefour.parse_product(response, producto_id=1)
