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
    if len(candidatas) >= 2500:
        break

hallada = None
stats = {"con_precio": 0, "precio_cero": 0, "float": 0}
for i, url in enumerate(candidatas):
    if hallada:
        break
    try:
        r = c.get(url)
        if r.status_code != 200:
            continue
        m = STATE_RE.search(r.text)
        if not m:
            continue
        state = json.loads(m.group(1))
        prod_keys = [
            k for k in state if k.startswith("Product:") and "." not in k[8:]
        ]
        if not prod_keys:
            continue
        prod = prod_keys[0]
        slug = prod[len("Product:"):]
        # oferta del MISMO producto
        offer = state.get("$" + prod + ".items.0.sellers.0.commertialOffer")
        if not isinstance(offer, dict):
            offers = [
                state[k]
                for k in state
                if k.endswith(".commertialOffer") and slug.split("-")[0] in k
            ]
            offer = offers[0] if offers else None
        if not isinstance(offer, dict):
            continue
        price = offer.get("Price")
        list_price = offer.get("ListPrice")
        teasers = offer.get("teasers") or []
        dh = offer.get("discountHighlights") or []
        if isinstance(price, float):
            stats["float"] += 1
            continue
        if not isinstance(price, int):
            continue
        if price <= 0:
            stats["precio_cero"] += 1
            continue
        stats["con_precio"] += 1
        if list_price == price and not teasers and not dh:
            hallada = (url, r.text, price)
            print("NO PROMO REAL:", url, price)
        if i % 40 == 0:
            print("  ...", i, price, list_price, "teasers", len(teasers))
    except Exception as exc:
        print("  err", type(exc).__name__, str(exc)[:50])

print("stats:", stats)
if hallada:
    Path("fixtures/carrefour/no_promo.html").write_text(
        hallada[1], encoding="utf-8"
    )
    print("guardada")
else:
    print("NO se encontro pagina limpia en", len(candidatas))
