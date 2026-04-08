"""Tests for Iron Age filter module."""

from __future__ import annotations

from src.extraction.iron_age_filter import IronAgeFilter


def test_hallstatt_detected():
    f = IronAgeFilter()
    assert f.is_iron_age("époque de Hallstatt") is True
    assert f.is_iron_age("période hallstattienne") is True


def test_la_tene_detected():
    f = IronAgeFilter()
    assert f.is_iron_age("La Tène finale") is True
    assert f.is_iron_age("LT D1") is True


def test_ha_all_sub_periods():
    f = IronAgeFilter()
    for sub in ["Ha A", "Ha B", "Ha C", "Ha D1", "Ha D2", "Ha D3"]:
        assert f.is_iron_age(f"mobilier {sub}") is True, f"Failed for {sub}"


def test_lt_all_sub_periods():
    f = IronAgeFilter()
    for sub in ["LT A", "LT B", "LT C", "LT D"]:
        assert f.is_iron_age(f"mobilier {sub}") is True, f"Failed for {sub}"


def test_german_terms():
    f = IronAgeFilter()
    assert f.is_iron_age("Grabhügel im Wald") is True
    assert f.is_iron_age("Ringwall der Eisenzeit") is True
    assert f.is_iron_age("Viereckschanze bei Kirchberg") is True
    assert f.is_iron_age("Fürstengrab am Maimont") is True


def test_bronze_final_detected():
    f = IronAgeFilter()
    assert f.is_iron_age("âge du bronze final") is True
    assert f.is_iron_age("BF IIIa") is True
    assert f.is_iron_age("BF III") is True


def test_gallo_romain_excluded():
    f = IronAgeFilter()
    assert f.is_iron_age("villa gallo-romaine du IIe siècle") is False


def test_medieval_excluded():
    f = IronAgeFilter()
    assert f.is_iron_age("céramique médiévale uniquement") is False


def test_mixed_periods():
    f = IronAgeFilter()
    text = "Hallstatt et gallo-romain"
    assert f.is_iron_age(text) is True
    periods = f.extract_all_periods(text)
    assert len(periods) >= 2


def test_normalize_period():
    f = IronAgeFilter()
    assert f.normalize_period("Ha D1") == "Ha D1"
    assert f.normalize_period("Hallstatt") == "Hallstatt"
    assert f.normalize_period("la tène") == "La Tène"
    assert f.normalize_period("gallo-romain") == "Gallo-romain"
    assert f.normalize_period("LT A") == "LT A"
    assert f.normalize_period("BF IIIa") == "BF III"
    assert f.normalize_period("néolithique") == "Néolithique"
    assert f.normalize_period("eisenzeit") == "Hallstatt"  # maps to Hallstatt umbrella


def test_is_fer_norm():
    f = IronAgeFilter()
    assert f.is_fer_norm("Ha D1") is True
    assert f.is_fer_norm("La Tène") is True
    assert f.is_fer_norm("Gallo-romain") is False
    assert f.is_fer_norm("Néolithique") is False
