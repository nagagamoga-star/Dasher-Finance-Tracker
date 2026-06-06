"""Cached data loaders for Streamlit."""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from core.logic import load_settings, load_shifts_df, weekly_stats
from core.weather import fetch_current_weather


@st.cache_data(show_spinner=False)
def cached_settings() -> dict:
    return load_settings()


@st.cache_data(show_spinner=False)
def cached_shifts() -> pd.DataFrame:
    return load_shifts_df()


@st.cache_data(show_spinner=False)
def cached_weekly_stats(_shifts_mtime: float) -> dict:
    df = cached_shifts()
    return weekly_stats(df)


@st.cache_data(ttl=900, show_spinner=False)
def cached_weather(latitude: float, longitude: float, timezone: str) -> dict[str, Any] | None:
    return fetch_current_weather(latitude, longitude, timezone=timezone)


def shifts_file_mtime() -> float:
    from core.paths import UNIFIED_LOG_PATH

    if UNIFIED_LOG_PATH.exists():
        return UNIFIED_LOG_PATH.stat().st_mtime
    return 0.0


def clear_caches() -> None:
    cached_settings.clear()
    cached_shifts.clear()
    cached_weekly_stats.clear()
    cached_weather.clear()
