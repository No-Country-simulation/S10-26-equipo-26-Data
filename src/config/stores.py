from dataclasses import dataclass


@dataclass(frozen=True)
class Store:
    key: str
    nombre: str  # valor exacto en la BD (Railway) → tiendas.nombre
    dominio: str
    url_base: str


STORES: dict[str, Store] = {
    "coto": Store(
        key="coto",
        nombre="Coto",
        dominio="www.coto.com.ar",
        url_base="https://www.coto.com.ar",
    ),
    "carrefour": Store(
        key="carrefour",
        nombre="Carrefour",
        dominio="www.carrefour.com.ar",
        url_base="https://www.carrefour.com.ar",
    ),
    "cetrogar": Store(
        key="cetrogar",
        nombre="Cetrogar",
        dominio="www.cetrogar.com.ar",
        url_base="https://www.cetrogar.com.ar",
    ),
}
