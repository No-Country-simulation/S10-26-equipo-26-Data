import re
from decimal import Decimal, InvalidOperation

_PRESENTATION_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(ml|cc|l|lt|g|kg|gr|un|uds|unidades)\b",
    re.IGNORECASE,
)

_UNIT_ALIASES = {"lt": "l", "gr": "g", "uds": "un", "unidades": "un"}


def parse_presentation(raw: str | None) -> tuple[Decimal | None, str | None]:
    """Extrae (cantidad, unidad) de la presentación cruda — base de reduflación (HU 2.4).

    "500 g" → (Decimal("500"), "g"). Sin match → (None, None); nunca inventa.
    """
    if not raw:
        return None, None
    match = _PRESENTATION_RE.search(raw)
    if not match:
        return None, None
    value, unit = match.group(1), match.group(2).lower()
    try:
        quantity = Decimal(value.replace(",", "."))
    except InvalidOperation:
        return None, None
    return quantity, _UNIT_ALIASES.get(unit, unit)
