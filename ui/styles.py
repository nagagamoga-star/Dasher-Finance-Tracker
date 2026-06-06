"""Streamlit layout tweaks for mobile-first dashboard."""
from __future__ import annotations

import streamlit as st


def inject_mobile_styles() -> None:
    st.markdown(
        """
        <style>
        /* Tighter metric blocks on narrow viewports */
        @media (max-width: 640px) {
            [data-testid="stMetric"] {
                padding: 0.35rem 0.5rem;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.35rem;
            }
            [data-testid="stTabs"] button {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
        }
        /* Live header card */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
