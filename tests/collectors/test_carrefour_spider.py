"""Integracion spider Carrefour: start() + parse() sin red (HU 1.3)."""

import asyncio
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from src.collectors.spiders.base import load_targets
from src.collectors.spiders.carrefour import CarrefourSpider
from src.models.observation import PriceObservation

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "carrefour"
FIXTURE_URL = "https://www.carrefour.com.ar/colita-de-cuadril-etiqueta-negra-x-kg-662871/p"


def _start_requests(spider) -> list[Request]:
    async def collect() -> list[Request]:
        return [request async for request in spider.start()]

    return asyncio.run(collect())


def test_load_targets_carrefour_activos() -> None:
    rows = load_targets("carrefour")
    assert rows
    assert all(r["activo"].lower() == "true" for r in rows)
    assert all(r["url"].startswith("https://www.carrefour.com.ar/") for r in rows)
    # decision #5: jamas /busca/*
    assert not any("/busca/" in r["url"] for r in rows)


def test_start_genera_un_request_por_target() -> None:
    spider = CarrefourSpider()
    requests = _start_requests(spider)

    assert len(requests) == len(load_targets("carrefour"))
    assert all(r.url.startswith("https://www.carrefour.com.ar/") for r in requests)
    assert all("producto_id" in r.cb_kwargs for r in requests)


def test_parse_con_fixture_genera_observacion_valida() -> None:
    body = (FIXTURES / "no_promo.html").read_text(encoding="utf-8")
    target = load_targets("carrefour")[0]
    request = Request(
        target["url"],
        cb_kwargs={"producto_id": int(target["producto_id"]), "external_id": None},
    )
    response = HtmlResponse(
        url=request.url,
        body=body.encode(),
        request=request,
    )

    spider = CarrefourSpider()
    items = list(spider.parse(response, **request.cb_kwargs))

    assert len(items) == 1
    item = items[0]
    assert item["store"] == "carrefour"
    assert item["source_url"] == target["url"]
    assert item["observed_at"] is not None
    assert item["fetched_at"] is not None

    obs = PriceObservation.model_validate(item)
    assert obs.price > 0
