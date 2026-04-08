"""Phase 4: Iron Age keyword detection, period extraction and normalization."""

from __future__ import annotations

import re

_FER_KEYWORDS = re.compile(
    r"(?i)\b(?:hallstatt|la\s+tène|âge\s+du\s+fer|protohistor|"
    r"tumulus|tertre\s+funéraire|Ha\s*[A-D]\d?|LT\s*[A-D]\d?|"
    r"premier\s+âge\s+du\s+fer|second\s+âge\s+du\s+fer|"
    r"âge\s+du\s+bronze\s+final|BF\s*III[a-b]?|"
    r"LT\s+finale|La\s+Tène\s+finale|"
    r"époque\s+de\s+hallstatt|hallstattien(?:ne)?|latènien(?:ne)?|eisenzeit|latènezeit|"
    r"Grabhügel|Hügelgrab|Flachgrab|Ringwall|"
    r"Viereckschanze|Fürstengrab|Fürstensitz)\b"
)

_ALL_PERIODS = re.compile(
    r"(?i)\b(?:hallstatt|la\s+tène|âge\s+du\s+fer|âge\s+du\s+bronze|"
    r"protohistor|gallo[- ]?romain|néolith|mésolithique|paléolithique|"
    r"méroving|caroling|médiéval|moyen\s+âge|romain|"
    r"Ha\s*[A-D]\d?|LT\s*[A-D]\d?|BF\s*[I]{1,3}[a-b]?|"
    r"LT\s+finale|La\s+Tène\s+finale|eisenzeit|latènezeit)\b"
)

_NORM_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?i)\bHa\s*A\d?\b"), "Ha A"),
    (re.compile(r"(?i)\bHa\s*B\d?\b"), "Ha B"),
    (re.compile(r"(?i)\bHa\s*C\d?\b"), "Ha C"),
    (re.compile(r"(?i)\bHa\s*D1\b"), "Ha D1"),
    (re.compile(r"(?i)\bHa\s*D2\b"), "Ha D2"),
    (re.compile(r"(?i)\bHa\s*D3\b"), "Ha D3"),
    (re.compile(r"(?i)\bHa\s*D\b(?!\d)"), "Ha D"),
    (re.compile(r"(?i)\bLT\s*A\d?\b"), "LT A"),
    (re.compile(r"(?i)\bLT\s*B\d?\b"), "LT B"),
    (re.compile(r"(?i)\bLT\s*C\d?\b"), "LT C"),
    (re.compile(r"(?i)\bLT\s*D\d?\b|LT\s+finale|La\s+Tène\s+finale"), "LT D"),
    (re.compile(r"(?i)\bBF\s*III[a-b]?\b|âge\s+du\s+bronze\s+final"), "BF III"),
    (re.compile(r"(?i)\bhallstatt|époque\s+de\s+hallstatt|eisenzeit|premier\s+âge\s+du\s+fer"), "Hallstatt"),
    (re.compile(r"(?i)\bla\s+tène|latènezeit|second\s+âge\s+du\s+fer"), "La Tène"),
    (re.compile(r"(?i)\bâge\s+du\s+fer|protohistor"), "Âge du Fer"),
    (re.compile(r"(?i)\bgallo[- ]?romain|romain"), "Gallo-romain"),
    (re.compile(r"(?i)\bnéolith"), "Néolithique"),
    (re.compile(r"(?i)\bmésolithique"), "Mésolithique"),
    (re.compile(r"(?i)\bpaléolithique"), "Paléolithique"),
    (re.compile(r"(?i)\bâge\s+du\s+bronze\b(?!\s+final)"), "Âge du Bronze"),
    (re.compile(r"(?i)\bméroving"), "Mérovingien"),
    (re.compile(r"(?i)\bcaroling"), "Carolingien"),
    (re.compile(r"(?i)\bmédiéval|moyen\s+âge"), "Médiéval"),
]

_FER_NORMS = frozenset({
    "Ha A", "Ha B", "Ha C", "Ha D", "Ha D1", "Ha D2", "Ha D3",
    "LT A", "LT B", "LT C", "LT D", "BF III",
    "Hallstatt", "La Tène", "Âge du Fer",
})


class IronAgeFilter:
    """Detect Iron Age relevance and extract all period mentions from text."""

    def is_iron_age(self, text: str) -> bool:
        return bool(_FER_KEYWORDS.search(text))

    def extract_iron_age_terms(self, text: str) -> list[str]:
        return list({m.group() for m in _FER_KEYWORDS.finditer(text)})

    def extract_all_periods(self, text: str) -> list[str]:
        return list({m.group() for m in _ALL_PERIODS.finditer(text)})

    @staticmethod
    def normalize_period(raw: str) -> str | None:
        """Map a raw period mention to a controlled vocabulary term."""
        for pattern, norm in _NORM_MAP:
            if pattern.search(raw):
                return norm
        return None

    @staticmethod
    def is_fer_norm(norm: str) -> bool:
        return norm in _FER_NORMS
