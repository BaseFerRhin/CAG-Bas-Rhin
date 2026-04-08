"""Page: Browse and search commune notices."""

from __future__ import annotations

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from pathlib import Path

from ...storage.queries import get_all_notices

dash.register_page(__name__, path="/notices", name="Notices", title="CAG 67/1 — Notices")

layout = dbc.Row([
    dbc.Col([
        html.H5("Communes", className="text-warning mb-3"),
        dbc.Input(id="notices-search", placeholder="Rechercher...", type="text", className="mb-2"),
        dbc.Switch(id="notices-fer-only", label="Fer uniquement", value=True, className="mb-3"),
        html.Div(id="notices-commune-list", style={"maxHeight": "70vh", "overflowY": "auto"}),
    ], width=3),
    dbc.Col([
        html.Div(id="notices-detail", style={"maxHeight": "85vh", "overflowY": "auto"}),
    ], width=9),
])


@callback(
    Output("notices-commune-list", "children"),
    Input("notices-search", "value"),
    Input("notices-fer-only", "value"),
    State("store-db-path", "data"),
)
def update_commune_list(search: str | None, fer_only: bool, db_path: str) -> list:
    db = Path(db_path)
    if not db.exists():
        return [html.P("Base non trouvée. Lancez l'extraction.", className="text-danger")]

    notices = get_all_notices(db, iron_age_only=fer_only)

    communes: dict[str, dict] = {}
    for n in notices:
        cid = n["commune_id"]
        if cid not in communes:
            communes[cid] = {"name": n.get("commune", ""), "count": 0, "id": cid}
        communes[cid]["count"] += 1

    items = sorted(communes.values(), key=lambda c: c["id"])

    if search:
        search_lower = search.lower()
        items = [c for c in items if search_lower in c["name"].lower() or search_lower in c["id"]]

    children = []
    for c in items:
        children.append(
            dbc.ListGroupItem(
                f"{c['id']} — {c['name']} ({c['count']})",
                id={"type": "commune-item", "index": c["id"]},
                action=True,
                className="py-1 px-2 small",
                style={"backgroundColor": "#16182d", "color": "#e0e0e0", "border": "1px solid #2a2d50"},
            )
        )

    return [
        html.Small(f"{len(items)} communes", className="text-muted d-block mb-2"),
        dbc.ListGroup(children, flush=True),
    ]


@callback(
    Output("notices-detail", "children"),
    Input({"type": "commune-item", "index": dash.ALL}, "n_clicks"),
    State("notices-fer-only", "value"),
    State("store-db-path", "data"),
    prevent_initial_call=True,
)
def show_notice_detail(clicks: list, fer_only: bool, db_path: str) -> list:
    ctx = dash.callback_context
    if not ctx.triggered:
        return [html.P("Sélectionnez une commune.", className="text-muted")]

    triggered_id = ctx.triggered_id
    if not triggered_id or not isinstance(triggered_id, dict):
        return [html.P("Sélectionnez une commune.", className="text-muted")]

    commune_id = triggered_id["index"]
    db = Path(db_path)
    notices = get_all_notices(db, iron_age_only=fer_only)
    commune_notices = [n for n in notices if n.get("commune_id") == commune_id]

    if not commune_notices:
        return [html.P(f"Aucune notice pour {commune_id}.", className="text-muted")]

    commune_name = commune_notices[0].get("commune", "")
    children = [
        html.H4(f"{commune_id} — {commune_name}", className="text-warning mb-3"),
        html.P(f"{len(commune_notices)} notices", className="text-muted"),
        html.Hr(),
    ]

    for n in commune_notices:
        code = n.get("sous_notice_code", "")
        lieu = n.get("lieu_dit") or ""
        type_site = n.get("type_site", "indéterminé")
        text = n.get("full_text") or n.get("raw_text", "")
        page = n.get("page_number", "?")
        is_fer = n.get("has_iron_age", False)

        badge_color = "danger" if is_fer else "secondary"
        badge_text = "Fer" if is_fer else "Autre"

        header_parts = []
        if code:
            header_parts.append(f"({code})")
        if lieu:
            header_parts.append(lieu)
        header = " ".join(header_parts) or "Notice"

        children.append(dbc.Card(dbc.CardBody([
            html.Div([
                html.H6(header, className="d-inline me-2"),
                html.Span(type_site, className="badge bg-info me-1"),
                html.Span(badge_text, className=f"badge bg-{badge_color} me-1"),
                html.Span(f"p.{page}", className="badge bg-dark"),
            ]),
            html.P(text[:800], className="small text-light mt-2 mb-0",
                   style={"whiteSpace": "pre-wrap", "lineHeight": "1.4"}),
        ]), className="mb-2", style={"backgroundColor": "#16182d", "border": "1px solid #2a2d50"}))

    return children
