"""Opción A: escritura directa en PostgreSQL (Railway Postgres vía túnel local 55432).

Solo DML aquí; las migraciones (DDL) viven en el Backend y se aplican por Alembic.
Sin constraint único en precios_historicos → deduplicación por regla (misma ventana
de corrida).
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import psycopg

from src.config.stores import STORES
from src.models.fx import ExchangeRateObservation
from src.models.observation import PriceObservation

logger = logging.getLogger(__name__)

DEDUP_VENTANA_MIN = 10

_INSERT_OBSERVACION = """
INSERT INTO precios_historicos
    (timestamp, producto_id, tienda_id, precio_local, precio_tachado, en_oferta,
     tipo_cambio_usado, precio_usd)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

_DEDUP_OBSERVACION = """
SELECT 1 FROM precios_historicos
WHERE producto_id = %s AND tienda_id = %s AND timestamp >= %s
LIMIT 1
"""

_UPSERT_FX = """
INSERT INTO historial_divisas (timestamp, tipo_cambio_oficial, tipo_cambio_paralelo)
VALUES (%s, %s, %s)
ON CONFLICT (timestamp) DO UPDATE
SET tipo_cambio_oficial = EXCLUDED.tipo_cambio_oficial,
    tipo_cambio_paralelo = EXCLUDED.tipo_cambio_paralelo
"""

_RATE_PREVIA = """
SELECT tipo_cambio_oficial, tipo_cambio_paralelo FROM historial_divisas
WHERE timestamp <= %s ORDER BY timestamp DESC LIMIT 1
"""

_RATE_MAS_ANTIGUA = """
SELECT tipo_cambio_oficial, tipo_cambio_paralelo FROM historial_divisas
ORDER BY timestamp ASC LIMIT 1
"""


def _dsn(dsn: str) -> str:
    """Acepta el formato del equipo (`postgresql+psycopg://…`) para psycopg3."""
    return dsn.replace("postgresql+psycopg://", "postgresql://", 1)


class PostgresWriter:
    def __init__(self, dsn: str, dedup_ventana_min: int = DEDUP_VENTANA_MIN):
        self._conn = psycopg.connect(_dsn(dsn), autocommit=True)
        self._desde = datetime.now(timezone.utc) - timedelta(minutes=dedup_ventana_min)
        self._tiendas: dict[str, int] = {}

    def _tienda_id(self, store_key: str) -> int:
        if store_key not in self._tiendas:
            nombre = STORES[store_key].nombre
            with self._conn.cursor() as cur:
                cur.execute("SELECT id FROM tiendas WHERE nombre = %s", (nombre,))
                row = cur.fetchone()
            if row is None:
                raise KeyError(f"tienda_no_encontrada nombre={nombre}")
            self._tiendas[store_key] = row[0]
        return self._tiendas[store_key]

    def write(self, obs: PriceObservation) -> None:
        tienda_id = self._tienda_id(obs.store)
        with self._conn.cursor() as cur:
            cur.execute(_DEDUP_OBSERVACION, (obs.producto_id, tienda_id, self._desde))
            if cur.fetchone() is not None:
                logger.info(
                    "observacion_duplicada store=%s producto_id=%s",
                    obs.store,
                    obs.producto_id,
                )
                return
            cur.execute(
                _INSERT_OBSERVACION,
                (
                    obs.observed_at,
                    obs.producto_id,
                    tienda_id,
                    obs.price,
                    obs.precio_tachado,
                    obs.en_oferta,
                    obs.fx_rate,
                    obs.price_usd,
                ),
            )

    def upsert(self, rate: ExchangeRateObservation) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                _UPSERT_FX,
                (rate.timestamp, rate.tipo_cambio_oficial, rate.tipo_cambio_paralelo),
            )

    def close(self) -> None:
        self._conn.close()


class PostgresRateProvider:
    def __init__(self, dsn: str):
        self._conn = psycopg.connect(_dsn(dsn), autocommit=True)

    def latest_at_or_before(self, ts: datetime) -> tuple[Decimal, Decimal] | None:
        with self._conn.cursor() as cur:
            cur.execute(_RATE_PREVIA, (ts,))
            row = cur.fetchone()
            if row is None:
                cur.execute(_RATE_MAS_ANTIGUA)
                row = cur.fetchone()
        return (row[0], row[1]) if row else None

    def close(self) -> None:
        self._conn.close()
