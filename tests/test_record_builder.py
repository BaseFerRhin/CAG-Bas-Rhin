"""Tests for record builder module."""

from __future__ import annotations

from src.extraction.notice_parser import SubNotice
from src.extraction.record_builder import RecordBuilder, SiteRecord


def _make_sub(text: str, code: str = "001", commune_id: str = "002") -> SubNotice:
    return SubNotice(
        commune_id=commune_id, commune_name="Achenheim",
        entry_number=1, sous_notice_code=code,
        lieu_dit="Todtenallee", text=text,
        page_number=155, bibliographie=["Forrer, 1923a"],
        figures_refs=["Fig. 28"],
    )


def test_build_record_basic():
    builder = RecordBuilder()
    sub = _make_sub("Un tumulus du Hallstatt D1 avec fibule en bronze.")
    rec = builder.build(sub, is_fer=True, all_periods=["Hallstatt", "Ha D1"])
    assert isinstance(rec, SiteRecord)
    assert rec.notice_id == "CAG67-002-001"
    assert rec.has_iron_age is True
    assert rec.commune_name == "Achenheim"


def test_guess_type_tumulus_vs_necropole():
    builder = RecordBuilder()
    sub_tumulus = _make_sub("Un tumulus isolé dans la forêt.")
    rec = builder.build(sub_tumulus, is_fer=True, all_periods=["Hallstatt"])
    assert rec.type_site == "tumulus"

    sub_necro = _make_sub("Vaste nécropole avec tombes multiples.")
    rec2 = builder.build(sub_necro, is_fer=True, all_periods=["Hallstatt"])
    assert rec2.type_site == "nécropole"


def test_guess_type_sanctuaire():
    builder = RecordBuilder()
    sub = _make_sub("Sanctuaire au sommet de la colline.")
    rec = builder.build(sub, is_fer=True, all_periods=["La Tène"])
    assert rec.type_site == "sanctuaire"


def test_guess_type_oppidum():
    builder = RecordBuilder()
    sub = _make_sub("Oppidum fortifié avec Ringwall.")
    rec = builder.build(sub, is_fer=True, all_periods=["La Tène"])
    assert rec.type_site == "oppidum"


def test_guess_type_habitat():
    builder = RecordBuilder()
    sub = _make_sub("Fosses et silos d'un habitat ouvert.")
    rec = builder.build(sub, is_fer=True, all_periods=["Hallstatt"])
    assert rec.type_site == "habitat"


def test_guess_type_indetermine():
    builder = RecordBuilder()
    sub = _make_sub("Découverte isolée sans contexte précis.")
    rec = builder.build(sub, is_fer=True, all_periods=["Hallstatt"])
    assert rec.type_site == "indéterminé"


def test_raw_text_truncation():
    builder = RecordBuilder()
    long_text = "x" * 1000
    sub = _make_sub(long_text)
    rec = builder.build(sub, is_fer=False, all_periods=[])
    assert len(rec.raw_text) == 500
    assert len(rec.full_text) == 1000


def test_confidence_high():
    builder = RecordBuilder()
    sub = _make_sub(
        "Fouille de sauvetage en 2005. Importante nécropole.",
        code="001", commune_id="002",
    )
    sub.bibliographie = ["Auteur, 2005", "Autre, 1995", "Encore, 2010"]
    rec = builder.build(sub, is_fer=True, all_periods=["Hallstatt"])
    assert rec.confidence_level == "HIGH"


def test_confidence_low():
    builder = RecordBuilder()
    sub = _make_sub("Mention ancienne sans précision.")
    sub.bibliographie = ["Forrer, 1912"]
    sub.figures_refs = []
    rec = builder.build(sub, is_fer=True, all_periods=["Hallstatt"])
    assert rec.confidence_level == "LOW"


def test_confidence_medium():
    builder = RecordBuilder()
    sub = _make_sub("Découverte lors de travaux. Fig. 45 montre le mobilier.")
    sub.bibliographie = ["Schaeffer, 1990"]
    rec = builder.build(sub, is_fer=True, all_periods=["Hallstatt"])
    assert rec.confidence_level == "MEDIUM"
