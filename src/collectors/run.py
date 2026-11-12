"""CLI del pipeline de recolección (HU 0.3).

    python -m src.collectors.run --store fake
    python -m src.collectors.run --store coto [--dry-run]
    python -m src.collectors.run --store all [--dry-run]   # coto+carrefour+cetrogar
"""

import argparse
import sys

STORES_REALES = ("coto", "carrefour", "cetrogar")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="collectors")
    parser.add_argument(
        "--store",
        required=True,
        choices=["fake", "all", *STORES_REALES],
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="no escribe en la BD; solo valida, buidea y registra metricas",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.store == "fake":
        from src.collectors import fake
        from src.models.observation import PriceObservation

        obs = PriceObservation.model_validate(fake.build_observation())
        print(obs.model_dump_json(indent=2))
        return 0

    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    settings = get_project_settings()
    if args.dry_run:
        settings.set("DRY_RUN", True, priority="cmdline")
    process = CrawlerProcess(settings)
    stores = STORES_REALES if args.store == "all" else (args.store,)
    for store in stores:
        process.crawl(store)
    process.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
