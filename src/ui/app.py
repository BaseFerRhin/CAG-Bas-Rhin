"""Dash application factory for CAG 67/1 explorer."""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc


def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        use_pages=True,
        external_stylesheets=[
            dbc.themes.DARKLY,
            "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        ],
        suppress_callback_exceptions=True,
        title="CAG 67/1 — Bas-Rhin",
    )

    from .layout import build_layout
    app.layout = build_layout()

    from . import callbacks  # noqa: F401 — register callbacks

    return app
