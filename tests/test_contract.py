import pytest
from pydantic import ValidationError

from src.collectors import fake
from src.models.observation import PriceObservation


def test_observacion_fake_es_valida():
    obs = PriceObservation.model_validate(fake.build_observation())
    assert obs.price > 0
    assert obs.precio_tachado is not None and obs.precio_tachado > obs.price
    assert obs.currency_code == "ARS"


def test_rechaza_precio_no_positivo():
    data = fake.build_observation()
    data["price"] = 0
    with pytest.raises(ValidationError):
        PriceObservation.model_validate(data)


def test_rechaza_tachado_igual_al_precio():
    data = fake.build_observation()
    data["precio_tachado"] = data["price"]
    with pytest.raises(ValidationError):
        PriceObservation.model_validate(data)


def test_rechaza_tachado_menor_al_precio():
    data = fake.build_observation()
    data["precio_tachado"] = data["price"] - 1
    with pytest.raises(ValidationError):
        PriceObservation.model_validate(data)


def test_rechaza_fetched_anterior_a_observed():
    data = fake.build_observation()
    data["fetched_at"] = data["observed_at"].replace(year=data["observed_at"].year - 1)
    with pytest.raises(ValidationError):
        PriceObservation.model_validate(data)


def test_rechaza_moneda_distinta_de_ars():
    data = fake.build_observation()
    data["currency_code"] = "USD"
    with pytest.raises(ValidationError):
        PriceObservation.model_validate(data)


def test_rechaza_store_desconocido():
    data = fake.build_observation()
    data["store"] = "otra-tienda"
    with pytest.raises(ValidationError):
        PriceObservation.model_validate(data)
