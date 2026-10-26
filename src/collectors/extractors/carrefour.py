"""Extractor de Carrefour (AR).

Carrefour está hecho sobre VTEX IO. La página de producto (`.../p`) trae todos
los datos del producto en un JSON embebido:

    <template data-type="json" data-varname="__STATE__"><script>{...}</script></template>

Ese JSON es un diccionario "plano": cada objeto vive en su propia clave y los
objetos se apuntan entre sí con referencias `{"type": "id", "id": "<clave>"}`.
El camino hasta el precio es:

    Product:<slug> → items[i] (SKU) → sellers[0] → commertialOffer

Restricción de la decisión #5: NO rastrear `/busca/*`; las URLs vienen de targets/.
"""

import json
from decimal import Decimal
from urllib.parse import urlparse

from src.collectors.extractors import ExtractionError

SOURCE = "www.carrefour.com.ar"
STATE_XPATH = '//template[@data-varname="__STATE__"]/script/text()'


def _load_state(response) -> dict:
    raw = response.xpath(STATE_XPATH).get()
    if not raw:
        raise ExtractionError("sin_state: la página no trae el JSON __STATE__")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"state_invalido: {exc}") from exc


def _resolve(state: dict, value):
    """Si `value` es una referencia {"type": "id", "id": ...}, devuelve el objeto apuntado."""
    if isinstance(value, dict) and value.get("type") == "id":
        return state.get(value.get("id"), {})
    return value


def _find_product_key(state: dict, url: str) -> str:
    # La URL es https://www.carrefour.com.ar/<slug>/p y la clave es "Product:<slug>".
    parts = [p for p in urlparse(url).path.split("/") if p]
    if len(parts) >= 2 and parts[-1] == "p":
        key = f"Product:{parts[-2]}"
        if key in state:
            return key
    # Si no coincide (redirección, URL rara), aceptamos solo si hay un único producto.
    keys = [k for k in state if k.startswith("Product:") and "." not in k]
    if len(keys) == 1:
        return keys[0]
    raise ExtractionError(f"producto_no_encontrado: {len(keys)} productos en __STATE__")


def _pick_item(state: dict, product: dict, external_id: str | None) -> dict:
    items = [_resolve(state, ref) for ref in product.get("items") or []]
    if not items:
        raise ExtractionError("sin_items: el producto no tiene SKUs")
    if external_id:
        for item in items:
            if str(item.get("itemId")) == external_id:
                return item
        raise ExtractionError(f"sku_no_encontrado: external_id={external_id}")
    return items[0]


def _to_decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def parse_product(response, producto_id: int, external_id: str | None = None) -> dict:
    state = _load_state(response)
    product = state[_find_product_key(state, response.url)]
    item = _pick_item(state, product, external_id)

    sellers = [_resolve(state, ref) for ref in item.get("sellers") or []]
    if not sellers:
        raise ExtractionError("sin_vendedor: el SKU no tiene sellers")
    offer = _resolve(state, sellers[0].get("commertialOffer"))

    price = _to_decimal(offer.get("Price"))
    list_price = _to_decimal(offer.get("ListPrice"))
    # VTEX pone Price = 0 cuando no hay stock; eso no es un precio real.
    if not price or price <= 0 or not offer.get("AvailableQuantity"):
        raise ExtractionError("sin_stock: precio 0 o cantidad disponible 0")

    # Precio tachado solo si el de lista es mayor que el que se paga hoy.
    precio_tachado = list_price if list_price and list_price > price else None
    # en_oferta = precio tachado o un descuento visible para todos (discountHighlights).
    # Los "teasers" (ej. "Tarjeta Carrefour 15%") dependen del medio de pago y no cuentan.
    en_oferta = precio_tachado is not None or bool(offer.get("discountHighlights"))

    categories = _resolve(state, product.get("categories")) or {}
    category_list = categories.get("json") if isinstance(categories, dict) else categories
    # El nombre del SKU conserva la presentación ("1.5 l."); productName la pierde ("15 l").
    sku_name = item.get("name") or product.get("productName")
    if not sku_name:
        raise ExtractionError("sin_nombre")

    return {
        "producto_id": producto_id,
        "source": SOURCE,
        "external_id": str(item.get("itemId")) if item.get("itemId") else external_id,
        "product_name": sku_name,
        "price": price,
        "precio_tachado": precio_tachado,
        "en_oferta": en_oferta,
        "raw_presentation": sku_name,
        "brand": product.get("brand"),
        "category": category_list[0] if category_list else None,
    }
