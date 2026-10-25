import logging
from decimal import Decimal

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from src.fx.converter import (
    FXUnavailableError,
    build_rate_provider,
    get_rate_as_of,
    to_usd,
)
from src.models.observation import PriceObservation

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """[100] Valida el contrato Pydantic; lo inválido se descarta con log (jamás se corrige)."""

    def process_item(self, item, spider):
        if isinstance(item, PriceObservation):
            return item
        data = dict(item) if isinstance(item, dict) else ItemAdapter(item).asdict()
        try:
            return PriceObservation.model_validate(data)
        except Exception as exc:
            raise DropItem(f"observacion_invalida: {exc}") from exc


class NormalizationPipeline:
    """[200] Normalización final: decimales consistentes y strings limpios."""

    def process_item(self, item, spider):
        updates: dict = {"price": item.price.quantize(Decimal("0.01"))}
        if item.precio_tachado is not None:
            updates["precio_tachado"] = item.precio_tachado.quantize(Decimal("0.01"))
        if item.product_name != item.product_name.strip():
            updates["product_name"] = item.product_name.strip()
        return item.model_copy(update=updates)


class FXPipeline:
    """[300] Asigna tipo_cambio_usado + precio_usd (decisión #3: los calcula Data).

    Sin cotización as-of utilizable → DropItem (precio_usd es NOT NULL en la BD).
    """

    def open_spider(self, spider):
        from src.config.settings import get_settings

        self.provider = build_rate_provider()
        self.tipo = get_settings().fx_rate_type

    def process_item(self, item, spider):
        if item.fx_rate is not None and item.price_usd is not None:
            return item
        try:
            rate = get_rate_as_of(item.observed_at, self.provider, tipo=self.tipo)
        except FXUnavailableError as exc:
            raise DropItem(f"fx_no_disponible: {exc}") from exc
        return item.model_copy(
            update={"fx_rate": rate, "price_usd": to_usd(item.price, rate)}
        )


class PersistencePipeline:
    """[400] Dump crudo JSONL (siempre) + escritura según INGEST_MODE (decisión #1)."""

    def open_spider(self, spider):
        from src.persistence import build_writer

        self.dry_run = spider.settings.getbool("DRY_RUN")
        self.writer = None if self.dry_run else build_writer()

    def process_item(self, item, spider):
        from src.utils.dumps import append_dump

        append_dump(getattr(spider, "store", item.store), item.model_dump(mode="json"))
        if self.writer is None:
            logger.warning(
                "ingest_omitido store=%s dry_run=%s (writer no configurado)",
                item.store,
                self.dry_run,
            )
            return item
        self.writer.write(item)
        return item

    def close_spider(self, spider):
        if self.writer is not None:
            self.writer.close()
