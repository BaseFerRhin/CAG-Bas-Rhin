"""Reusable notice card component."""

from __future__ import annotations

import re
from dash import html
import dash_bootstrap_components as dbc

_FER_HIGHLIGHT = re.compile(
    r"(?i)\b(hallstatt|la\s+tène|tumulus|oppidum|nécropole|"
    r"Ha\s*[A-D]\d?|LT\s*[A-D]\d?|âge\s+du\s+fer)\b"
)


def render_notice_card(notice: dict) -> dbc.Card:
    """Render a single notice as a Card component."""
    code = notice.get("sous_notice_code", "")
    lieu = notice.get("lieu_dit") or ""
    type_site = notice.get("type_site", "indéterminé")
    text = notice.get("full_text") or notice.get("raw_text", "")
    page = notice.get("page_number", "?")
    is_fer = notice.get("has_iron_age", False)
    confidence = notice.get("confidence_level", "LOW")

    header_parts = []
    if code:
        header_parts.append(f"({code})")
    if lieu:
        header_parts.append(lieu)
    header = " ".join(header_parts) or "Notice"

    badge_color = "danger" if is_fer else "secondary"
    badge_text = "Fer" if is_fer else "Autre"

    conf_colors = {"HIGH": "success", "MEDIUM": "warning", "LOW": "secondary"}

    return dbc.Card(dbc.CardBody([
        html.Div([
            html.H6(header, className="d-inline me-2"),
            html.Span(type_site, className="badge bg-info me-1"),
            html.Span(badge_text, className=f"badge bg-{badge_color} me-1"),
            html.Span(confidence, className=f"badge bg-{conf_colors.get(confidence, 'secondary')} me-1"),
            html.Span(f"p.{page}", className="badge bg-dark"),
        ]),
        html.P(
            _highlight_text(text[:800]),
            className="small text-light mt-2 mb-0",
            style={"whiteSpace": "pre-wrap", "lineHeight": "1.4"},
        ),
    ]), className="mb-2", style={"backgroundColor": "#16182d", "border": "1px solid #2a2d50"})


def _highlight_text(text: str) -> str:
    """Return text with keywords marked (Dash html.P doesn't support inline HTML,
    so we return plain text — highlighting is handled via CSS .badge in practice)."""
    return text
