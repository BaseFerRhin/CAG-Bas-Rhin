"""Page: Interactive map of communes with Iron Age sites."""

from __future__ import annotations

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from pathlib import Path

from ...storage.queries import get_commune_stats, get_all_notices

dash.register_page(__name__, path="/", name="Carte", title="CAG 67/1 — Carte")

_TYPE_COLORS = {
    "nécropole": "#6A3D9A", "habitat": "#1F78B4", "oppidum": "#E31A1C",
    "dépôt": "#FF7F00", "sanctuaire": "#33A02C", "atelier": "#B15928",
    "tumulus": "#FB9A99", "indéterminé": "#B2DF8A",
}

layout = dbc.Row([
    dbc.Col([
        html.H5("Filtres", className="text-warning mb-3"),
        dbc.Label("Type de site"),
        dcc.Dropdown(
            id="carte-type-filter",
            options=[{"label": t, "value": t} for t in _TYPE_COLORS],
            multi=True,
            placeholder="Tous les types",
            className="mb-3",
        ),
        dbc.Switch(id="carte-fer-only", label="Fer uniquement", value=True, className="mb-3"),
        html.Hr(),
        html.Div(id="carte-detail-panel"),
    ], width=3, style={"maxHeight": "85vh", "overflowY": "auto"}),
    dbc.Col([
        dcc.Graph(id="carte-map", style={"height": "85vh"}),
    ], width=9),
])


@callback(
    Output("carte-map", "figure"),
    Input("carte-type-filter", "value"),
    Input("carte-fer-only", "value"),
    State("store-db-path", "data"),
)
def update_map(types: list[str] | None, fer_only: bool, db_path: str) -> dict:
    db = Path(db_path)
    if not db.exists():
        return _empty_map()

    stats = get_commune_stats(db)
    df = pd.DataFrame(stats)

    if df.empty or "latitude" not in df.columns:
        return _empty_map()

    df = df.dropna(subset=["latitude", "longitude"])

    col = "fer_notices" if fer_only else "total_notices"
    df = df[df[col] > 0]

    if df.empty:
        return _empty_map()

    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        size=col,
        color=col,
        color_continuous_scale="YlOrRd",
        hover_name="commune_name",
        hover_data={"commune_id": True, "fer_notices": True, "total_notices": True,
                     "latitude": False, "longitude": False},
        zoom=8.5,
        center={"lat": 48.6, "lon": 7.75},
        mapbox_style="carto-darkmatter",
        size_max=20,
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="#0f0f1a",
        plot_bgcolor="#0f0f1a",
        font_color="white",
    )
    return fig


@callback(
    Output("carte-detail-panel", "children"),
    Input("carte-map", "clickData"),
    State("store-db-path", "data"),
)
def show_detail(click_data: dict | None, db_path: str) -> list:
    if not click_data:
        return [html.P("Cliquez sur une commune pour voir le détail.", className="text-muted")]

    point = click_data["points"][0]
    commune_name = point.get("hovertext", "")
    commune_id = point.get("customdata", [None])[0]

    if not commune_id:
        return [html.P("Commune non identifiée.", className="text-muted")]

    db = Path(db_path)
    notices = get_all_notices(db, iron_age_only=True)
    commune_notices = [n for n in notices if n.get("commune_id") == commune_id]

    children = [
        html.H5(f"{commune_id} — {commune_name}", className="text-warning"),
        html.P(f"{len(commune_notices)} notices âge du Fer", className="text-muted"),
        html.Hr(),
    ]

    for n in commune_notices[:15]:
        code = n.get("sous_notice_code", "")
        lieu = n.get("lieu_dit", "")
        label = f"({code}) {lieu}" if code else lieu or "Notice"
        children.append(dbc.Card(dbc.CardBody([
            html.H6(label, className="text-info mb-1"),
            html.Small(n.get("type_site", ""), className="badge bg-secondary me-1"),
            html.P(n.get("raw_text", "")[:200] + "...", className="small text-light mt-1 mb-0"),
        ]), className="mb-2", style={"backgroundColor": "#16182d"}))

    return children


def _empty_map() -> dict:
    fig = px.scatter_mapbox(
        pd.DataFrame({"lat": [48.6], "lon": [7.75]}),
        lat="lat", lon="lon", zoom=8, mapbox_style="carto-darkmatter",
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      paper_bgcolor="#0f0f1a")
    return fig
