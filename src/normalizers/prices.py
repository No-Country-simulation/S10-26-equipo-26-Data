import re
from decimal import Decimal, InvalidOperation


def parse_price(raw: str | Decimal | int | float) -> Decimal:
    """Convierte precios AR ("$12.990,00", "1.234.567,89", "1299.99") a Decimal.

    Lanza ValueError con valores no interpretables o no positivos (nunca inventa).
    """
    if isinstance(raw, Decimal):
        value = raw
    else:
        text = re.sub(r"[^\d.,+-]", "", str(raw)).strip()
        if not text or text in {"-", "+", "+"}:
            raise ValueError(f"precio_vacio raw={raw!r}")
        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        elif "," in text:
            parte_decimal = text.split(",")[1]
            text = (
                text.replace(",", ".")
                if len(parte_decimal) <= 2
                else text.replace(",", "")
            )
        elif "." in text and len(text.split(".")[1]) == 3:
            text = text.replace(".", "")
        try:
            value = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"precio_no_interpretable raw={raw!r}") from exc
    if value <= 0:
        raise ValueError(f"precio_no_positivo raw={raw!r}")
    return value
