"""Orchestrate the 4-phase extraction: PDF → text → communes → notices → DuckDB."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


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

    t0 = time.time()

    console.rule("[bold orange1]Phase 1: PDF text extraction")
    reader = PDFReader(pdf_path, page_range=page_range)
    pages = reader.read_pages()
    console.print(f"  [green]{len(pages)}[/green] pages extracted")

    console.rule("[bold orange1]Phase 2: Commune splitting")
    splitter = CommuneSplitter()
    communes = splitter.split(pages)
    console.print(f"  [green]{len(communes)}[/green] commune notices")

    console.rule("[bold orange1]Phase 3: Sub-notice parsing")
    parser = NoticeParser()
    all_sub_notices = []
    for commune in communes:
        subs = parser.parse(commune)
        all_sub_notices.extend(subs)
    console.print(f"  [green]{len(all_sub_notices)}[/green] sub-notices")

    console.rule("[bold orange1]Phase 4: Iron Age filter + record building")
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

    console.print(f"  [green]{len(records)}[/green] records ([bold]{fer_count}[/bold] Iron Age)")

    console.rule("[bold orange1]Loading into DuckDB")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    init_db(db_path)
    load_records(db_path, records, communes)
    console.print(f"  → {db_path}")

    elapsed = time.time() - t0

    # Quality metrics
    pages_with_header = sum(1 for p in pages if p.commune_header)
    coverage = (pages_with_header / max(len(pages), 1)) * 100
    communes_with_notices = len({r.commune_id for r in records})
    notices_per_commune = len(all_sub_notices) / max(len(communes), 1)
    zero_sub = sum(1 for c in communes if not any(s.commune_id == c.commune_id for s in all_sub_notices))
    text_lengths = [len(r.full_text) for r in records]
    avg_len = sum(text_lengths) / max(len(text_lengths), 1)

    stats = {
        "pages": len(pages),
        "communes": len(communes),
        "notices": len(records),
        "fer_notices": fer_count,
        "elapsed_s": round(elapsed, 1),
        "coverage_pct": round(coverage, 1),
        "avg_notices_per_commune": round(notices_per_commune, 1),
        "communes_zero_sub": zero_sub,
        "avg_notice_len": round(avg_len),
    }

    _print_summary(stats)
    return stats


def _print_summary(stats: dict) -> None:
    console.rule("[bold green]Extraction Summary")

    tbl = Table(show_header=False, box=None)
    tbl.add_column(style="bold")
    tbl.add_column(style="green")

    tbl.add_row("Pages traitées", str(stats["pages"]))
    tbl.add_row("Communes", str(stats["communes"]))
    tbl.add_row("Notices totales", str(stats["notices"]))
    tbl.add_row("Notices Fer", str(stats["fer_notices"]))
    tbl.add_row("Temps", f"{stats['elapsed_s']}s")
    tbl.add_row("Couverture header", f"{stats['coverage_pct']}%")
    tbl.add_row("Moy. notices/commune", str(stats["avg_notices_per_commune"]))
    tbl.add_row("Communes sans sub-notice", str(stats["communes_zero_sub"]))
    tbl.add_row("Longueur moy. notice", f"{stats['avg_notice_len']} chars")

    console.print(tbl)
