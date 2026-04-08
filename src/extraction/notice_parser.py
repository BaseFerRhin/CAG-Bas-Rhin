"""Phase 3: Parse a commune notice into sub-notices (lieu-dit level)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from .commune_splitter import CommuneNotice

logger = logging.getLogger(__name__)

_NUMBERED_RE = re.compile(r"\n\s*(\d+)\*\s*\((\d{3}(?:\s*[A-Z]{2})?)\)\s*")
_LIEU_DIT_RE = re.compile(
    r"(?:Au[x]?\s+lieu[x]?-dit[s]?\s+)(.+?)(?:\.|,\s*(?:en|à|vers|entre|des|dans|un|une|le|la|les))",
    re.IGNORECASE,
)
_BIBLIO_RE = re.compile(r"([A-Z][a-zà-ÿ]+(?:\s+et\s+alii)?,\s*\d{4}[a-z]?)")
_FIG_REF_RE = re.compile(r"Fig\.\s*(\d+[a-z]?)")


@dataclass
class SubNotice:
    commune_id: str
    commune_name: str
    entry_number: int | None
    sous_notice_code: str | None
    lieu_dit: str | None
    text: str
    page_number: int
    bibliographie: list[str]
    figures_refs: list[str]


class NoticeParser:
    """Split a commune notice into sub-notices by numbered entries."""

    def parse(self, notice: CommuneNotice) -> list[SubNotice]:
        parts = _NUMBERED_RE.split(notice.text)

        if len(parts) <= 1:
            return [self._build_sub(notice, None, None, notice.text, notice.page_start)]

        result: list[SubNotice] = []

        if parts[0].strip():
            result.append(self._build_sub(notice, None, None, parts[0].strip(), notice.page_start))

        i = 1
        while i < len(parts) - 1:
            entry_num = int(parts[i])
            code = parts[i + 1].strip()
            text = parts[i + 2].strip() if i + 2 < len(parts) else ""

            result.append(self._build_sub(notice, entry_num, code, text, notice.page_start))
            i += 3

        return result

    def _build_sub(
        self,
        notice: CommuneNotice,
        entry_num: int | None,
        code: str | None,
        text: str,
        page: int,
    ) -> SubNotice:
        lieu_dit = self._extract_lieu_dit(text)
        biblio = _BIBLIO_RE.findall(text)
        figs = [f"Fig. {n}" for n in _FIG_REF_RE.findall(text)]

        return SubNotice(
            commune_id=notice.commune_id,
            commune_name=notice.commune_name,
            entry_number=entry_num,
            sous_notice_code=code,
            lieu_dit=lieu_dit,
            text=text,
            page_number=page,
            bibliographie=biblio,
            figures_refs=figs,
        )

    @staticmethod
    def _extract_lieu_dit(text: str) -> str | None:
        m = _LIEU_DIT_RE.search(text[:200])
        return m.group(1).strip() if m else None
