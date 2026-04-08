"""Tests for DuckDB storage (schema, loader, queries)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import duckdb

from src.extraction.commune_splitter import CommuneNotice
from src.extraction.record_builder import SiteRecord
from src.storage.schema import init_db
from src.storage.loader import load_records
from src.storage.queries import get_summary_stats, extraction_metrics


def _make_commune(cid: str = "001", name: str = "TestCommune") -> CommuneNotice:
    return CommuneNotice(commune_id=cid, commune_name=name, text="text", page_start=155, page_end=156)


def _make_record(cid: str = "001", code: str = "001", is_fer: bool = True) -> SiteRecord:
    return SiteRecord(
        notice_id=f"CAG67-{cid}-{code}",
        commune_id=cid, commune_name="TestCommune",
        sous_notice_code=code, lieu_dit="TestLieu",
        type_site="tumulus",
        periode_mentions=["Hallstatt"], vestiges_mentions=["tumulus"],
        raw_text="Tumulus du Hallstatt.", full_text="Tumulus du Hallstatt D1.",
        page_number=155, bibliographie=["Forrer, 1923a"],
        figures_refs=["Fig. 28"], has_iron_age=is_fer,
        all_periods=["Hallstatt", "Ha D1"],
        confidence_level="MEDIUM",
    )


def test_schema_creation():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.duckdb"
        init_db(db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        con.close()
        assert "communes" in tables
        assert "notices" in tables
        assert "periodes" in tables
        assert "vestiges" in tables
        assert "bibliographie" in tables
        assert "figures" in tables


def test_schema_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.duckdb"
        init_db(db_path)
        init_db(db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        base_tables = [t for t in tables if not t.startswith("v_")]
        con.close()
        assert len(base_tables) == 6


def test_load_and_query():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.duckdb"
        init_db(db_path)

        communes = [_make_commune("001"), _make_commune("002", "Other")]
        records = [_make_record("001", "001"), _make_record("001", "002"), _make_record("002", "001", is_fer=False)]
        load_records(db_path, records, communes)

        stats = get_summary_stats(db_path)
        assert stats["communes"] == 2
        assert stats["notices"] == 3
        assert stats["fer_notices"] == 2


def test_views_exist():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.duckdb"
        init_db(db_path)
        con = duckdb.connect(str(db_path), read_only=True)
        for view in ["v_fer_notices", "v_stats_by_commune", "v_stats_by_type", "v_stats_by_periode", "v_period_cooccurrence"]:
            con.execute(f"SELECT * FROM {view} LIMIT 1")
        con.close()


def test_extraction_metrics():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.duckdb"
        init_db(db_path)
        communes = [_make_commune()]
        records = [_make_record()]
        load_records(db_path, records, communes)

        m = extraction_metrics(db_path)
        assert m["total_communes"] == 1
        assert m["total_notices"] == 1
        assert m["iron_age_notices"] == 1
        assert m["coverage_rate"] == 100.0


def test_idempotent_reload():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.duckdb"
        init_db(db_path)

        communes = [_make_commune()]
        records = [_make_record()]
        load_records(db_path, records, communes)
        load_records(db_path, records, communes)

        stats = get_summary_stats(db_path)
        assert stats["notices"] == 1
