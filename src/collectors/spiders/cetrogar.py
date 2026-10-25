from src.collectors.extractors import cetrogar
from src.collectors.spiders.base import BaseStoreSpider


class CetrogarSpider(BaseStoreSpider):
    name = "cetrogar"
    store = "cetrogar"
    extractor = cetrogar
