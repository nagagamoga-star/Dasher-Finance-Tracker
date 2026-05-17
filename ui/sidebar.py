"""Sidebar: vehicle status, filters, export."""
from __future__ import annotations

import streamlit as st

from core.logic import daily_target, export_shifts_csv, fuel_level_pct, km_left_on_fuel
from core.version import __version__


def render_sidebar_status(settings: dict, stats: dict) -> None:
    st.sidebar.caption(f"BioDash v{__version__}")
    st.sidebar.header("Vehicle & fuel")
    st.sidebar.metric("Odometer", f"{settings.get('last_odo_reading', 0):,.0f} km")
    fuel_l = float(settings.get("current_fuel_litres", 0))
    tank = float(settings["vehicle"]["tank_capacity"])
    st.sidebar.progress(fuel_level_pct(settings), text=f"{fuel_l:.1f}L / {tank:.0f}L")
    st.sidebar.metric("Km on fuel", f"~{km_left_on_fuel(settings):,.0f} km")
    st.sidebar.metric("Fuel price", f"${settings.get('last_fuel_price', 0):.2f}/L")
    st.sidebar.markdown("---")

    target = daily_target(settings)
    net_delta = stats["weekly_net"] - stats.get("prior_weekly_net", 0)
    st.sidebar.metric(
        "Weekly net",
        f"${stats['weekly_net']:,.2f}",
        delta=f"${net_delta:+,.2f} vs prior week" if stats.get("prior_weekly_net") else None,
    )
    today_pct = min(stats["today_gross"] / target * 100, 100) if target else 0
    st.sidebar.progress(today_pct / 100, text=f"Today ${stats['today_gross']:.0f} / ${target:.0f}")


def render_filters(df) -> tuple:
    """Return (filtered_df, date_range, energy_filter)."""
    st.sidebar.header("Filters")
    if df.empty:
        return df, None, []

    min_d, max_d = df["Shift_Date"].min().date(), df["Shift_Date"].max().date()
    date_range = st.sidebar.date_input("Date range", [min_d, max_d])
    options = sorted(df["Energy_State"].dropna().unique())
    energy_filter = st.sidebar.multiselect("Energy states", options=options, default=list(options))

    if len(date_range) != 2:
        return df.iloc[0:0], date_range, energy_filter

    mask = (
        (df["Shift_Date"].dt.date >= date_range[0])
        & (df["Shift_Date"].dt.date <= date_range[1])
        & (df["Energy_State"].isin(energy_filter))
    )
    return df.loc[mask], date_range, energy_filter


def render_export_button(f_df) -> None:
    if f_df is None or f_df.empty:
        return
    st.sidebar.download_button(
        "Download filtered CSV",
        data=export_shifts_csv(f_df),
        file_name="biodash_shifts_export.csv",
        mime="text/csv",
        use_container_width=True,
    )
