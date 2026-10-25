"""Cotización as-of y conversión a USD (decisión #3: los calcula el pipeline Data).

Regla "más cercana anterior" (misma que HU 3.2 del Backend); si no hay dato previo,
se usa el más antiguo disponible; si la tabla está vacía → FXUnavailableError.
"""

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from src.config.settings import get_settings


class FXUnavailableError(Exception):
    """No hay cotización utilizable para el timestamp pedido."""


class RateProvider(Protocol):
    def latest_at_or_before(self, ts: datetime) -> tuple[Decimal, Decimal] | None: ...


class MemoryRateProvider:
    """Filas (timestamp, oficial, paralelo) ordenadas; para tests y corridas sin BD."""

    def __init__(self, rows: list[tuple[datetime, Decimal, Decimal]] | None = None):
        self._rows = sorted(rows or [], key=lambda row: row[0])

    def latest_at_or_before(self, ts: datetime) -> tuple[Decimal, Decimal] | None:
        previa: tuple[Decimal, Decimal] | None = None
        for timestamp, oficial, paralelo in self._rows:
            if timestamp <= ts:
                previa = (oficial, paralelo)
            else:
                break
        if previa is not None:
            return previa
        if self._rows:
            _, oficial, paralelo = self._rows[0]
            return (oficial, paralelo)
        return None


def get_rate_as_of(
    ts: datetime,
    provider: RateProvider,
    tipo: str = "oficial",
) -> Decimal:
    row = provider.latest_at_or_before(ts)
    if row is None:
        raise FXUnavailableError(f"sin_cotizacion ts={ts.isoformat()}")
    oficial, paralelo = row
    if tipo not in ("oficial", "paralelo"):
        raise ValueError(f"tipo_desconocido tipo={tipo!r}")
    return oficial if tipo == "oficial" else paralelo


def to_usd(precio_local: Decimal, fx: Decimal) -> Decimal:
    """ARS/USD → división; redondeo a 2 decimales (columna precio_usd)."""
    if fx <= 0:
        raise ValueError("fx debe ser > 0")
    return (precio_local / fx).quantize(Decimal("0.01"))


def build_rate_provider() -> RateProvider:
    settings = get_settings()
    if settings.ingest_mode == "postgres" and settings.database_url:
        from src.persistence.postgres import PostgresRateProvider

        return PostgresRateProvider(settings.database_url)
    return MemoryRateProvider()
