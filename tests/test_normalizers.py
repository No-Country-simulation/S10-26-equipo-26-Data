from decimal import Decimal

import pytest

from src.normalizers.presentation import parse_presentation
from src.normalizers.prices import parse_price
from src.normalizers.strings import normalize, similarity, tokens


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("$12.990,00", Decimal("12990.00")),
        ("1299,99", Decimal("1299.99")),
        ("$ 1.234.567,89", Decimal("1234567.89")),
        ("1299.99", Decimal("1299.99")),
        ("12.990", Decimal("12990")),
        ("ARS 1500", Decimal("1500")),
        (Decimal("50.5"), Decimal("50.5")),
    ],
)
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


@pytest.mark.parametrize("raw", ["", "gratis", "-5", "0", "N/D"])
def test_parse_price_rechaza(raw):
    with pytest.raises(ValueError):
        parse_price(raw)


def test_normalize_quita_tildes_y_puntuacion():
    assert normalize("Coca-Cola 500 ML") == "coca cola 500 ml"
    assert normalize("  Café  Instantáneo  ") == "cafe instantaneo"


def test_tokens():
    assert tokens("Arroz Lucchetti 1 kg") == ["arroz", "lucchetti", "1", "kg"]


def test_similarity_alta_para_el_mismo_producto():
    score = similarity("Coca Cola 500ml", "COCA-COLA 500 ml")
    assert score >= 0.90


def test_similarity_baja_para_productos_distintos():
    score = similarity("Coca Cola 500ml", "Agua Villavicencio 2 l")
    assert score < 0.75


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("500 g", (Decimal("500"), "g")),
        ("1 kg", (Decimal("1"), "kg")),
        ("Pack x 2 unidades", (Decimal("2"), "un")),
        ("sin presentacion", (None, None)),
        (None, (None, None)),
    ],
)
def test_parse_presentation(raw, expected):
    assert parse_presentation(raw) == expected
