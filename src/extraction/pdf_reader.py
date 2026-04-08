"""Phase 1: Extract text from CAG 67/1 PDF page by page with 2-column handling."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)

_COMMUNE_HEADER_RE = re.compile(r"Commune[s]?\s+(\d{3}(?:\s+à\s+\d{3})?)")


@dataclass
class PageText:
    page_num: int
    text: str
    commune_header: str | None = None
    tables: list[list[list[str]]] = field(default_factory=list)


class PDFReader:
    """Extract text from CAG 67/1 PDF, handling 2-column layout via crop."""

    def __init__(self, pdf_path: Path, *, page_range: tuple[int, int] = (154, 660)):
        self._pdf_path = pdf_path
        self._start = page_range[0]
        self._end = page_range[1]

    def read_pages(self) -> list[PageText]:
        results: list[PageText] = []

        with pdfplumber.open(self._pdf_path) as pdf:
            for i in range(self._start - 1, min(self._end, len(pdf.pages))):
                page = pdf.pages[i]
                text = self._extract_two_columns(page)
                tables = page.extract_tables() or []
                commune_header = self._detect_commune_header(text)

                results.append(PageText(
                    page_num=i + 1,
                    text=text,
                    commune_header=commune_header,
                    tables=tables,
                ))

                if (i - self._start) % 50 == 0:
                    logger.debug("  page %d/%d", i + 1, self._end)

        logger.info("PDFReader: %d pages extracted", len(results))
        return results

    @staticmethod
    def _extract_two_columns(page: pdfplumber.page.Page) -> str:
        """Crop page into left/right halves and concatenate text."""
        width = page.width
        height = page.height

        left = page.crop((0, 0, width / 2, height))
        right = page.crop((width / 2, 0, width, height))

        left_text = (left.extract_text() or "").strip()
        right_text = (right.extract_text() or "").strip()

        if left_text and right_text:
            return left_text + "\n" + right_text
        return left_text or right_text

    @staticmethod
    def _detect_commune_header(text: str) -> str | None:
        m = _COMMUNE_HEADER_RE.search(text[:200])
        return m.group(1) if m else None
