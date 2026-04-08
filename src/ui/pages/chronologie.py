"""Page: Chronological overview of all periods mentioned in CAG 67/1."""

from __future__ import annotations

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

import duckdb

dash.register_page(__name__, path="/chronologie", name="Chronologie", title="CAG 67/1 — Chronologie")

_PERIOD_COLORS = {
    "Hallstatt": "#D95F02", "La Tène": "#1B9E77", "Âge du Fer": "#E6550D",
    "Gallo-romain": "#7570B3", "Néolithique": "#A6761D", "Âge du Bronze": "#E6AB02",
    "Mérovingien": "#66A61E", "Médiéval": "#E7298A", "Carolingien": "#A6CEE3",
    "BF III": "#FDBF6F", "Mésolithique": "#B2DF8A", "Paléolithique": "#CAB2D6",
    "Ha A": "#FDD0A2", "Ha B": "#FDAE6B", "Ha C": "#FD8D3C", "Ha D": "#E6550D",
    "Ha D1": "#D94701", "Ha D2": "#A63603", "Ha D3": "#7F2704",
    "LT A": "#BAE4B3", "LT B": "#74C476", "LT C": "#31A354", "LT D": "#006D2C",
}

layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H4("Frise chronologique — CAG 67/1", className="text-warning mb-4"),
            dcc.Graph(id="chrono-bar-all", style={"height": "350px"}),
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.H5("Sous-périodes âge du Fer", className="text-info mt-4 mb-3"),
            dcc.Graph(id="chrono-bar-fer", style={"height": "280px"}),
        ], width=7),
        dbc.Col([
            html.H5("Co-occurrences", className="text-info mt-4 mb-3"),
            dcc.Graph(id="chrono-heatmap", style={"height": "280px"}),
        ], width=5),
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
        "SELECT periode_norm as periode, COUNT(DISTINCT notice_id) as cnt "
        "FROM periodes WHERE periode_norm IS NOT NULL "
        "GROUP BY periode_norm ORDER BY cnt DESC"
    ).fetchdf()

    fer_sub = con.execute("""
        SELECT periode_norm as periode, COUNT(DISTINCT notice_id) as cnt
        FROM periodes
        WHERE periode_norm IN ('Ha A','Ha B','Ha C','Ha D','Ha D1','Ha D2','Ha D3',
                               'LT A','LT B','LT C','LT D','BF III')
        GROUP BY periode_norm ORDER BY cnt DESC
    """).fetchdf()

    cooc = con.execute("SELECT * FROM v_period_cooccurrence LIMIT 100").fetchdf()
    con.close()

    # All periods bar
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

    # Iron Age sub-periods
    fig_fer = px.bar(
        fer_sub, x="cnt", y="periode", orientation="h",
        color="periode", color_discrete_map=_PERIOD_COLORS,
        labels={"cnt": "Notices", "periode": ""},
    )
    fig_fer.update_layout(
        showlegend=False,
        paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
        font_color="white", margin={"l": 80},
    )

    # Co-occurrence heatmap
    if not cooc.empty and len(cooc) > 0:
        periods_a = sorted(cooc["period_a"].unique())
        periods_b = sorted(cooc["period_b"].unique())
        all_p = sorted(set(periods_a) | set(periods_b))

        matrix = pd.DataFrame(0, index=all_p, columns=all_p)
        for _, row in cooc.iterrows():
            matrix.loc[row["period_a"], row["period_b"]] = row["co_count"]
            matrix.loc[row["period_b"], row["period_a"]] = row["co_count"]

        fig_heat = go.Figure(data=go.Heatmap(
            z=matrix.values, x=matrix.columns.tolist(), y=matrix.index.tolist(),
            colorscale="YlOrRd", showscale=True,
        ))
    else:
        fig_heat = go.Figure(data=go.Heatmap(z=[[0]], x=["—"], y=["—"], colorscale="YlOrRd"))

    fig_heat.update_layout(
        paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
        font_color="white", margin={"l": 80, "t": 20, "r": 20},
    )

    return fig_all, fig_fer, fig_heat
