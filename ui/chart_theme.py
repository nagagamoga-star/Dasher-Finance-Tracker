"""Plotly styling aligned with .streamlit/config.toml dark theme."""
from __future__ import annotations

import plotly.graph_objects as go

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#262730",
    font=dict(color="#FAFAFA", size=13),
    title_font=dict(color="#FAFAFA", size=15),
    legend=dict(font=dict(color="#FAFAFA")),
    margin=dict(l=48, r=24, t=48, b=48),
    xaxis=dict(
        gridcolor="#3a3d46",
        zerolinecolor="#3a3d46",
        linecolor="#3a3d46",
        tickfont=dict(color="#C4C7CE"),
        title_font=dict(color="#FAFAFA"),
    ),
    yaxis=dict(
        gridcolor="#3a3d46",
        zerolinecolor="#3a3d46",
        linecolor="#3a3d46",
        tickfont=dict(color="#C4C7CE"),
        title_font=dict(color="#FAFAFA"),
    ),
    colorway=["#00CC96", "#7DD3FC", "#FBBF24", "#F87171"],
)


def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig
