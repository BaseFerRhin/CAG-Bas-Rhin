"""Tests for commune splitter module."""

from __future__ import annotations

import json
from pathlib import Path

from src.extraction.pdf_reader import PageText
from src.extraction.commune_splitter import CommuneSplitter


FIXTURES = Path(__file__).parent / "fixtures" / "sample_pages.json"


def _load_pages_as_page_texts() -> list[PageText]:
    data = json.loads(FIXTURES.read_text())["pages"]
    return [PageText(page_num=p["page_num"], text=p["text"], commune_header=p["commune_header"]) for p in data]


def test_split_finds_communes():
    pages = _load_pages_as_page_texts()
    splitter = CommuneSplitter()
    communes = splitter.split(pages)
    assert len(communes) >= 8


def test_commune_ids_are_three_digits():
    pages = _load_pages_as_page_texts()
    splitter = CommuneSplitter()
    communes = splitter.split(pages)
    for c in communes:
        assert len(c.commune_id) == 3
        assert c.commune_id.isdigit()


def test_commune_names_are_stripped():
    pages = _load_pages_as_page_texts()
    splitter = CommuneSplitter()
    communes = splitter.split(pages)
    for c in communes:
        assert c.commune_name == c.commune_name.strip()
        assert len(c.commune_name) > 0


def test_commune_has_page_range():
    pages = _load_pages_as_page_texts()
    splitter = CommuneSplitter()
    communes = splitter.split(pages)
    for c in communes:
        assert c.page_start > 0
        assert c.page_end >= c.page_start


def test_single_page_commune():
    page = PageText(page_num=155, text="001 — ACHENHEIM (1 360 ha)\nUne commune.\n1* (001) Site.", commune_header="001")
    splitter = CommuneSplitter()
    communes = splitter.split([page])
    assert len(communes) == 1
    assert communes[0].commune_id == "001"
    assert communes[0].commune_name == "ACHENHEIM"


def test_multi_commune_single_page():
    text = "001 — AAA (100 ha)\nTexte A.\n002 — BBB (200 ha)\nTexte B."
    page = PageText(page_num=155, text=text, commune_header="001")
    splitter = CommuneSplitter()
    communes = splitter.split([page])
    assert len(communes) == 2
    assert communes[0].commune_id == "001"
    assert communes[1].commune_id == "002"
