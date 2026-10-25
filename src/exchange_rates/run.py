"""Job de ingesta FX horaria (HU 3.1).

    python -m src.exchange_rates.run [--dry-run]

En producción lo corre el cron de Railway (`0 * * * *`); debe salir con código 0
y cerrar conexiones (requisito de los cron jobs de la plataforma).
"""

import argparse
import logging
import sys

from src.config.settings import get_settings
from src.exchange_rates.client import FXClientError, fetch_rates
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="exchange_rates")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="consulta y valida sin persistir en historial_divisas",
    )
    args = parser.parse_args(argv)
    setup_logging()
    settings = get_settings()

    try:
        observation = fetch_rates(
            settings.exchange_rate_api_url,
            api_key=settings.exchange_rate_api_key,
        )
    except FXClientError as exc:
        logger.error("fx_error %s", exc)
        return 1

    if args.dry_run:
        print(observation.model_dump_json(indent=2))
        return 0

    from src.persistence import build_writer

    writer = build_writer()
    if writer is None:
        logger.error("fx_writer_no_configurado (INGEST_MODE / DATABASE_URL / API_URL)")
        return 2
    writer.upsert(observation)
    writer.close()
    logger.info("fx_upsert timestamp=%s", observation.timestamp.isoformat())
    return 0


if __name__ == "__main__":
    sys.exit(main())
