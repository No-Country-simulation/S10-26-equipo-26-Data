import json
from datetime import datetime, timezone
from pathlib import Path


def append_dump(store: str, payload: dict, base_dir: Path | None = None) -> Path:
    """Dump JSONL crudo por corrida en runs/{store}/YYYYMMDD.jsonl (trazabilidad).

    Conserva los campos identitarios (external_id, source_url, nombre crudo,
    presentación, fetched_at) que aún no tienen columna en la BD (decisión #8).
    """
    directory = (base_dir or Path("runs")) / store
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{datetime.now(timezone.utc):%Y%m%d}.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    return path
