from datetime import datetime, timezone
from decimal import Decimal


def build_observation() -> dict:
    """Observación sintética válida para el DOD de la HU 0.3 (sin red, sin BD)."""
    now = datetime.now(timezone.utc)
    return {
        "store": "coto",
        "producto_id": 1,
        "price": Decimal("1299.99"),
        "precio_tachado": Decimal("1599.99"),
        "en_oferta": True,
        "observed_at": now,
        "fx_rate": None,
        "price_usd": None,
        "source": "fake.local",
        "external_id": "FAKE-1",
        "source_url": "https://fake.local/producto/1",
        "product_name": "Producto de ejemplo 500 g",
        "raw_presentation": "500 g",
        "brand": "Marca de ejemplo",
        "category": "Alimentos y Bebidas",
        "fetched_at": now,
        "currency_code": "ARS",
    }
