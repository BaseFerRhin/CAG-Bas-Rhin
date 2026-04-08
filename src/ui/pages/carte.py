"""Page: Interactive map of communes with Iron Age sites."""

from __future__ import annotations

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from pathlib import Path

from ...storage.queries import get_commune_stats, get_all_notices
from ..components.commune_map import create_commune_map, empty_map, TYPE_COLORS

dash.register_page(__name__, path="/", name="Carte", title="CAG 67/1 — Carte")

layout = dbc.Row([
    dbc.Col([
        html.H5("Filtres", className="text-warning mb-3"),
        dbc.Label("Type de site"),
        dcc.Dropdown(
            id="carte-type-filter",
            options=[{"label": t, "value": t} for t in TYPE_COLORS],
            multi=True,
            placeholder="Tous les types",
            className="mb-3",
        ),
        dbc.Label("Période normalisée"),
        dcc.Dropdown(
            id="carte-period-filter",
            multi=True,
            placeholder="Toutes les périodes",
            className="mb-3",
        ),
        dbc.Label("Notices minimum"),
        dcc.Slider(id="carte-min-notices", min=1, max=20, step=1, value=1,
                   marks={1: "1", 5: "5", 10: "10", 20: "20"}),
        dbc.Switch(id="carte-fer-only", label="Fer uniquement", value=True, className="mt-3 mb-3"),
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
    Input("carte-period-filter", "value"),
    Input("carte-min-notices", "value"),
    Input("carte-fer-only", "value"),
    State("store-db-path", "data"),
)
def update_map(types: list[str] | None, periods: list[str] | None,
               min_notices: int, fer_only: bool, db_path: str) -> dict:
    db = Path(db_path)
    if not db.exists():
        return empty_map()

    stats = get_commune_stats(db)
    df = pd.DataFrame(stats)

    if df.empty or "latitude" not in df.columns:
        return empty_map()

    df = df.dropna(subset=["latitude", "longitude"])
    col = "fer_notices" if fer_only else "total_notices"
    df = df[df[col] >= (min_notices or 1)]

    if df.empty:
        return empty_map()

    return create_commune_map(df, size_col=col)


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
        conf = n.get("confidence_level", "LOW")
        conf_colors = {"HIGH": "success", "MEDIUM": "warning", "LOW": "secondary"}
        children.append(dbc.Card(dbc.CardBody([
            html.H6(label, className="text-info mb-1"),
            html.Small(n.get("type_site", ""), className="badge bg-secondary me-1"),
            html.Small(conf, className=f"badge bg-{conf_colors.get(conf, 'secondary')} me-1"),
            html.P(n.get("raw_text", "")[:200] + "...", className="small text-light mt-1 mb-0"),
        ]), className="mb-2", style={"backgroundColor": "#16182d"}))

    return children
