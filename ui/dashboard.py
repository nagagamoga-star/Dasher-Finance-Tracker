"""Dashboard tab: KPIs and charts."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.chart_theme import apply_plotly_theme
from ui.sidebar import render_export_button, render_filters


def render_dashboard(df: pd.DataFrame, stats: dict) -> None:
    f_df, _, _ = render_filters(df)
    render_export_button(f_df)

    if f_df.empty:
        st.info("No shifts match the current filters. Widen the date range or energy states.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total gross", f"${f_df['Gross'].sum():,.2f}")
    c2.metric("Net profit", f"${f_df['Net_Profit'].sum():,.2f}")
    c3.metric("Distance", f"{f_df['Total_KM'].sum():,.1f} km")
    hours_sum = f_df["Hours"].replace(0, pd.NA).sum()
    avg_net = f_df["Net_Profit"].sum() / hours_sum if hours_sum else 0
    c4.metric("Avg hourly net", f"${avg_net:,.2f}")

    st.markdown("---")

    col_l, col_r = st.columns(2)
    with col_l:
        vibe_df = f_df.groupby("Energy_State", as_index=False)[["Gross", "Net_Profit"]].sum()
        bar_fig = px.bar(
            vibe_df,
            x="Energy_State",
            y=["Gross", "Net_Profit"],
            barmode="group",
            title="Earnings by energy state",
            labels={"value": "AUD", "Energy_State": "Energy state", "variable": "Metric"},
            text_auto=".2s",
        )
        st.plotly_chart(apply_plotly_theme(bar_fig), use_container_width=True)
    with col_r:
        hourly = (
            f_df.groupby("Energy_State")
            .apply(lambda x: x["Net_Profit"].sum() / x["Hours"].replace(0, pd.NA).sum(), include_groups=False)
            .reset_index(name="Hourly_Rate")
        )
        hourly = hourly[np.isfinite(hourly["Hourly_Rate"]) & (hourly["Hourly_Rate"] > 0)]
        if hourly.empty:
            st.caption("Not enough hour data to chart net $/hr by energy state.")
        else:
            pie_fig = px.pie(
                hourly,
                values="Hourly_Rate",
                names="Energy_State",
                title="Net $/hr by energy",
                hole=0.4,
            )
            st.plotly_chart(apply_plotly_theme(pie_fig), use_container_width=True)

    st.subheader("Performance over time")
    daily = (
        f_df.assign(day=f_df["Shift_Date"].dt.normalize())
        .groupby("day", as_index=False)[["Gross", "Net_Profit"]]
        .sum()
        .rename(columns={"day": "Shift_Date"})
    )
    if not daily.empty:
        line_fig = go.Figure()
        line_fig.add_trace(go.Scatter(x=daily["Shift_Date"], y=daily["Gross"], name="Gross", mode="lines+markers"))
        line_fig.add_trace(
            go.Scatter(x=daily["Shift_Date"], y=daily["Net_Profit"], name="Net profit", mode="lines+markers")
        )
        line_fig.update_layout(title="Gross vs net by day", height=320, xaxis_title="Date", yaxis_title="AUD")
        st.plotly_chart(apply_plotly_theme(line_fig), use_container_width=True)

    st.subheader("7-day summary")
    breakdown = stats["daily_breakdown"]
    if breakdown.empty:
        st.caption("No shifts in the last 7 days.")
    else:
        display = breakdown.copy()
        display["Date"] = pd.to_datetime(display["date"]).dt.strftime("%d/%m/%Y")
        display["Gross"] = display["gross"].map("${:,.2f}".format)
        display["Net"] = display["net"].map("${:,.2f}".format)
        st.dataframe(
            display[["Date", "Gross", "Net"]],
            use_container_width=True,
            hide_index=True,
        )

    if st.checkbox("Show raw shift logs"):
        raw = f_df.sort_values("Shift_Date", ascending=False)
        st.dataframe(raw, use_container_width=True, hide_index=True)
