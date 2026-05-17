"""Refuel tab."""
from __future__ import annotations

import streamlit as st

from core.logic import apply_refill, km_left_on_fuel
from core.validation import ValidationError
from ui.cache import clear_caches


def render_refuel(settings: dict) -> None:
    st.subheader("Refuel")
    tank = float(settings["vehicle"]["tank_capacity"])
    current = float(settings.get("current_fuel_litres", 0))
    st.caption(f"Tank: {current:.1f}L / {tank:.0f}L · ~{km_left_on_fuel(settings):.0f} km range")

    with st.form("refuel_form"):
        litres = st.number_input("Litres added", min_value=0.0, step=0.1, format="%.1f")
        price = st.number_input(
            "Price per litre (AUD)",
            min_value=0.0,
            value=float(settings.get("last_fuel_price", 1.9)),
            step=0.01,
            format="%.2f",
        )
        if st.form_submit_button("Save refill", type="primary"):
            try:
                result = apply_refill(settings, litres, price)
                clear_caches()
                if result["capped"]:
                    st.warning("Fill capped at tank capacity.")
                st.success(
                    f"Added {litres:.1f}L @ ${price:.2f}/L = ${result['total_cost']:.2f} · "
                    f"Tank {result['new_level']:.1f}L · ~{result['km_range']:.0f} km range"
                )
                st.rerun()
            except ValidationError as e:
                st.error(str(e))
