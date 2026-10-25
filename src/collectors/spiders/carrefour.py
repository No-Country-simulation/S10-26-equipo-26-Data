from src.collectors.extractors import carrefour
from src.collectors.spiders.base import BaseStoreSpider


class CarrefourSpider(BaseStoreSpider):
    name = "carrefour"
    store = "carrefour"
    extractor = carrefour
