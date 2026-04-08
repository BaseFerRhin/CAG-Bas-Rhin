"""Page: Statistics dashboard for CAG 67/1 data."""

from __future__ import annotations

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from pathlib import Path

from ...storage.queries import get_summary_stats, get_commune_stats

dash.register_page(__name__, path="/stats", name="Statistiques", title="CAG 67/1 — Stats")

_TYPE_COLORS = {
    "nécropole": "#6A3D9A", "habitat": "#1F78B4", "oppidum": "#E31A1C",
    "tumulus": "#FB9A99", "sépulture": "#CAB2D6", "sanctuaire": "#33A02C",
    "dépôt": "#FF7F00", "atelier": "#B15928", "indéterminé": "#B2DF8A",
}

layout = html.Div([
    html.H4("Statistiques — CAG 67/1", className="text-warning mb-4"),
    dbc.Row(id="stats-kpis", className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="stats-type-donut"), width=4),
        dbc.Col(dcc.Graph(id="stats-top-communes"), width=8),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="stats-vestiges-treemap"), width=8, className="mt-3"),
        dbc.Col(dcc.Graph(id="stats-confidence"), width=4, className="mt-3"),
    ]),
])


@callback(
    Output("stats-kpis", "children"),
    Output("stats-type-donut", "figure"),
    Output("stats-top-communes", "figure"),
    Output("stats-vestiges-treemap", "figure"),
    Output("stats-confidence", "figure"),
    Input("store-db-path", "data"),
)
def update_stats(db_path: str):
    db = Path(db_path)
    if not db.exists():
        empty = px.bar(title="Base non trouvée")
        return [], empty, empty, empty, empty

    s = get_summary_stats(db)

    kpis = dbc.Row([
        _kpi_card("Communes", s["communes"], "#1F78B4"),
        _kpi_card("Notices", s["notices"], "#6A3D9A"),
        _kpi_card("Notices Fer", s["fer_notices"], "#D95F02"),
        _kpi_card("Figures", s["figures"], "#33A02C"),
    ])

    # Donut chart: site types
    type_df = pd.DataFrame(s["by_type"], columns=["type_site", "count"])
    fig_type = px.pie(
        type_df, values="count", names="type_site",
        color="type_site", color_discrete_map=_TYPE_COLORS,
        hole=0.4,
    )
    fig_type.update_layout(
        paper_bgcolor="#0f0f1a", font_color="white",
        legend=dict(font=dict(size=11)),
        margin={"t": 30, "b": 10},
        title="Types de sites (Fer)",
    )

    # Top communes bar
    commune_stats = get_commune_stats(db)
    top = pd.DataFrame(commune_stats).nlargest(20, "fer_notices")
    fig_communes = px.bar(
        top, x="fer_notices", y="commune_name", orientation="h",
        color_discrete_sequence=["#D95F02"],
        labels={"fer_notices": "Notices Fer", "commune_name": ""},
        title="Top 20 communes (notices Fer)",
    )
    fig_communes.update_layout(
        paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
        font_color="white", margin={"l": 150},
        yaxis={"categoryorder": "total ascending"},
    )

    # Vestiges treemap
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    vestiges_df = con.execute("""
        SELECT v.vestige, COUNT(*) as cnt
        FROM vestiges v JOIN notices n ON v.notice_id = n.notice_id
        WHERE n.has_iron_age GROUP BY v.vestige ORDER BY cnt DESC LIMIT 30
    """).fetchdf()

    # Confidence distribution
    conf_df = con.execute("""
        SELECT confidence_level, COUNT(*) as cnt
        FROM notices WHERE has_iron_age
        GROUP BY confidence_level ORDER BY confidence_level
    """).fetchdf()
    con.close()

    fig_vestiges = px.treemap(
        vestiges_df, path=["vestige"], values="cnt",
        color="cnt", color_continuous_scale="YlOrRd",
        title="Vestiges les plus fréquents (Fer)",
    )
    fig_vestiges.update_layout(
        paper_bgcolor="#0f0f1a", font_color="white",
        margin={"t": 40, "b": 10},
    )

    conf_colors = {"HIGH": "#33A02C", "MEDIUM": "#FF7F00", "LOW": "#E31A1C"}
    fig_conf = px.bar(
        conf_df, x="confidence_level", y="cnt",
        color="confidence_level", color_discrete_map=conf_colors,
        labels={"cnt": "Notices", "confidence_level": "Confiance"},
        title="Niveaux de confiance (Fer)",
    )
    fig_conf.update_layout(
        showlegend=False,
        paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
        font_color="white", margin={"t": 40},
    )

    return kpis, fig_type, fig_communes, fig_vestiges, fig_conf


def _kpi_card(label: str, value: int, color: str) -> dbc.Col:
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.H2(f"{value:,}", className="mb-0", style={"color": color}),
        html.Small(label, className="text-muted"),
    ]), style={"backgroundColor": "#16182d", "border": f"1px solid {color}"}), width=3)
