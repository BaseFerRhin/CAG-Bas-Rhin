"""Load extracted records into DuckDB."""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from ..extraction.commune_splitter import CommuneNotice
from ..extraction.iron_age_filter import IronAgeFilter
from ..extraction.record_builder import SiteRecord

logger = logging.getLogger(__name__)

_filter = IronAgeFilter()


def load_records(
    db_path: Path,
    records: list[SiteRecord],
    communes: list[CommuneNotice],
) -> None:
    """Insert communes and records into DuckDB, replacing existing data."""
    con = duckdb.connect(str(db_path))

    con.execute("DELETE FROM figures")
    con.execute("DELETE FROM bibliographie")
    con.execute("DELETE FROM vestiges")
    con.execute("DELETE FROM periodes")
    con.execute("DELETE FROM notices")
    con.execute("DELETE FROM communes")

    _load_communes(con, communes)
    _load_notices(con, records)
    _load_periodes(con, records)
    _load_vestiges(con, records)
    _load_bibliographie(con, records)
    _load_figures(con, records)

    con.close()
    logger.info("Loaded %d communes, %d notices into %s", len(communes), len(records), db_path)


def _load_communes(con: duckdb.DuckDBPyConnection, communes: list[CommuneNotice]) -> None:
    seen: set[str] = set()
    for c in communes:
        if c.commune_id in seen:
            continue
        seen.add(c.commune_id)
        con.execute(
            "INSERT INTO communes (commune_id, commune_name, page_start, page_end) VALUES (?, ?, ?, ?)",
            [c.commune_id, c.commune_name, c.page_start, c.page_end],
        )


def _load_notices(con: duckdb.DuckDBPyConnection, records: list[SiteRecord]) -> None:
    for r in records:
        con.execute(
            "INSERT INTO notices (notice_id, commune_id, sous_notice_code, lieu_dit, "
            "type_site, raw_text, full_text, page_number, has_iron_age, confidence_level) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [r.notice_id, r.commune_id, r.sous_notice_code, r.lieu_dit,
             r.type_site, r.raw_text, r.full_text, r.page_number, r.has_iron_age,
             r.confidence_level],
        )


def _load_periodes(con: duckdb.DuckDBPyConnection, records: list[SiteRecord]) -> None:
    for r in records:
        for p in r.all_periods:
            norm = _filter.normalize_period(p)
            is_fer = _filter.is_fer_norm(norm) if norm else False
            con.execute(
                "INSERT INTO periodes (notice_id, periode, periode_norm, is_iron_age) VALUES (?, ?, ?, ?)",
                [r.notice_id, p, norm, is_fer],
            )


def _load_vestiges(con: duckdb.DuckDBPyConnection, records: list[SiteRecord]) -> None:
    for r in records:
        for v in r.vestiges_mentions:
            con.execute(
                "INSERT INTO vestiges (notice_id, vestige) VALUES (?, ?)",
                [r.notice_id, v],
            )


def _load_bibliographie(con: duckdb.DuckDBPyConnection, records: list[SiteRecord]) -> None:
    for r in records:
        for b in r.bibliographie:
            con.execute(
                "INSERT INTO bibliographie (notice_id, reference) VALUES (?, ?)",
                [r.notice_id, b],
            )


def _load_figures(con: duckdb.DuckDBPyConnection, records: list[SiteRecord]) -> None:
    for r in records:
        for f in r.figures_refs:
            con.execute(
                "INSERT INTO figures (notice_id, figure_ref, page_number) VALUES (?, ?, ?)",
                [r.notice_id, f, r.page_number],
            )
