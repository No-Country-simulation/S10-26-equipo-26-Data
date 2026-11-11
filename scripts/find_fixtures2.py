import json
import re
from pathlib import Path

import httpx

H = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}
c = httpx.Client(timeout=45, follow_redirects=True, headers=H)
STATE_RE = re.compile(
    r'<template data-type="json" data-varname="__STATE__">\s*<script>(.*?)</script>',
    re.S,
)

idx = c.get("https://www.carrefour.com.ar/sitemap.xml").text
prods = [s for s in re.findall(r"<loc>([^<]+)</loc>", idx) if "/sitemap/product" in s]
candidatas: list[str] = []
for s in prods:
    xml = c.get(s).text
    candidatas.extend(re.findall(r"<loc>([^<]+)</loc>", xml))
    if len(candidatas) >= 1200:
        break
print("candidatas:", len(candidatas))

out = Path("fixtures/carrefour")
out.mkdir(parents=True, exist_ok=True)

encontrados = {"promo": None, "no_promo": None, "no_price": None}

for i, url in enumerate(candidatas):
    if all(encontrados.values()):
        break
    try:
        r = c.get(url)
        if r.status_code != 200:
            continue
        m = STATE_RE.search(r.text)
        if not m:
            if encontrados["no_price"] is None:
                encontrados["no_price"] = (url, r.text)
                print("SIN STATE:", url)
            continue
        state = json.loads(m.group(1))
        prod_keys = [k for k in state if k.startswith("Product:") and "." not in k[8:]]
        offers = [state[k] for k in state if k.endswith(".commertialOffer")]
        if not prod_keys or not offers:
            if encontrados["no_price"] is None:
                encontrados["no_price"] = (url, r.text)
                print("SIN PRODUCT/OFFER:", url)
            continue

        offer = offers[0]
        price = offer.get("Price")
        list_price = offer.get("ListPrice")
        teasers = offer.get("teasers") or []
        dh = offer.get("discountHighlights") or []

        if not isinstance(price, int):
            if encontrados["no_price"] is None:
                encontrados["no_price"] = (url, r.text)
                print("SIN PRICE:", url, price)
            continue

        if list_price > price and encontrados["promo"] is None:
            encontrados["promo"] = (url, r.text)
            print("PROMO:", url, price, list_price)

        if (
            list_price == price
            and not teasers
            and not dh
            and encontrados["no_promo"] is None
        ):
            encontrados["no_promo"] = (url, r.text)
            print("NO PROMO:", url, price)

        if i % 25 == 0:
            print("  ...", i, "teasers", len(teasers), price, list_price)
    except Exception as exc:
        print("  err", type(exc).__name__, str(exc)[:60])

for name, data in encontrados.items():
    if data:
        (out / f"{name}.html").write_text(data[1], encoding="utf-8")
        print("guardada", name, "->", data[0])
    else:
        print("FALTA", name)
