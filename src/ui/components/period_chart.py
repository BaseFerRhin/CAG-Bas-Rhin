"""Reusable period chart components."""

from __future__ import annotations

import plotly.express as px
import pandas as pd

PERIOD_COLORS = {
    "Hallstatt": "#D95F02", "La Tène": "#1B9E77", "Âge du Fer": "#E6550D",
    "Gallo-romain": "#7570B3", "Néolithique": "#A6761D", "Âge du Bronze": "#E6AB02",
    "Mérovingien": "#66A61E", "Médiéval": "#E7298A",
    "Ha A": "#FDD0A2", "Ha B": "#FDAE6B", "Ha C": "#FD8D3C", "Ha D": "#E6550D",
    "Ha D1": "#D94701", "Ha D2": "#A63603", "Ha D3": "#7F2704",
    "LT A": "#BAE4B3", "LT B": "#74C476", "LT C": "#31A354", "LT D": "#006D2C",
    "BF III": "#FDBF6F",
}


def create_period_bar(df: pd.DataFrame, *, title: str = "") -> dict:
    """Horizontal bar chart of period mention counts."""
    fig = px.bar(
        df, x="cnt", y="periode", orientation="h",
        color="periode", color_discrete_map=PERIOD_COLORS,
        labels={"cnt": "Notices", "periode": ""},
    )
    fig.update_layout(
        showlegend=False, title=title,
        paper_bgcolor="#0f0f1a", plot_bgcolor="#16182d",
        font_color="white", margin={"l": 120},
    )
    return fig
