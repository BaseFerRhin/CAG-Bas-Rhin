"""Export Iron Age notices from DuckDB as RawRecord-compatible JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)


def export_raw_records(db_path: Path, output: Path, *, iron_age_only: bool = True) -> int:
    """Export DuckDB notices to a format consumable by the parent pipeline."""
    con = duckdb.connect(str(db_path), read_only=True)

    where = "WHERE n.has_iron_age = true" if iron_age_only else ""
    rows = con.execute(f"""
        SELECT n.notice_id, n.commune_id, c.commune_name, n.sous_notice_code,
               n.lieu_dit, n.type_site, n.raw_text, n.full_text, n.page_number,
               n.confidence_level, c.latitude, c.longitude
        FROM notices n
        JOIN communes c ON n.commune_id = c.commune_id
        {where}
        ORDER BY n.commune_id
    """).fetchall()

    columns = [
        "notice_id", "commune_id", "commune_name", "sous_notice_code",
        "lieu_dit", "type_site", "raw_text", "full_text", "page_number",
        "confidence_level", "latitude", "longitude",
    ]

    records = []
    for row in rows:
        d = dict(zip(columns, row))
        records.append({
            "raw_text": d["raw_text"],
            "commune": d["commune_name"],
            "type_mention": d["type_site"],
            "periode_mention": None,
            "latitude_raw": d["latitude"],
            "longitude_raw": d["longitude"],
            "source_path": str(db_path),
            "page_number": d["page_number"],
            "extraction_method": "cag_pdf_67",
            "extra": {
                "cag_commune_id": d["commune_id"],
                "source_label": "cag_67",
                "sous_notice_code": d["sous_notice_code"],
                "lieu_dit": d["lieu_dit"],
                "notice_id": d["notice_id"],
                "confidence_level": d["confidence_level"],
            },
        })

    con.close()

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Exported %d records to %s", len(records), output)
    return len(records)
