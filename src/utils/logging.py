import logging

from src.config.settings import get_settings


def setup_logging(level: str | None = None) -> None:
    logging.basicConfig(
        level=level or get_settings().log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def log_run_summary(
    store: str,
    consultadas: int,
    extraidas: int,
    errores: int,
    duracion_s: float,
) -> None:
    """Métricas por corrida (README Data §9): detectan fallas de la fuente a tiempo."""
    logging.getLogger(__name__).info(
        "run_summary store=%s consultadas=%d extraidas=%d errores=%d duracion_s=%.1f",
        store,
        consultadas,
        extraidas,
        errores,
        duracion_s,
    )
