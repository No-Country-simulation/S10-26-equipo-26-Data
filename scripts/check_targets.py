"""Valida la estructura de targets/*.csv.

    python scripts/check_targets.py

Comprueba columnas, URLs, producto_id entero positivo, valores de `activo` y
URLs duplicadas por tienda. Sale con código 1 si hay errores.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS_DIR = ROOT / "targets"
REQUIRED_COLUMNS = {"url", "external_id", "producto_id", "activo"}
ACTIVOS = {"true", "false"}


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        if columns != REQUIRED_COLUMNS:
            return [f"{path.name}: columnas {sorted(columns)} != {sorted(REQUIRED_COLUMNS)}"]
        seen_urls: set[str] = set()
        for line, row in enumerate(reader, start=2):
            url = (row.get("url") or "").strip()
            activo = (row.get("activo") or "").strip().lower()
            producto_id = (row.get("producto_id") or "").strip()
            if not url.startswith(("http://", "https://")):
                errors.append(f"{path.name}:{line} url inválida: {url!r}")
            elif url in seen_urls:
                errors.append(f"{path.name}:{line} url duplicada: {url}")
            else:
                seen_urls.add(url)
            if not producto_id.isdigit() or int(producto_id) <= 0:
                errors.append(f"{path.name}:{line} producto_id inválido: {producto_id!r}")
            if activo not in ACTIVOS:
                errors.append(f"{path.name}:{line} activo inválido: {row.get('activo')!r}")
    return errors


def main() -> int:
    files = sorted(TARGETS_DIR.glob("*.csv"))
    if not files:
        print(f"ERROR: sin archivos en {TARGETS_DIR}")
        return 1
    errors: list[str] = []
    for path in files:
        errors.extend(validate_file(path))
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"OK: {len(files)} archivo(s) de targets válidos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
