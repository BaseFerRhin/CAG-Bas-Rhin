"""Tests for notice parser module."""

from __future__ import annotations

from src.extraction.commune_splitter import CommuneNotice
from src.extraction.notice_parser import NoticeParser


def _make_notice(text: str, commune_id: str = "001", name: str = "TEST") -> CommuneNotice:
    return CommuneNotice(commune_id=commune_id, commune_name=name, text=text, page_start=155, page_end=155)


def test_parse_numbered_sub_notices():
    text = "Intro text.\n1* (001) Au lieu-dit AAA, un habitat.\n2* (002) Au lieu-dit BBB, une nécropole."
    parser = NoticeParser()
    subs = parser.parse(_make_notice(text))
    numbered = [s for s in subs if s.entry_number is not None]
    assert len(numbered) == 2
    assert numbered[0].sous_notice_code == "001"
    assert numbered[1].sous_notice_code == "002"


def test_parse_lieu_dit_code():
    text = "Intro.\n1* (003 AH) Au lieu-dit Todtenallee, un tumulus."
    parser = NoticeParser()
    subs = parser.parse(_make_notice(text))
    numbered = [s for s in subs if s.sous_notice_code]
    assert len(numbered) >= 1
    assert "003 AH" in numbered[0].sous_notice_code


def test_parse_no_sub_notices():
    text = "Simple commune without numbered entries. Céramique médiévale."
    parser = NoticeParser()
    subs = parser.parse(_make_notice(text))
    assert len(subs) == 1
    assert subs[0].sous_notice_code is None


def test_extract_lieu_dit():
    text = "1* (001) Au lieu-dit Oberschaeffolsheim, fouille de 1990."
    parser = NoticeParser()
    subs = parser.parse(_make_notice(f"Intro.\n{text}"))
    named_subs = [s for s in subs if s.lieu_dit]
    assert len(named_subs) >= 1
    assert "Oberschaeffolsheim" in named_subs[0].lieu_dit


def test_extract_bibliography():
    text = "Intro.\n1* (001) Site. Forrer, 1923a, p. 106. Normand, 1973."
    parser = NoticeParser()
    subs = parser.parse(_make_notice(text))
    numbered = [s for s in subs if s.entry_number]
    assert len(numbered) >= 1
    assert any("Forrer" in b for b in numbered[0].bibliographie)


def test_extract_figure_refs():
    text = "Intro.\n1* (001) Site décrit. Fig. 28 et Fig. 30b."
    parser = NoticeParser()
    subs = parser.parse(_make_notice(text))
    numbered = [s for s in subs if s.entry_number]
    assert len(numbered) >= 1
    assert "Fig. 28" in numbered[0].figures_refs
    assert "Fig. 30b" in numbered[0].figures_refs
