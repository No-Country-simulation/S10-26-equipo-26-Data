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
c = httpx.Client(timeout=60, follow_redirects=True, headers=H)

idx = c.get("https://www.carrefour.com.ar/sitemap.xml").text
prods = [s for s in re.findall(r"<loc>([^<]+)</loc>", idx) if "/sitemap/product" in s]

kws = ["arroz-gallo", "arroz-blanco", "playadito-500", "playadito"]
hits = {k: [] for k in kws}
for s in prods:
    if all(hits[k] for k in ("arroz-gallo", "playadito")):
        break
    xml = c.get(s).text
    for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
        low = loc.lower()
        for k in kws:
            if k in low and len(hits[k]) < 4:
                hits[k].append(loc)

for k, v in hits.items():
    print("##", k)
    for u in v:
        print("  ", u)

# --- trim de fixtures: conservar solo el template __STATE__ ---
STATE_RE = re.compile(
    r'(<template data-type="json" data-varname="__STATE__">.*?</template>)',
    re.S,
)
fixtures = Path("fixtures/carrefour")
for f in sorted(fixtures.glob("*.html")):
    text = f.read_text(encoding="utf-8")
    m = STATE_RE.search(text)
    if not m:
        print("trim: sin state", f.name, "se conserva tal cual")
        continue
    trimmed = (
        "<!DOCTYPE html><html><head><title>fixture</title></head><body>"
        + m.group(1)
        + "</body></html>"
    )
    before = f.stat().st_size
    f.write_text(trimmed, encoding="utf-8")
    print(f"trim {f.name}: {before} -> {len(trimmed.encode('utf-8'))}")
