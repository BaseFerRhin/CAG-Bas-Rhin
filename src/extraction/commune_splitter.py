"""Phase 2: Split aggregated page text into individual commune notices."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from .pdf_reader import PageText

logger = logging.getLogger(__name__)

_COMMUNE_RE = re.compile(
    r"^(\d{3})\s*[-–—]\s*([A-ZÀ-Ü][a-zà-ÿA-ZÀ-Ü\-\s'()]+)",
    re.MULTILINE,
)


@dataclass
class CommuneNotice:
    commune_id: str
    commune_name: str
    text: str
    page_start: int
    page_end: int


class CommuneSplitter:
    """Aggregate pages by commune, then split by header pattern."""

    def split(self, pages: list[PageText]) -> list[CommuneNotice]:
        full_text = "\n".join(p.text for p in pages)
        page_offsets = self._build_page_offsets(pages)

        matches = list(_COMMUNE_RE.finditer(full_text))
        if not matches:
            logger.warning("No commune headers found")
            return []

        notices: list[CommuneNotice] = []
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            notice_text = full_text[start:end].strip()

            page_start = self._offset_to_page(m.start(), page_offsets)
            page_end = self._offset_to_page(end - 1, page_offsets)

            notices.append(CommuneNotice(
                commune_id=m.group(1),
                commune_name=m.group(2).strip().rstrip("("),
                text=notice_text,
                page_start=page_start,
                page_end=page_end,
            ))

        logger.info("CommuneSplitter: %d communes", len(notices))
        return notices

    @staticmethod
    def _build_page_offsets(pages: list[PageText]) -> list[tuple[int, int, int]]:
        """Build (char_offset, char_end, page_num) mapping."""
        offsets: list[tuple[int, int, int]] = []
        pos = 0
        for p in pages:
            length = len(p.text) + 1
            offsets.append((pos, pos + length, p.page_num))
            pos += length
        return offsets

    @staticmethod
    def _offset_to_page(char_offset: int, offsets: list[tuple[int, int, int]]) -> int:
        for start, end, page_num in offsets:
            if start <= char_offset < end:
                return page_num
        return offsets[-1][2] if offsets else 0
