"""Reusable map component for commune visualization."""

from __future__ import annotations

import plotly.express as px
import pandas as pd

TYPE_COLORS = {
    "nécropole": "#6A3D9A", "habitat": "#1F78B4", "oppidum": "#E31A1C",
    "tumulus": "#FB9A99", "sépulture": "#CAB2D6", "sanctuaire": "#33A02C",
    "dépôt": "#FF7F00", "atelier": "#B15928", "indéterminé": "#B2DF8A",
}

MAP_CENTER = {"lat": 48.6, "lon": 7.75}
MAP_ZOOM = 8.5
MAP_STYLE = "carto-darkmatter"


def create_commune_map(df: pd.DataFrame, *, size_col: str = "fer_notices") -> dict:
    """Create a Scattermapbox figure from commune stats DataFrame."""
    if df.empty or "latitude" not in df.columns:
        return empty_map()

    df = df.dropna(subset=["latitude", "longitude"])
    df = df[df[size_col] > 0]

    if df.empty:
        return empty_map()

    fig = px.scatter_mapbox(
        df,
        lat="latitude", lon="longitude",
        size=size_col, color=size_col,
        color_continuous_scale="YlOrRd",
        hover_name="commune_name",
        hover_data={"commune_id": True, "fer_notices": True, "total_notices": True,
                     "latitude": False, "longitude": False},
        zoom=MAP_ZOOM, center=MAP_CENTER,
        mapbox_style=MAP_STYLE, size_max=20,
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="#0f0f1a", plot_bgcolor="#0f0f1a",
        font_color="white",
    )
    return fig


def empty_map() -> dict:
    fig = px.scatter_mapbox(
        pd.DataFrame({"lat": [MAP_CENTER["lat"]], "lon": [MAP_CENTER["lon"]]}),
        lat="lat", lon="lon", zoom=MAP_ZOOM - 1, mapbox_style=MAP_STYLE,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, paper_bgcolor="#0f0f1a")
    return fig
