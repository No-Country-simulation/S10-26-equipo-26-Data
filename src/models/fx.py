from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExchangeRateObservation(BaseModel):
    """Fila de historial_divisas: oficial + paralelo en la misma fila (HU 3.1)."""

    timestamp: datetime  # efectivo de la fuente; PK en la BD (Railway)
    tipo_cambio_oficial: Decimal = Field(gt=0)
    tipo_cambio_paralelo: Decimal = Field(gt=0)
