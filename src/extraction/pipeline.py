"""Orchestrate the 4-phase extraction: PDF → text → communes → notices → DuckDB."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run_extraction(
    *,
    pdf_path: Path,
    db_path: Path,
    page_range: tuple[int, int] = (154, 660),
    source_label: str = "cag_67",
) -> dict:
    """Run the full extraction pipeline and return stats."""
    from .pdf_reader import PDFReader
    from .commune_splitter import CommuneSplitter
    from .notice_parser import NoticeParser
    from .iron_age_filter import IronAgeFilter
    from .record_builder import RecordBuilder
    from ..storage.schema import init_db
    from ..storage.loader import load_records

    logger.info("Phase 1: PDF text extraction (%s)", pdf_path.name)
    reader = PDFReader(pdf_path, page_range=page_range)
    pages = reader.read_pages()
    logger.info("  %d pages extracted", len(pages))

    logger.info("Phase 2: Commune splitting")
    splitter = CommuneSplitter()
    communes = splitter.split(pages)
    logger.info("  %d commune notices", len(communes))

    logger.info("Phase 3: Sub-notice parsing")
    parser = NoticeParser()
    all_sub_notices = []
    for commune in communes:
        subs = parser.parse(commune)
        all_sub_notices.extend(subs)
    logger.info("  %d sub-notices", len(all_sub_notices))

    logger.info("Phase 4: Iron Age filter + record building")
    fer_filter = IronAgeFilter()
    builder = RecordBuilder(source_label=source_label)

    records = []
    fer_count = 0
    for sub in all_sub_notices:
        is_fer = fer_filter.is_iron_age(sub.text)
        all_periods = fer_filter.extract_all_periods(sub.text)
        record = builder.build(sub, is_fer=is_fer, all_periods=all_periods)
        records.append(record)
        if is_fer:
            fer_count += 1

    logger.info("  %d records (%d Iron Age)", len(records), fer_count)

    logger.info("Loading into DuckDB: %s", db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    init_db(db_path)
    load_records(db_path, records, communes)

    return {
        "pages": len(pages),
        "communes": len(communes),
        "notices": len(records),
        "fer_notices": fer_count,
    }
