"""Tests for PDF reader module."""

from __future__ import annotations

import json
from pathlib import Path

from src.extraction.pdf_reader import PageText, PDFReader


FIXTURES = Path(__file__).parent / "fixtures" / "sample_pages.json"


def _load_fixture_pages() -> list[dict]:
    return json.loads(FIXTURES.read_text())["pages"]


def test_page_text_dataclass():
    pt = PageText(page_num=155, text="hello", commune_header="001")
    assert pt.page_num == 155
    assert pt.commune_header == "001"
    assert pt.tables == []


def test_detect_commune_header_single():
    reader = PDFReader.__new__(PDFReader)
    assert reader._detect_commune_header("Commune 002\nsome text") == "002"


def test_detect_commune_header_multi():
    reader = PDFReader.__new__(PDFReader)
    assert reader._detect_commune_header("Communes 045 à 048\nsome text") == "045-048"


def test_detect_commune_header_none():
    reader = PDFReader.__new__(PDFReader)
    assert reader._detect_commune_header("No header here") is None


def test_fixture_pages_exist():
    pages = _load_fixture_pages()
    assert len(pages) == 10
    assert pages[0]["page_num"] == 155
    assert pages[-1]["page_num"] == 660


def test_fixture_page_has_commune_header():
    pages = _load_fixture_pages()
    for p in pages:
        assert "commune_header" in p
        assert p["commune_header"] is not None
