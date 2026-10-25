import os

BOT_NAME = "pricescope-data"

SPIDER_MODULES = ["src.collectors.spiders"]
NEWSPIDER_MODULE = "src.collectors.spiders"

# Reglas de scraping (DOR HU 1.3): robots.txt verificado para Coto/Carrefour/Cetrogar
# (Carrefour: evitar /busca/*, usar sitemap/categorías)
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = float(os.environ.get("DOWNLOAD_DELAY", "1.5"))
CONCURRENT_REQUESTS = 8
AUTOTHROTTLE_ENABLED = True
RETRY_TIMES = int(os.environ.get("COLLECTION_MAX_RETRIES", "2"))
USER_AGENT = "PriceScopeBot/0.1 (NoCountry PriceScope; respetuoso con robots.txt)"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
FEED_EXPORT_ENCODING = "utf-8"

# DOD HU 1.3: log de errores + reintentos simples (2 intentos)
RETRY_HTTP_CODES = [408, 429, 500, 502, 503, 504]

ITEM_PIPELINES = {
    "src.collectors.pipelines.ValidationPipeline": 100,
    "src.collectors.pipelines.NormalizationPipeline": 200,
    "src.collectors.pipelines.FXPipeline": 300,
    "src.collectors.pipelines.PersistencePipeline": 400,
}

DOWNLOADER_MIDDLEWARES = {
    "src.collectors.middlewares.UserAgentMiddleware": 400,
}

# --dry-run en CLI: valida y buidea pero no escribe en la BD
DRY_RUN = False
