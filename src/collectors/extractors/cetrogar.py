"""Extractor de Cetrogar.

Pendiente (DOR HU 1.3): inspeccionar DOM con
`scrapy shell "<url de producto de Cetrogar>"` y guardar fixtures reales.
Campos a extraer: source, external_id, product_name, price, precio_tachado,
en_oferta, raw_presentation, brand, category.
"""

from src.collectors.extractors import ExtractionError


def parse_product(response, producto_id: int, external_id: str | None = None) -> dict:
    raise ExtractionError("selectores_pendientes: falta inspeccionar DOM de Cetrogar")
