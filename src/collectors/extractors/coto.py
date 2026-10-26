"""Extractor de Coto.

La web de Coto (www.coto.com.ar) es una app de Angular: la página de producto
llega vacía (`<app-root></app-root>`) y el precio lo carga JavaScript después.
Por eso NO leemos el HTML, sino la misma página en formato JSON, que es lo que
pide el JavaScript del sitio:

    https://www.coto.com.ar/sitios/cdigi/productos/<slug>/_/R-<id>-<id>-200?format=json

Esa es la URL que va en targets/coto.csv. El JSON es de Oracle ATG/Endeca y los
datos están en `contents[0].Main[i].record.attributes`, donde cada valor es una
lista (ej. `"product.brand": ["NATURA"]`). La categoría sale de
`contents[0].Main[i].breadcrumbs`, que viene en orden (de la más general a la
más específica); `allAncestors.displayName` NO sirve porque viene en orden alfabético.

Precios:
- `sku.activePrice` es el precio regular ("Precio Contado").
- `product.dtoDescuentos` (un JSON dentro de un texto) trae las ofertas para
  todos, ej. "20%Dto" con `precioDesc` = precio final.
- `product.dtoDescuentosMediosPago` son descuentos con tarjeta/banco: no cuentan.
- OJO: `sku.dtoPrice.precio` NO es el precio del producto, es el precio por
  unidad de medida (por litro, por kilo).
"""

import json
from decimal import Decimal, InvalidOperation

from src.collectors.extractors import ExtractionError

SOURCE = "www.coto.com.ar"
# Categoría raíz que Coto agrega a todos los productos; no aporta nada.
ROOT_CATEGORY = "CotoDigital"


def _load_main_block(response) -> dict:
    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, AttributeError) as exc:
        raise ExtractionError(
            f"json_invalido: ¿la URL de targets tiene ?format=json? ({exc})"
        ) from exc
    try:
        mains = data["contents"][0]["Main"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ExtractionError("sin_main: el JSON no tiene contents[0].Main") from exc
    for block in mains:
        if (block.get("record") or {}).get("attributes"):
            return block
    raise ExtractionError("sin_record: el JSON no trae un producto")


def _first(attributes: dict, key: str) -> str | None:
    values = attributes.get(key) or []
    return values[0] if values else None


def _to_decimal(value) -> Decimal | None:
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, TypeError):
        return None
    return number if number > 0 else None


def _discount_price(attributes: dict) -> Decimal | None:
    """Precio más bajo entre las ofertas para todos (`product.dtoDescuentos`)."""
    raw = _first(attributes, "product.dtoDescuentos")
    if not raw:
        return None
    try:
        discounts = json.loads(raw)
    except json.JSONDecodeError:
        return None
    prices = [_to_decimal(d.get("precioDesc")) for d in discounts if isinstance(d, dict)]
    prices = [p for p in prices if p is not None]
    return min(prices) if prices else None


def _category(block: dict, attributes: dict) -> str | None:
    # breadcrumbs: [{"name": "CotoDigital"}, {"name": "Almacén"}, ..., {"name": "Mate"}]
    names = [
        b.get("name")
        for b in block.get("breadcrumbs") or []
        if isinstance(b, dict) and b.get("name") and b.get("name") != ROOT_CATEGORY
    ]
    # La categoría final (ej. "Yerba") a veces no está en las migas: la sumamos.
    leaf = _first(attributes, "parentCategory.displayName")
    if leaf and leaf not in names:
        names.append(leaf)
    if not names:
        return None
    return "/" + "/".join(names) + "/"


def parse_product(response, producto_id: int, external_id: str | None = None) -> dict:
    block = _load_main_block(response)
    attributes = block["record"]["attributes"]

    sku_id = _first(attributes, "sku.repositoryId")
    if external_id and sku_id != external_id:
        raise ExtractionError(f"sku_distinto: esperaba {external_id}, vino {sku_id}")

    name = _first(attributes, "sku.displayName") or _first(attributes, "product.displayName")
    if not name:
        raise ExtractionError("sin_nombre")

    regular = _to_decimal(_first(attributes, "sku.activePrice"))
    if regular is None:
        raise ExtractionError("sin_precio: sku.activePrice vacío o en 0")

    discounted = _discount_price(attributes)
    if discounted is not None and discounted < regular:
        price, precio_tachado, en_oferta = discounted, regular, True
    else:
        price, precio_tachado, en_oferta = regular, None, False

    return {
        "producto_id": producto_id,
        "source": SOURCE,
        "external_id": sku_id or external_id,
        "product_name": name,
        "price": price,
        "precio_tachado": precio_tachado,
        "en_oferta": en_oferta,
        "raw_presentation": name,
        "brand": _first(attributes, "product.brand"),
        "category": _category(block, attributes),
    }
