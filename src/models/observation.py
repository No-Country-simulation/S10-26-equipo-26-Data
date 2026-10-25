from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

StoreName = Literal["coto", "carrefour", "cetrogar"]


class PriceObservation(BaseModel):
    """Contrato único de observación de precio (HU 0.3 / HU 2.1).

    Nombres de promo alineados al DOD de la HU 2.1 (`precio_tachado`, `en_oferta`)
    y mapeados a las columnas reales de la BD (Railway) (ver GUIA-ESTRUCTURA-DATA §2).
    """

    # ── destino directo en precios_historicos ─────────────────────────
    store: StoreName
    producto_id: int  # resuelto desde targets/
    price: Decimal = Field(gt=0)  # → precio_local (NOT NULL)
    precio_tachado: Decimal | None = None  # → precio_tachado (si existe, > price)
    en_oferta: bool = False  # → en_oferta (señal visible: badge "oferta", "2x1")
    observed_at: datetime  # → timestamp (UTC)

    # ── calculados por el pipeline (NO por el extractor) ──────────────
    fx_rate: Decimal | None = None  # → tipo_cambio_usado (as-of, NOT NULL al insertar)
    price_usd: Decimal | None = None  # → precio_usd = price / fx_rate (NOT NULL al insertar)

    # ── identidad: SOLO dump crudo hasta la decisión #8 ──────────────
    source: str
    external_id: str | None = None
    source_url: str
    product_name: str
    raw_presentation: str | None = None  # "500 g" → base de reduflación (HU 2.4)
    brand: str | None = None
    category: str | None = None
    fetched_at: datetime  # no se persiste (sin columna en la BD)
    currency_code: Literal["ARS"] = "ARS"  # validado, no persistido

    @model_validator(mode="after")
    def _check(self):
        if self.precio_tachado is not None and self.precio_tachado <= self.price:
            raise ValueError("precio_tachado debe ser mayor que price")
        if self.fetched_at < self.observed_at:
            raise ValueError("fetched_at no puede ser anterior a observed_at")
        return self
