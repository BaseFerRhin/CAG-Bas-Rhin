"""Dash application factory for CAG 67/1 explorer."""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/cag67.duckdb")


def _is_nan(v) -> bool:
    try:
        import math
        return v is None or (isinstance(v, float) and math.isnan(v))
    except (TypeError, ValueError):
        return False


def _safe_str(v, default: str = "") -> str:
    if v is None or _is_nan(v):
        return default
    return str(v)


def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.DARKLY,
            "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        ],
        suppress_callback_exceptions=True,
        title="CAG 67/1 — Bas-Rhin",
        assets_folder=str(Path(__file__).parent / "assets"),
    )

    app.layout = _build_layout()
    _register_callbacks(app)
    return app


# ── Layout ───────────────────────────────────────────────────────────────

def _build_layout() -> html.Div:
    navbar = dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("CAG 67/1 — Carte Archéologique du Bas-Rhin",
                            className="fw-bold", style={"fontFamily": "Inter, sans-serif"}),
            dbc.Nav([
                dbc.NavLink("Carte", id="nav-carte", href="#", active=True, className="me-2"),
                dbc.NavLink("Notices", id="nav-notices", href="#", className="me-2"),
                dbc.NavLink("Chronologie", id="nav-chrono", href="#", className="me-2"),
                dbc.NavLink("Statistiques", id="nav-stats", href="#"),
            ], navbar=True),
        ], fluid=True),
        color="dark", dark=True, sticky="top",
        style={"borderBottom": "3px solid #D95F02"},
    )

    return html.Div([
        dcc.Store(id="current-page", data="carte"),
        navbar,
        dbc.Container(id="page-content", fluid=True, className="py-3"),
    ], style={"backgroundColor": "#0f0f1a", "minHeight": "100vh", "fontFamily": "Inter, sans-serif"})


# ── Pages ────────────────────────────────────────────────────────────────

_TYPE_COLORS = {
    "nécropole": "#6A3D9A", "habitat": "#1F78B4", "oppidum": "#E31A1C",
    "tumulus": "#FB9A99", "sépulture": "#CAB2D6", "sanctuaire": "#33A02C",
    "dépôt": "#FF7F00", "atelier": "#B15928", "indéterminé": "#B2DF8A",
}

_PERIOD_COLORS = {
    "Hallstatt": "#D95F02", "La Tène": "#1B9E77", "Âge du Fer": "#E6550D",
    "Gallo-romain": "#7570B3", "Néolithique": "#A6761D", "Âge du Bronze": "#E6AB02",
    "Mérovingien": "#66A61E", "Médiéval": "#E7298A", "Carolingien": "#A6CEE3",
    "BF III": "#FDBF6F", "Mésolithique": "#B2DF8A", "Paléolithique": "#CAB2D6",
    "Ha C": "#FD8D3C", "Ha D": "#E6550D", "Ha D1": "#D94701", "Ha D2": "#A63603",
    "Ha D3": "#7F2704", "LT A": "#BAE4B3", "LT B": "#74C476", "LT C": "#31A354", "LT D": "#006D2C",
}


def _page_carte():
    return dbc.Row([
        dbc.Col([
            html.H5("Filtres", className="text-warning mb-3"),
            dbc.Label("Notices minimum"),
            dcc.Slider(id="carte-min-notices", min=1, max=20, step=1, value=1,
                       marks={1: "1", 5: "5", 10: "10", 20: "20"}),
            dbc.Switch(id="carte-fer-only", label="Fer uniquement", value=True, className="mt-3 mb-3"),
            html.Hr(),
            html.Div(id="carte-detail-panel"),
        ], width=3, style={"maxHeight": "85vh", "overflowY": "auto"}),
        dbc.Col([dcc.Graph(id="carte-map", style={"height": "85vh"})], width=9),
    ])


def _page_notices():
    return dbc.Row([
        dbc.Col([
            html.H5("Communes", className="text-warning mb-3"),
            dbc.Input(id="notices-search", placeholder="Rechercher...", type="text", className="mb-2"),
            dbc.Switch(id="notices-fer-only", label="Fer uniquement", value=True, className="mb-3"),
            html.Div(id="notices-commune-list", style={"maxHeight": "70vh", "overflowY": "auto"}),
        ], width=3),
        dbc.Col([html.Div(id="notices-detail", style={"maxHeight": "85vh", "overflowY": "auto"})], width=9),
    ])


def _page_chronologie():
    return html.Div([
        dbc.Row([dbc.Col([
            html.H4("Frise chronologique — CAG 67/1", className="text-warning mb-4"),
            dcc.Graph(id="chrono-bar-all", style={"height": "350px"}),
        ], width=12)]),
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


def _page_stats():
    return html.Div([
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


def _kpi_card(label: str, value: int, color: str) -> dbc.Col:
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.H2(f"{value:,}", className="mb-0", style={"color": color}),
        html.Small(label, className="text-muted"),
    ]), style={"backgroundColor": "#16182d", "border": f"1px solid {color}"}), width=3)


