"""Pre-defined analytical queries for the CAG 67/1 DuckDB database."""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import httpx
from pyproj import Transformer

logger = logging.getLogger(__name__)

_WGS84_TO_L93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)


def get_summary_stats(db_path: Path) -> dict:
    """Return summary statistics from the database."""
    con = duckdb.connect(str(db_path), read_only=True)

    communes = con.execute("SELECT COUNT(*) FROM communes").fetchone()[0]
    notices = con.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
    fer = con.execute("SELECT COUNT(*) FROM notices WHERE has_iron_age").fetchone()[0]
    geocoded = con.execute("SELECT COUNT(*) FROM communes WHERE latitude IS NOT NULL").fetchone()[0]
    by_type = con.execute("SELECT type_site, COUNT(*) FROM notices WHERE has_iron_age GROUP BY type_site ORDER BY 2 DESC").fetchall()
    by_periode = con.execute("SELECT periode, COUNT(DISTINCT notice_id) FROM periodes WHERE is_iron_age GROUP BY periode ORDER BY 2 DESC").fetchall()

    con.close()
    return {
        "communes": communes,
        "notices": notices,
        "fer_notices": fer,
        "geocoded": geocoded,
        "by_type": by_type,
        "by_periode": by_periode,
    }


def get_fer_notices(db_path: Path) -> list[dict]:
    """Return all Iron Age notices with commune coordinates."""
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute("SELECT * FROM v_fer_notices ORDER BY commune_id").fetchdf()
    con.close()
    return rows.to_dict("records")


def get_all_notices(db_path: Path, *, iron_age_only: bool = False) -> list[dict]:
    """Return notices, optionally filtered to Iron Age."""
    con = duckdb.connect(str(db_path), read_only=True)
    where = "WHERE has_iron_age = true" if iron_age_only else ""
    rows = con.execute(
        f"SELECT n.*, c.commune_name AS commune, c.latitude, c.longitude "
        f"FROM notices n JOIN communes c ON n.commune_id = c.commune_id {where} "
        f"ORDER BY n.commune_id, n.sous_notice_code"
    ).fetchdf()
    con.close()
    return rows.to_dict("records")


def get_commune_stats(db_path: Path) -> list[dict]:
    """Return per-commune statistics."""
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute("SELECT * FROM v_stats_by_commune ORDER BY fer_notices DESC").fetchdf()
    con.close()
    return rows.to_dict("records")


def geocode_communes(db_path: Path) -> int:
    """Geocode all communes via French BAN API and update DuckDB."""
    con = duckdb.connect(str(db_path))
    communes = con.execute(
        "SELECT commune_id, commune_name FROM communes WHERE latitude IS NULL"
    ).fetchall()

    count = 0
    for cid, name in communes:
        coords = _geocode_ban(name, department="67")
        if not coords:
            continue

        lat, lon = coords
        x_l93, y_l93 = _WGS84_TO_L93.transform(lon, lat)
        con.execute(
            "UPDATE communes SET latitude=?, longitude=?, x_l93=?, y_l93=? WHERE commune_id=?",
            [lat, lon, x_l93, y_l93, cid],
        )
        count += 1

    con.close()
    logger.info("Geocoded %d/%d communes", count, len(communes))
    return count


def _geocode_ban(commune: str, *, department: str = "67") -> tuple[float, float] | None:
    """Geocode a commune name via BAN API."""
    try:
        resp = httpx.get(
            "https://api-adresse.data.gouv.fr/search/",
            params={"q": commune, "type": "municipality", "postcode": department, "limit": 1},
            timeout=10,
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if not features:
            return None
        coords = features[0]["geometry"]["coordinates"]
        return coords[1], coords[0]
    except Exception as exc:
        logger.debug("BAN geocode failed for %s: %s", commune, exc)
        return None
