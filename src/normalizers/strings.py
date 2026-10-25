import re
import unicodedata


def normalize(text: str) -> str:
    """Minúsculas, sin acentos, sin puntuación, espacios simples (HU 1.4).

    Separa dígitos de letras ("500ml" → "500 ml") para comparar presentaciones.
    """
    lowered = unicodedata.normalize("NFKD", str(text).lower())
    without_accents = "".join(
        char for char in lowered if not unicodedata.combining(char)
    )
    without_punctuation = re.sub(r"[^\w\s]", " ", without_accents)
    separated = re.sub(
        r"(?<=\d)(?=[a-z])|(?<=[a-z])(?=\d)", " ", without_punctuation
    )
    return re.sub(r"\s+", " ", separated).strip()


def tokens(text: str) -> list[str]:
    normalized = normalize(text)
    return normalized.split() if normalized else []


def similarity(text_a: str, text_b: str) -> float:
    """Score 0..1 de similitud entre nombres crudos y canónicos (HU 1.4).

    Umbrales acordados en el plan: >= 0.90 auto-sugiere; 0.75–0.90 revisión manual.
    """
    from rapidfuzz import fuzz

    return round(fuzz.token_sort_ratio(normalize(text_a), normalize(text_b)) / 100.0, 4)
