"""Live clock and weather widgets for Streamlit sidebar."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import streamlit as st

from core.weather import DEFAULT_TIMEZONE, delivery_weather_hint, location_from_settings
from ui.cache import cached_weather


def _safe_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def _weather_compact(settings: dict[str, Any]) -> tuple[str, str, str | None]:
    """Return (primary line, caption line, delivery hint)."""
    loc = location_from_settings(settings)
    weather = cached_weather(loc["latitude"], loc["longitude"], loc["timezone"])
    hint = delivery_weather_hint(weather)

    if weather is None:
        return "—", f"Weather unavailable · {loc['city']}", hint

    temp = weather.get("temperature_c")
    temp_s = f"{temp:.0f}°C" if temp is not None else "—"
    primary = f"{weather['icon']} {temp_s}"
    caption = f"{loc['city']} · {weather['label']}"
    return primary, caption, hint


@st.fragment(run_every=timedelta(seconds=1))
def _sidebar_live_strip(timezone: str, settings: dict[str, Any]) -> None:
    now = datetime.now(_safe_zone(timezone))
    st.markdown(f"## {now.strftime('%A, %d %B %Y')}")

    time_col, weather_col = st.columns(2, gap="small")
    weather_primary, weather_caption, hint = _weather_compact(settings)

    with time_col:
        st.markdown(f"**{now.strftime('%H:%M:%S')}**")
        st.caption(now.strftime("%Z"))

    with weather_col:
        st.markdown(f"**{weather_primary}**")
        st.caption(weather_caption)

    if hint:
        st.info(hint)


def render_sidebar_live(settings: dict[str, Any]) -> None:
    """Sidebar date, clock, and weather in one row."""
    loc = location_from_settings(settings)
    with st.sidebar:
        _sidebar_live_strip(loc["timezone"], settings)
    st.sidebar.markdown("---")
