"""Phase 4: Iron Age keyword detection and period extraction."""

from __future__ import annotations

import re

_FER_KEYWORDS = re.compile(
    r"(?i)\b(?:hallstatt|la\s+tène|âge\s+du\s+fer|protohistor|"
    r"tumulus|tertre\s+funéraire|Ha\s*[CD]\d?|LT\s*[A-D]\d?|"
    r"premier\s+âge\s+du\s+fer|second\s+âge\s+du\s+fer|"
    r"âge\s+du\s+bronze\s+final|BF\s*III|"
    r"époque\s+de\s+hallstatt|eisenzeit|latènezeit)\b"
)

_ALL_PERIODS = re.compile(
    r"(?i)\b(?:hallstatt|la\s+tène|âge\s+du\s+fer|âge\s+du\s+bronze|"
    r"protohistor|gallo[- ]?romain|néolith|mésolithique|paléolithique|"
    r"méroving|caroling|médiéval|moyen\s+âge|romain|"
    r"Ha\s*[CD]\d?|LT\s*[A-D]\d?|BF\s*[I]{1,3}[a-b]?)\b"
)


class IronAgeFilter:
    """Detect Iron Age relevance and extract all period mentions from text."""

    def is_iron_age(self, text: str) -> bool:
        return bool(_FER_KEYWORDS.search(text))

    def extract_iron_age_terms(self, text: str) -> list[str]:
        return list({m.group() for m in _FER_KEYWORDS.finditer(text)})

    def extract_all_periods(self, text: str) -> list[str]:
        return list({m.group() for m in _ALL_PERIODS.finditer(text)})
