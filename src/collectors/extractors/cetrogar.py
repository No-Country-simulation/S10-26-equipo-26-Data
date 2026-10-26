"""Extractor de Cetrogar.

Cetrogar está hecha con VTEX FastStore, que usa Next.js. La página de producto
(`.../p`) trae todos los datos en un JSON embebido:

    <script id="__NEXT_DATA__" type="application/json">{...}</script>

El producto está en `props.pageProps.data.product`:
- `offers.offers[0].price`: lo que se paga hoy.
- `offers.offers[0].listPrice`: el precio de lista; si es mayor, es el tachado.
- `breadcrumbList`: Tecnología › Tv y Video › Smart TV › <producto>.

Restricción del robots.txt: NO rastrear `/s?` (buscador) ni `/api/`; las URLs
de producto vienen de targets/.
"""

import json
from decimal import Decimal, InvalidOperation

from src.collectors.extractors import ExtractionError

SOURCE = "www.cetrogar.com.ar"
NEXT_DATA_XPATH = '//script[@id="__NEXT_DATA__"]/text()'
IN_STOCK = "https://schema.org/InStock"


def _load_product(response) -> dict:
    raw = response.xpath(NEXT_DATA_XPATH).get()
    if not raw:
        raise ExtractionError("sin_next_data: la página no trae el JSON __NEXT_DATA__")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"next_data_invalido: {exc}") from exc
    try:
        product = data["props"]["pageProps"]["data"]["product"]
    except (KeyError, TypeError) as exc:
        raise ExtractionError("sin_producto: __NEXT_DATA__ no trae data.product") from exc
    if not isinstance(product, dict):
        raise ExtractionError("sin_producto: data.product vacío")
    return product


def _to_decimal(value) -> Decimal | None:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None
    return number if number > 0 else None


def _category(product: dict) -> str | None:
    items = (product.get("breadcrumbList") or {}).get("itemListElement") or []
    items = sorted(items, key=lambda i: i.get("position", 0))
    # El último elemento es el propio producto (su URL termina en /p): lo sacamos.
    names = [i.get("name") for i in items if i.get("name") and not str(i.get("item", "")).endswith("/p")]
    if not names:
        return None
    return "/" + "/".join(names) + "/"


def parse_product(response, producto_id: int, external_id: str | None = None) -> dict:
    product = _load_product(response)

    sku = str(product.get("sku") or "")
    if external_id and sku != external_id:
        raise ExtractionError(f"sku_distinto: esperaba {external_id}, vino {sku}")

    name = product.get("name")
    if not name:
        raise ExtractionError("sin_nombre")

    offers = (product.get("offers") or {}).get("offers") or []
    if not offers:
        raise ExtractionError("sin_oferta: el producto no tiene offers")
    offer = offers[0]
    if offer.get("availability") != IN_STOCK:
        raise ExtractionError(f"sin_stock: availability={offer.get('availability')}")

    price = _to_decimal(offer.get("price"))
    if price is None:
        raise ExtractionError("sin_precio: price vacío o en 0")
    list_price = _to_decimal(offer.get("listPrice"))

    precio_tachado = list_price if list_price and list_price > price else None

    return {
        "producto_id": producto_id,
        "source": SOURCE,
        "external_id": sku or external_id,
        "product_name": name,
        "price": price,
        "precio_tachado": precio_tachado,
        "en_oferta": precio_tachado is not None,
        "raw_presentation": name,
        "brand": (product.get("brand") or {}).get("name"),
        "category": _category(product),
    }
