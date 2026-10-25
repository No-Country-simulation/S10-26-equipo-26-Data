from src.collectors.extractors import coto
from src.collectors.spiders.base import BaseStoreSpider


class CotoSpider(BaseStoreSpider):
    name = "coto"
    store = "coto"
    extractor = coto
