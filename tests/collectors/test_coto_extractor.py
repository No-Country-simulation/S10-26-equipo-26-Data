"""Extractores de Coto — tests sin red con fixtures HTML.

Pendiente (DOR HU 1.3): capturar fixtures/coto/*.html con
`scrapy shell "<url real>"` → `save_response` y reemplazar el test stub.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="fixture HTML pendiente: capturar con scrapy shell (DOR HU 1.3)"
)


def test_parse_product_stub():
    from scrapy.http import HtmlResponse, Request

    from src.collectors.extractors import ExtractionError, coto

    request = Request("https://www.cotodigital3.com.ar/sku/1")
    response = HtmlResponse(url=request.url, body="<html></html>", request=request)
    with pytest.raises(ExtractionError):
        coto.parse_product(response, producto_id=1)
