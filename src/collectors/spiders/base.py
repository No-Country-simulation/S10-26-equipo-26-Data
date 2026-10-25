import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import scrapy

from src.collectors.extractors import ExtractionError
from src.utils.logging import log_run_summary

TARGETS_DIR = Path(__file__).resolve().parents[3] / "targets"


def load_targets(store: str) -> list[dict]:
    """Lee targets/{store}.csv — solo filas activas (curado humano, decisión #8)."""
    path = TARGETS_DIR / f"{store}.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        row
        for row in rows
        if str(row.get("activo", "")).strip().lower() == "true"
    ]


class BaseStoreSpider(scrapy.Spider):
    """Solo orquestación: targets → requests → extractor puro (ver extractors/)."""

    store: str = ""
    extractor = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inicio = time.monotonic()
        self._consultadas = 0
        self._extraidas = 0
        self._errores = 0

    def start_requests(self):
        for row in load_targets(self.store):
            url = (row.get("url") or "").strip()
            if not url.startswith(("http://", "https://")):
                self.logger.error("target_url_invalida row=%s", row)
                continue
            try:
                producto_id = int(row["producto_id"])
            except (KeyError, ValueError):
                self.logger.error("target_producto_id_invalido row=%s", row)
                continue
            external_id = (row.get("external_id") or "").strip() or None
            yield scrapy.Request(
                url,
                cb_kwargs={"producto_id": producto_id, "external_id": external_id},
            )

    def parse(self, response, producto_id, external_id=None):
        self._consultadas += 1
        try:
            data = self.extractor.parse_product(
                response, producto_id=producto_id, external_id=external_id
            )
        except ExtractionError as exc:
            self._errores += 1
            self.logger.error("extract_failed url=%s err=%s", response.url, exc)
            return

        fetched_at = datetime.now(timezone.utc)
        data.setdefault("store", self.store)
        data.setdefault("source_url", response.url)
        data.setdefault("observed_at", fetched_at)
        data.setdefault("fetched_at", fetched_at)
        self._extraidas += 1
        yield data

    def closed(self, reason):
        log_run_summary(
            store=self.store,
            consultadas=self._consultadas,
            extraidas=self._extraidas,
            errores=self._errores,
            duracion_s=time.monotonic() - self._inicio,
        )
