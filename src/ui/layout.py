"""Main layout with navigation bar and page container."""

from __future__ import annotations

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc


def build_layout() -> html.Div:
    navbar = dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand(
                "CAG 67/1 — Carte Archéologique du Bas-Rhin",
                className="fw-bold",
                style={"fontFamily": "Inter, sans-serif"},
            ),
            dbc.Nav([
                dbc.NavLink("Carte", href="/", active="exact"),
                dbc.NavLink("Notices", href="/notices", active="exact"),
                dbc.NavLink("Chronologie", href="/chronologie", active="exact"),
                dbc.NavLink("Statistiques", href="/stats", active="exact"),
            ], navbar=True),
        ], fluid=True),
        color="dark",
        dark=True,
        sticky="top",
        style={"borderBottom": "3px solid #D95F02"},
    )

    return html.Div([
        dcc.Store(id="store-db-path", data="data/cag67.duckdb"),
        navbar,
        dbc.Container(
            dash.page_container,
            fluid=True,
            className="py-3",
        ),
    ], style={
        "backgroundColor": "#0f0f1a",
        "minHeight": "100vh",
        "fontFamily": "Inter, sans-serif",
    })
