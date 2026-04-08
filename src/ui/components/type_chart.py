"""Reusable site-type chart components."""

from __future__ import annotations

import plotly.express as px
import pandas as pd

TYPE_COLORS = {
    "nécropole": "#6A3D9A", "habitat": "#1F78B4", "oppidum": "#E31A1C",
    "tumulus": "#FB9A99", "sépulture": "#CAB2D6", "sanctuaire": "#33A02C",
    "dépôt": "#FF7F00", "atelier": "#B15928", "indéterminé": "#B2DF8A",
}


def create_type_donut(df: pd.DataFrame) -> dict:
    """Donut chart of site type distribution."""
    fig = px.pie(
        df, values="count", names="type_site",
        color="type_site", color_discrete_map=TYPE_COLORS,
        hole=0.4,
    )
    fig.update_layout(
        paper_bgcolor="#0f0f1a", font_color="white",
        legend=dict(font=dict(size=11)),
        margin={"t": 30, "b": 10},
    )
    return fig
