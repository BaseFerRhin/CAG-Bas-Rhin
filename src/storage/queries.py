"""Pre-defined analytical queries for the CAG 67/1 DuckDB database."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import duckdb
import httpx
from pyproj import Transformer

logger = logging.getLogger(__name__)

_WGS84_TO_L93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)


# ── Summary ──────────────────────────────────────────────────────────────

def get_summary_stats(db_path: Path) -> dict:
    con = duckdb.connect(str(db_path), read_only=True)
    communes = con.execute("SELECT COUNT(*) FROM communes").fetchone()[0]
    notices = con.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
    fer = con.execute("SELECT COUNT(*) FROM notices WHERE has_iron_age").fetchone()[0]
    geocoded = con.execute("SELECT COUNT(*) FROM communes WHERE latitude IS NOT NULL").fetchone()[0]
    figures = con.execute("SELECT COUNT(*) FROM figures").fetchone()[0]
    by_type = con.execute(
        "SELECT type_site, COUNT(*) FROM notices WHERE has_iron_age GROUP BY type_site ORDER BY 2 DESC"
    ).fetchall()
    by_periode = con.execute(
        "SELECT periode_norm, COUNT(DISTINCT notice_id) FROM periodes WHERE is_iron_age AND periode_norm IS NOT NULL "
        "GROUP BY periode_norm ORDER BY 2 DESC"
    ).fetchall()
    con.close()
    return {
        "communes": communes, "notices": notices, "fer_notices": fer,
        "geocoded": geocoded, "figures": figures,
        "by_type": by_type, "by_periode": by_periode,
    }


def extraction_metrics(db_path: Path) -> dict:
    con = duckdb.connect(str(db_path), read_only=True)
    total_communes = con.execute("SELECT COUNT(*) FROM communes").fetchone()[0]
    total_notices = con.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
    fer = con.execute("SELECT COUNT(*) FROM notices WHERE has_iron_age").fetchone()[0]
    avg_len = con.execute("SELECT AVG(LENGTH(full_text)) FROM notices").fetchone()[0] or 0
    median_len = con.execute("SELECT MEDIAN(LENGTH(full_text)) FROM notices").fetchone()[0] or 0
    empty_communes = con.execute(
        "SELECT COUNT(*) FROM communes c WHERE NOT EXISTS (SELECT 1 FROM notices n WHERE n.commune_id = c.commune_id)"
    ).fetchone()[0]
    con.close()
    return {
        "total_communes": total_communes,
        "total_notices": total_notices,
        "iron_age_notices": fer,
        "avg_notice_length": round(avg_len),
        "median_notice_length": round(median_len),
        "communes_without_notices": empty_communes,
        "coverage_rate": round(((total_communes - empty_communes) / max(total_communes, 1)) * 100, 1),
    }


# ── Notices ──────────────────────────────────────────────────────────────

def get_fer_notices(db_path: Path) -> list[dict]:
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute("SELECT * FROM v_fer_notices ORDER BY commune_id").fetchdf()
    con.close()
    return rows.to_dict("records")


def get_all_notices(db_path: Path, *, iron_age_only: bool = False) -> list[dict]:
    con = duckdb.connect(str(db_path), read_only=True)
    where = "WHERE has_iron_age = true" if iron_age_only else ""
    rows = con.execute(
        f"SELECT n.*, c.commune_name AS commune, c.latitude, c.longitude "
        f"FROM notices n JOIN communes c ON n.commune_id = c.commune_id {where} "
        f"ORDER BY n.commune_id, n.sous_notice_code"
    ).fetchdf()
    con.close()
    return rows.to_dict("records")


def search_notices(db_path: Path, query: str, *, iron_age_only: bool = False) -> list[dict]:
    """Search notices by full-text content (AND logic for space-separated terms)."""
    con = duckdb.connect(str(db_path), read_only=True)
    terms = query.strip().split()
    where_parts = ["n.full_text ILIKE ?"] * len(terms)
    if iron_age_only:
        where_parts.append("n.has_iron_age = true")
    params = [f"%{t}%" for t in terms]
    sql = (
        "SELECT n.*, c.commune_name AS commune, c.latitude, c.longitude "
        "FROM notices n JOIN communes c ON n.commune_id = c.commune_id "
        f"WHERE {' AND '.join(where_parts)} "
        "ORDER BY n.commune_id LIMIT 200"
    )
    rows = con.execute(sql, params).fetchdf()
    con.close()
    return rows.to_dict("records")


# ── Communes ─────────────────────────────────────────────────────────────

def get_commune_stats(db_path: Path) -> list[dict]:
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute("SELECT * FROM v_stats_by_commune ORDER BY fer_notices DESC").fetchdf()
    con.close()
    return rows.to_dict("records")


def top_communes(db_path: Path, *, limit: int = 20, iron_age_only: bool = True) -> list[dict]:
    col = "fer_notices" if iron_age_only else "total_notices"
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute(
        f"SELECT * FROM v_stats_by_commune ORDER BY {col} DESC LIMIT ?", [limit]
    ).fetchdf()
    con.close()
    return rows.to_dict("records")


# ── Periods ──────────────────────────────────────────────────────────────

def period_distribution(db_path: Path, *, normalized: bool = True) -> list[dict]:
    col = "periode_norm" if normalized else "periode"
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute(
        f"SELECT {col} as periode, is_iron_age, COUNT(DISTINCT notice_id) as cnt "
        f"FROM periodes WHERE {col} IS NOT NULL GROUP BY {col}, is_iron_age ORDER BY cnt DESC"
    ).fetchdf()
    con.close()
    return rows.to_dict("records")


def period_cooccurrence(db_path: Path) -> list[tuple[str, str, int]]:
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute("SELECT * FROM v_period_cooccurrence").fetchall()
    con.close()
    return rows


# ── Vestiges ─────────────────────────────────────────────────────────────

def vestige_frequency(db_path: Path, *, iron_age_only: bool = True, limit: int = 30) -> list[dict]:
    where = "WHERE n.has_iron_age" if iron_age_only else ""
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute(
        f"SELECT v.vestige, COUNT(*) as cnt "
        f"FROM vestiges v JOIN notices n ON v.notice_id = n.notice_id {where} "
        f"GROUP BY v.vestige ORDER BY cnt DESC LIMIT ?", [limit]
    ).fetchdf()
    con.close()
    return rows.to_dict("records")


# ── Geocoding ────────────────────────────────────────────────────────────

def geocode_communes(db_path: Path, *, cache_path: Path | None = None, throttle_rps: int = 10) -> int:
    """Geocode communes via BAN API with cache and incremental update."""
    if cache_path is None:
        cache_path = Path("data/communes_geo.json")

    cache = _load_geo_cache(cache_path)

    con = duckdb.connect(str(db_path))
    communes = con.execute(
        "SELECT commune_id, commune_name FROM communes WHERE latitude IS NULL"
    ).fetchall()

    delay = 1.0 / max(throttle_rps, 1)
    count = 0

    for cid, name in communes:
        if cid in cache:
            lat, lon = cache[cid]["lat"], cache[cid]["lon"]
        else:
            coords = _geocode_ban(name, department="67")
            if not coords:
                logger.warning("BAN: no result for %s (%s)", name, cid)
                continue
            lat, lon = coords
            cache[cid] = {"lat": lat, "lon": lon, "name": name}
            time.sleep(delay)

        x_l93, y_l93 = _WGS84_TO_L93.transform(lon, lat)
        con.execute(
            "UPDATE communes SET latitude=?, longitude=?, x_l93=?, y_l93=? WHERE commune_id=?",
            [lat, lon, x_l93, y_l93, cid],
        )
        count += 1

    con.close()
    _save_geo_cache(cache_path, cache)
    logger.info("Geocoded %d/%d communes", count, len(communes))
    return count


def _geocode_ban(commune: str, *, department: str = "67") -> tuple[float, float] | None:
    try:
        resp = httpx.get(
            "https://api-adresse.data.gouv.fr/search/",
            params={"q": commune, "type": "municipality", "citycode": department, "limit": 1},
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


def _load_geo_cache(path: Path) -> dict:
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("type") == "FeatureCollection":
            cache = {}
            for f in data.get("features", []):
                props = f.get("properties", {})
                coords = f.get("geometry", {}).get("coordinates", [])
                if len(coords) == 2 and props.get("commune_id"):
                    cache[props["commune_id"]] = {
                        "lat": coords[1], "lon": coords[0], "name": props.get("commune_name", ""),
                    }
            return cache
    return {}


def _save_geo_cache(path: Path, cache: dict) -> None:
    features = []
    for cid, v in sorted(cache.items()):
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [v["lon"], v["lat"]]},
            "properties": {"commune_id": cid, "commune_name": v.get("name", "")},
        })
    geojson = {"type": "FeatureCollection", "features": features}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
