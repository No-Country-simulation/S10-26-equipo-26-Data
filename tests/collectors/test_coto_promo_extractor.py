"""Extractor de Coto con promo — fixtures promo/ vs no_promo/ (HU 2.1).

Pendiente: capturar HTML real de producto en oferta y sin oferta.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="fixtures promo/no_promo pendientes (DOD HU 2.1)"
)


def test_parse_promo_stub():
    from scrapy.http import HtmlResponse, Request

    from src.collectors.extractors import ExtractionError, coto

    request = Request("https://www.cotodigital3.com.ar/sku/1")
    response = HtmlResponse(url=request.url, body="<html></html>", request=request)
    with pytest.raises(ExtractionError):
        coto.parse_product(response, producto_id=1)
