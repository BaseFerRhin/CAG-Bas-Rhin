"""Page: Chronological overview of all periods mentioned in CAG 67/1."""

from __future__ import annotations

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

import duckdb

dash.register_page(__name__, path="/chronologie", name="Chronologie", title="CAG 67/1 — Chronologie")

_PERIOD_COLORS = {
    "Hallstatt": "#D95F02", "hallstatt": "#D95F02",
    "La Tène": "#1B9E77", "la tène": "#1B9E77",
    "gallo-romain": "#7570B3",
    "néolithique": "#A6761D",
    "âge du Bronze": "#E6AB02",
    "mérovingien": "#66A61E",
    "médiéval": "#E7298A",
    "romain": "#7570B3",
}

layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H4("Frise chronologique — CAG 67/1", className="text-warning mb-4"),
            dcc.Graph(id="chrono-bar-all", style={"height": "300px"}),
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.H5("Sous-périodes âge du Fer", className="text-info mt-4 mb-3"),
            dcc.Graph(id="chrono-bar-fer", style={"height": "250px"}),
        ], width=8),
        dbc.Col([
            html.H5("Co-occurrences", className="text-info mt-4 mb-3"),
            dcc.Graph(id="chrono-heatmap", style={"height": "250px"}),
        ], width=4),
    ]),
])


@callback(
    Output("chrono-bar-all", "figure"),
    Output("chrono-bar-fer", "figure"),
    Output("chrono-heatmap", "figure"),
    Input("store-db-path", "data"),
)
def update_chronology(db_path: str) -> tuple[dict, dict, dict]:
    db = Path(db_path)
    if not db.exists():
        empty = px.bar(title="Base non trouvée")
        return empty, empty, empty

    con = duckdb.connect(str(db), read_only=True)

    all_periods = con.execute(
        "SELECT periode, COUNT(DISTINCT notice_id) as cnt FROM periodes GROUP BY periode ORDER BY cnt DESC"
    ).fetchdf()

    fer_sub = con.execute("""
        SELECT periode, COUNT(DISTINCT notice_id) as cnt
        FROM periodes
        WHERE periode SIMILAR TO '(Ha|LT|hallstatt|la tène|Hallstatt|La Tène).*'
        GROUP BY periode ORDER BY cnt DESC
    """).fetchdf()

    con.close()

    fig_all = px.bar(
        all_periods, x="cnt", y="periode", orientation="h",
        color="periode", color_discrete_map=_PERIOD_COLORS,
        labels={"cnt": "Notices", "periode": "Période"},
    )
    fig_all.update_layout(
        showlegend=False,
        paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
        font_color="white", margin={"l": 150},
    )

    fig_fer = px.bar(
        fer_sub, x="cnt", y="periode", orientation="h",
        color_discrete_sequence=["#D95F02"],
        labels={"cnt": "Notices", "periode": ""},
    )
    fig_fer.update_layout(
        paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
        font_color="white", margin={"l": 80},
    )

    fig_heat = go.Figure(data=go.Heatmap(
        z=[[0]], x=["—"], y=["—"],
        colorscale="YlOrRd",
    ))
    fig_heat.update_layout(
        paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
        font_color="white", margin={"l": 80, "t": 20},
        annotations=[dict(text="Données en cours", showarrow=False, font=dict(color="grey"))],
    )

    return fig_all, fig_fer, fig_heat