def _empty_map():
    fig = px.scatter_map(
        pd.DataFrame({"lat": [48.6], "lon": [7.75]}),
        lat="lat", lon="lon", zoom=8, map_style="carto-darkmatter",
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, paper_bgcolor="#0f0f1a")
    return fig


# ── Callbacks ────────────────────────────────────────────────────────────

def _register_callbacks(app: dash.Dash) -> None:
    import duckdb

    @app.callback(
        Output("page-content", "children"),
        Output("nav-carte", "active"), Output("nav-notices", "active"),
        Output("nav-chrono", "active"), Output("nav-stats", "active"),
        Input("nav-carte", "n_clicks"), Input("nav-notices", "n_clicks"),
        Input("nav-chrono", "n_clicks"), Input("nav-stats", "n_clicks"),
        prevent_initial_call=False,
    )
    def navigate(c1, c2, c3, c4):
        ctx = dash.callback_context
        tid = ctx.triggered_id if ctx.triggered_id else "nav-carte"
        pages = {
            "nav-carte": (_page_carte(), True, False, False, False),
            "nav-notices": (_page_notices(), False, True, False, False),
            "nav-chrono": (_page_chronologie(), False, False, True, False),
            "nav-stats": (_page_stats(), False, False, False, True),
        }
        return pages.get(tid, pages["nav-carte"])

    # ── Carte ──

    @app.callback(Output("carte-map", "figure"),
                  Input("carte-min-notices", "value"), Input("carte-fer-only", "value"))
    def update_map(min_notices, fer_only):
        from src.storage.queries import get_commune_stats
        if not DB_PATH.exists():
            return _empty_map()
        stats = get_commune_stats(DB_PATH)
        df = pd.DataFrame(stats)
        if df.empty or "latitude" not in df.columns:
            return _empty_map()
        df = df.dropna(subset=["latitude", "longitude"])
        col = "fer_notices" if fer_only else "total_notices"
        df = df[df[col] >= (min_notices or 1)]
        if df.empty:
            return _empty_map()
        fig = px.scatter_map(
            df, lat="latitude", lon="longitude", size=col, color=col,
            color_continuous_scale="YlOrRd", hover_name="commune_name",
            hover_data={"commune_id": True, "fer_notices": True, "total_notices": True,
                        "latitude": False, "longitude": False},
            zoom=8.5, center={"lat": 48.6, "lon": 7.75},
            map_style="carto-darkmatter", size_max=20,
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                          paper_bgcolor="#0f0f1a", plot_bgcolor="#0f0f1a", font_color="white")
        return fig

    @app.callback(Output("carte-detail-panel", "children"),
                  Input("carte-map", "clickData"))
    def carte_detail(click_data):
        if not click_data:
            return [html.P("Cliquez sur une commune.", className="text-muted")]
        from src.storage.queries import get_all_notices
        point = click_data["points"][0]
        commune_name = point.get("hovertext", "")
        commune_id = point.get("customdata", [None])[0]
        if not commune_id:
            return [html.P("Commune non identifiée.", className="text-muted")]
        notices = get_all_notices(DB_PATH, iron_age_only=True)
        cn = [n for n in notices if n.get("commune_id") == commune_id]
        children = [html.H5(f"{commune_id} — {commune_name}", className="text-warning"),
                    html.P(f"{len(cn)} notices Fer", className="text-muted"), html.Hr()]
        for n in cn[:15]:
            code = _safe_str(n.get("sous_notice_code"))
            lieu = _safe_str(n.get("lieu_dit"))
            label = f"({code}) {lieu}" if code else lieu or "Notice"
            children.append(dbc.Card(dbc.CardBody([
                html.H6(label, className="text-info mb-1"),
                html.Small(_safe_str(n.get("type_site")), className="badge bg-secondary me-1"),
                html.P(_safe_str(n.get("raw_text"))[:200] + "...", className="small text-light mt-1 mb-0"),
            ]), className="mb-2", style={"backgroundColor": "#16182d"}))
        return children

    # ── Notices ──

    @app.callback(Output("notices-commune-list", "children"),
                  Input("notices-search", "value"), Input("notices-fer-only", "value"))
    def update_commune_list(search, fer_only):
        from src.storage.queries import get_all_notices
        if not DB_PATH.exists():
            return [html.P("Base non trouvée.", className="text-danger")]
        notices = get_all_notices(DB_PATH, iron_age_only=fer_only)
        communes: dict[str, dict] = {}
        for n in notices:
            cid = n["commune_id"]
            if cid not in communes:
                communes[cid] = {"name": n.get("commune", ""), "count": 0, "id": cid}
            communes[cid]["count"] += 1
        items = sorted(communes.values(), key=lambda c: c["id"])
        if search:
            sl = search.lower()
            items = [c for c in items if sl in c["name"].lower() or sl in c["id"]]
        children = []
        for c in items:
            children.append(dbc.ListGroupItem(
                f"{c['id']} — {c['name']} ({c['count']})",
                id={"type": "commune-item", "index": c["id"]}, action=True, className="py-1 px-2 small",
                style={"backgroundColor": "#16182d", "color": "#e0e0e0", "border": "1px solid #2a2d50"},
            ))
        return [html.Small(f"{len(items)} communes", className="text-muted d-block mb-2"),
                dbc.ListGroup(children, flush=True)]

    @app.callback(Output("notices-detail", "children"),
                  Input({"type": "commune-item", "index": dash.ALL}, "n_clicks"),
                  State("notices-fer-only", "value"), prevent_initial_call=True)
    def show_notice_detail(clicks, fer_only):
        from src.storage.queries import get_all_notices
        ctx = dash.callback_context
        if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
            return [html.P("Sélectionnez une commune.", className="text-muted")]
        commune_id = ctx.triggered_id["index"]
        notices = get_all_notices(DB_PATH, iron_age_only=fer_only)
        cn = [n for n in notices if n.get("commune_id") == commune_id]
        if not cn:
            return [html.P(f"Aucune notice pour {commune_id}.", className="text-muted")]
        commune_name = cn[0].get("commune", "")
        children = [html.H4(f"{commune_id} — {commune_name}", className="text-warning mb-3"),
                    html.P(f"{len(cn)} notices", className="text-muted"), html.Hr()]
        for n in cn:
            code = n.get("sous_notice_code", "")
            lieu = _safe_str(n.get("lieu_dit"))
            type_site = _safe_str(n.get("type_site"), "indéterminé")
            text = _safe_str(n.get("full_text")) or _safe_str(n.get("raw_text"))
            page = n.get("page_number", "?")
            is_fer = n.get("has_iron_age", False)
            conf = _safe_str(n.get("confidence_level"), "LOW")
            header = " ".join(filter(None, [f"({code})" if code else "", lieu])) or "Notice"
            conf_c = {"HIGH": "success", "MEDIUM": "warning", "LOW": "secondary"}
            children.append(dbc.Card(dbc.CardBody([
                html.Div([
                    html.H6(header, className="d-inline me-2"),
                    html.Span(type_site, className="badge bg-info me-1"),
                    html.Span("Fer" if is_fer else "Autre", className=f"badge bg-{'danger' if is_fer else 'secondary'} me-1"),
                    html.Span(conf, className=f"badge bg-{conf_c.get(conf, 'secondary')} me-1"),
                    html.Span(f"p.{page}", className="badge bg-dark"),
                ]),
                html.P(text[:800], className="small text-light mt-2 mb-0",
                       style={"whiteSpace": "pre-wrap", "lineHeight": "1.4"}),
            ]), className="mb-2", style={"backgroundColor": "#16182d", "border": "1px solid #2a2d50"}))
        return children

    # ── Chronologie ──

    @app.callback(Output("chrono-bar-all", "figure"), Output("chrono-bar-fer", "figure"),
                  Output("chrono-heatmap", "figure"), Input("current-page", "data"))
    def update_chronology(_):
        if not DB_PATH.exists():
            empty = px.bar(title="Base non trouvée")
            return empty, empty, empty
        con = duckdb.connect(str(DB_PATH), read_only=True)
        all_p = con.execute(
            "SELECT periode_norm as periode, COUNT(DISTINCT notice_id) as cnt "
            "FROM periodes WHERE periode_norm IS NOT NULL GROUP BY periode_norm ORDER BY cnt DESC"
        ).fetchdf()
        fer_sub = con.execute(
            "SELECT periode_norm as periode, COUNT(DISTINCT notice_id) as cnt FROM periodes "
            "WHERE periode_norm IN ('Ha A','Ha B','Ha C','Ha D','Ha D1','Ha D2','Ha D3',"
            "'LT A','LT B','LT C','LT D','BF III') GROUP BY periode_norm ORDER BY cnt DESC"
        ).fetchdf()
        cooc = con.execute("SELECT * FROM v_period_cooccurrence LIMIT 100").fetchdf()
        con.close()

        fig_all = px.bar(all_p, x="cnt", y="periode", orientation="h",
                         color="periode", color_discrete_map=_PERIOD_COLORS,
                         labels={"cnt": "Notices", "periode": "Période"})
        fig_all.update_layout(showlegend=False, paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
                              font_color="white", margin={"l": 150})

        fig_fer = px.bar(fer_sub, x="cnt", y="periode", orientation="h",
                         color="periode", color_discrete_map=_PERIOD_COLORS,
                         labels={"cnt": "Notices", "periode": ""})
        fig_fer.update_layout(showlegend=False, paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
                              font_color="white", margin={"l": 80})

        if not cooc.empty:
            all_per = sorted(set(cooc["period_a"].tolist() + cooc["period_b"].tolist()))
            matrix = pd.DataFrame(0, index=all_per, columns=all_per)
            for _, row in cooc.iterrows():
                matrix.loc[row["period_a"], row["period_b"]] = row["co_count"]
                matrix.loc[row["period_b"], row["period_a"]] = row["co_count"]
            fig_heat = go.Figure(data=go.Heatmap(
                z=matrix.values, x=matrix.columns.tolist(), y=matrix.index.tolist(),
                colorscale="YlOrRd", showscale=True))
        else:
            fig_heat = go.Figure(data=go.Heatmap(z=[[0]], x=["—"], y=["—"], colorscale="YlOrRd"))
        fig_heat.update_layout(paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
                               font_color="white", margin={"l": 80, "t": 20, "r": 20})
        return fig_all, fig_fer, fig_heat

    # ── Stats ──

    @app.callback(Output("stats-kpis", "children"), Output("stats-type-donut", "figure"),
                  Output("stats-top-communes", "figure"), Output("stats-vestiges-treemap", "figure"),
                  Output("stats-confidence", "figure"), Input("current-page", "data"))
    def update_stats(_):
        from src.storage.queries import get_summary_stats, get_commune_stats
        if not DB_PATH.exists():
            empty = px.bar(title="Base non trouvée")
            return [], empty, empty, empty, empty
        s = get_summary_stats(DB_PATH)

        kpis = dbc.Row([
            _kpi_card("Communes", s["communes"], "#1F78B4"),
            _kpi_card("Notices", s["notices"], "#6A3D9A"),
            _kpi_card("Notices Fer", s["fer_notices"], "#D95F02"),
            _kpi_card("Figures", s["figures"], "#33A02C"),
        ])

        type_df = pd.DataFrame(s["by_type"], columns=["type_site", "count"])
        fig_type = px.pie(type_df, values="count", names="type_site", color="type_site",
                          color_discrete_map=_TYPE_COLORS, hole=0.4)
        fig_type.update_layout(paper_bgcolor="#0f0f1a", font_color="white",
                               legend=dict(font=dict(size=11)), margin={"t": 30, "b": 10},
                               title="Types de sites (Fer)")

        cs = get_commune_stats(DB_PATH)
        top = pd.DataFrame(cs).nlargest(20, "fer_notices")
        fig_communes = px.bar(top, x="fer_notices", y="commune_name", orientation="h",
                              color_discrete_sequence=["#D95F02"],
                              labels={"fer_notices": "Notices Fer", "commune_name": ""},
                              title="Top 20 communes (notices Fer)")
        fig_communes.update_layout(paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
                                   font_color="white", margin={"l": 150},
                                   yaxis={"categoryorder": "total ascending"})

        con = duckdb.connect(str(DB_PATH), read_only=True)
        vestiges_df = con.execute(
            "SELECT v.vestige, COUNT(*) as cnt FROM vestiges v JOIN notices n ON v.notice_id = n.notice_id "
            "WHERE n.has_iron_age GROUP BY v.vestige ORDER BY cnt DESC LIMIT 30"
        ).fetchdf()
        conf_df = con.execute(
            "SELECT confidence_level, COUNT(*) as cnt FROM notices WHERE has_iron_age "
            "GROUP BY confidence_level ORDER BY confidence_level"
        ).fetchdf()
        con.close()

        fig_vestiges = px.treemap(vestiges_df, path=["vestige"], values="cnt",
                                  color="cnt", color_continuous_scale="YlOrRd",
                                  title="Vestiges les plus fréquents (Fer)")
        fig_vestiges.update_layout(paper_bgcolor="#0f0f1a", font_color="white", margin={"t": 40, "b": 10})

        conf_colors = {"HIGH": "#33A02C", "MEDIUM": "#FF7F00", "LOW": "#E31A1C"}
        fig_conf = px.bar(conf_df, x="confidence_level", y="cnt", color="confidence_level",
                          color_discrete_map=conf_colors,
                          labels={"cnt": "Notices", "confidence_level": "Confiance"},
                          title="Niveaux de confiance (Fer)")
        fig_conf.update_layout(showlegend=False, paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
                               font_color="white", margin={"t": 40})

        return kpis, fig_type, fig_communes, fig_vestiges, fig_conf
