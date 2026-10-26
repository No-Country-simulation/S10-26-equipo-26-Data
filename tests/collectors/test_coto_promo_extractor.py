"""Extractor de Coto con promo — fixtures promo/ vs no_promo/ (HU 2.1).

promo/aceite_natura.json: capturada el 26/10/2026 de
https://www.coto.com.ar/sitios/cdigi/productos/aceite-girasol-natura-botella-1-5-l-/_/R-00014076-00014076-200?format=json
En la página se veía: "20%Dto", $5.970,45, "Precio regular: $7.464,00".

no_promo/yerba_playadito.json: capturada el 26/10/2026 de
https://www.coto.com.ar/sitios/cdigi/productos/yerba-mate-suave-playadito-500-gr/_/R-00502007-00502007-200?format=json
Sin cartel de oferta; precio $2.800.
"""

from datetime import datetime, timezone
from decimal import Decimal

from scrapy.http import Request, TextResponse

from src.collectors.extractors import coto
from src.models.observation import PriceObservation
from src.normalizers.presentation import parse_presentation

URL_ACEITE = (
    "https://www.coto.com.ar/sitios/cdigi/productos/aceite-girasol-natura-botella-1-5-l-"
    "/_/R-00014076-00014076-200?format=json"
)
URL_YERBA = (
    "https://www.coto.com.ar/sitios/cdigi/productos/yerba-mate-suave-playadito-500-gr"
    "/_/R-00502007-00502007-200?format=json"
)


def _response(url: str, body: str) -> TextResponse:
    return TextResponse(url=url, body=body, encoding="utf-8", request=Request(url))


def test_aceite_en_oferta(load_fixture):
    response = _response(URL_ACEITE, load_fixture("coto/promo/aceite_natura.json"))

    data = coto.parse_product(response, producto_id=2)

    assert data["source"] == "www.coto.com.ar"
    assert data["external_id"] == "sku00014076"
    assert data["product_name"] == "Aceite Girasol NATURA Botella 1.5 L"
    assert data["price"] == Decimal("5970.45")
    assert data["precio_tachado"] == Decimal("7464")
    assert data["en_oferta"] is True
    assert data["brand"] == "NATURA"
    assert data["category"] == "/Almacén/Aceites y Condimentos/Aceites/Aceite Girasol/"


def test_no_usa_el_precio_por_litro(load_fixture):
    # dtoPrice.precio = 4976 es el precio por litro, no el del producto.
    response = _response(URL_ACEITE, load_fixture("coto/promo/aceite_natura.json"))

    data = coto.parse_product(response, producto_id=2)

    assert data["price"] != Decimal("4976")


def test_presentacion_se_puede_normalizar(load_fixture):
    response = _response(URL_ACEITE, load_fixture("coto/promo/aceite_natura.json"))

    data = coto.parse_product(response, producto_id=2)

    assert parse_presentation(data["raw_presentation"]) == (Decimal("1.5"), "l")


def test_cumple_el_contrato(load_fixture):
    response = _response(URL_ACEITE, load_fixture("coto/promo/aceite_natura.json"))
    data = coto.parse_product(response, producto_id=2)
    ahora = datetime.now(timezone.utc)

    obs = PriceObservation(
        store="coto", source_url=URL_ACEITE, observed_at=ahora, fetched_at=ahora, **data
    )

    assert obs.precio_tachado > obs.price


def test_yerba_sin_oferta(load_fixture):
    response = _response(URL_YERBA, load_fixture("coto/no_promo/yerba_playadito.json"))

    data = coto.parse_product(response, producto_id=3)

    assert data["external_id"] == "sku00502007"
    assert data["product_name"] == "Yerba Mate Suave PLAYADITO 500 Gr"
    assert data["price"] == Decimal("2800")
    assert data["precio_tachado"] is None
    assert data["en_oferta"] is False
    assert data["brand"] == "PLAYADITO"
    assert data["category"] == "/Almacén/Infusiones/Mate/Yerba/"
    assert parse_presentation(data["raw_presentation"]) == (Decimal("500"), "g")
