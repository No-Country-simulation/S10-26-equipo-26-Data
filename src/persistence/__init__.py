import logging
from typing import Protocol

from src.config.settings import get_settings
from src.models.fx import ExchangeRateObservation
from src.models.observation import PriceObservation

logger = logging.getLogger(__name__)


class ObservationWriter(Protocol):
    def write(self, obs: PriceObservation) -> None: ...


class FxWriter(Protocol):
    def upsert(self, rate: ExchangeRateObservation) -> None: ...


class Writer(ObservationWriter, FxWriter, Protocol):
    def close(self) -> None: ...


def build_writer() -> Writer | None:
    """Según INGEST_MODE (decisión #1, pendiente — recomendada B).

    Sin configurar → None: el PersistencePipeline solo buidea con warning.
    """
    settings = get_settings()
    if settings.ingest_mode == "postgres":
        if not settings.database_url:
            logger.warning("ingest_postgres_sin_DATABASE_URL")
            return None
        from src.persistence.postgres import PostgresWriter

        return PostgresWriter(settings.database_url)
    if settings.ingest_mode == "api":
        if not settings.api_url:
            logger.warning("ingest_api_sin_API_URL")
            return None
        from src.persistence.api import ApiWriter

        return ApiWriter(settings.api_url, settings.api_key)
    logger.warning("ingest_mode_desconocido mode=%s", settings.ingest_mode)
    return None
