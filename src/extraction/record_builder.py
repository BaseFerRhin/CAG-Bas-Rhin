"""Phase 4: Build SiteRecord from parsed sub-notice."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .notice_parser import SubNotice

_VESTIGES_RE = re.compile(
    r"(?i)\b(?:tumulus|tertre|sépulture|nécropole|habitat|oppidum|"
    r"fortification|enceinte|silo|fosse|four|atelier|dépôt|"
    r"tombe|inhumation|incinération|urne|céramique|tessons?|"
    r"fibule|bracelet|épée|monnaie|torque|hache|rasoir|"
    r"poignard|anneau|poterie|sanctuaire|fanum|lieu\s+de\s+culte|"
    r"Viereckschanze|Grabhügel|Hügelgrab|Flachgrab|Ringwall|"
    r"Siedlung|Brandgrab|Fürstengrab)\b"
)


@dataclass
class SiteRecord:
    notice_id: str
    commune_id: str
    commune_name: str
    sous_notice_code: str | None
    lieu_dit: str | None
    type_site: str
    periode_mentions: list[str]
    vestiges_mentions: list[str]
    raw_text: str
    full_text: str
    page_number: int
    bibliographie: list[str]
    figures_refs: list[str]
    has_iron_age: bool
    all_periods: list[str]
    confidence_level: str  # HIGH / MEDIUM / LOW


class RecordBuilder:
    """Construct a SiteRecord from a parsed SubNotice."""

    def __init__(self, source_label: str = "cag_67"):
        self._label = source_label
        self._seen_ids: dict[str, int] = {}

    def build(
        self,
        sub: SubNotice,
        *,
        is_fer: bool,
        all_periods: list[str],
    ) -> SiteRecord:
        vestiges = list({m.group().lower() for m in _VESTIGES_RE.finditer(sub.text)})
        type_site = self._guess_type(vestiges)
        code_suffix = f"-{sub.sous_notice_code}" if sub.sous_notice_code else ""
        base_id = f"CAG67-{sub.commune_id}{code_suffix}"
        if base_id in self._seen_ids:
            self._seen_ids[base_id] += 1
            notice_id = f"{base_id}_{self._seen_ids[base_id]}"
        else:
            self._seen_ids[base_id] = 0
            notice_id = base_id

        fer_periods = [p for p in all_periods if self._is_fer_period(p)]

        confidence = self._estimate_confidence(sub.text, sub.bibliographie)

        return SiteRecord(
            notice_id=notice_id,
            commune_id=sub.commune_id,
            commune_name=sub.commune_name,
            sous_notice_code=sub.sous_notice_code,
            lieu_dit=sub.lieu_dit,
            type_site=type_site,
            periode_mentions=fer_periods,
            vestiges_mentions=vestiges,
            raw_text=sub.text[:500],
            full_text=sub.text,
            page_number=sub.page_number,
            bibliographie=sub.bibliographie,
            figures_refs=sub.figures_refs,
            has_iron_age=is_fer,
            all_periods=all_periods,
            confidence_level=confidence,
        )

    @staticmethod
    def _guess_type(vestiges: list[str]) -> str:
        v = {x.lower() for x in vestiges}
        if v & {"oppidum", "fortification", "enceinte", "ringwall", "fürstensitz"}:
            return "oppidum"
        if v & {"sanctuaire", "fanum", "lieu de culte", "viereckschanze"}:
            return "sanctuaire"
        if v & {"nécropole"}:
            return "nécropole"
        if v & {"tumulus", "tertre", "grabhügel", "hügelgrab", "fürstengrab"}:
            return "tumulus"
        if v & {"tombe", "sépulture", "inhumation", "incinération", "urne", "brandgrab", "flachgrab"}:
            return "sépulture"
        if v & {"habitat", "silo", "fosse", "four", "siedlung"}:
            return "habitat"
        if v & {"atelier"}:
            return "atelier"
        if v & {"dépôt"}:
            return "dépôt"
        return "indéterminé"

    @staticmethod
    def _is_fer_period(period: str) -> bool:
        p = period.lower()
        return any(k in p for k in ("hallstatt", "tène", "fer", "ha ", "lt ", "protohistor", "eisenzeit", "latènezeit"))

    @staticmethod
    def _estimate_confidence(text: str, biblio: list[str]) -> str:
        """Heuristic confidence based on source quality indicators."""
        t = text.lower()
        has_fouille = any(k in t for k in ("fouille", "sondage", "prospection systématique", "grabung"))
        recent_refs = any(re.search(r"\b(19[89]\d|20[0-2]\d)\b", ref) for ref in biblio)
        has_figures = "fig." in t

        if has_fouille and recent_refs:
            return "HIGH"
        if recent_refs or has_figures or len(biblio) >= 3:
            return "MEDIUM"
        return "LOW"
