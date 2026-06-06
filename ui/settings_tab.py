"""Settings tab: vehicle and financial config."""
from __future__ import annotations

import shutil

import streamlit as st

from core.logic import save_settings, settings_from_form
from core.paths import CONFIG_EXAMPLE_PATH, CONFIG_PATH
from core.validation import ValidationError
from core.weather import DEFAULT_CITY, DEFAULT_TIMEZONE, geocode_city, location_from_settings
from ui.cache import clear_caches


def render_settings(settings: dict) -> None:
    st.subheader("Settings")
    vehicle = settings["vehicle"]
    financials = settings["financials"]
    loc = location_from_settings(settings)

    if "geo_lookup" in st.session_state:
        hit = st.session_state.pop("geo_lookup")
        loc = {**loc, **hit}

    with st.expander("Location (weather & local time)", expanded=False):
        st.caption("Used for the live clock and weather widgets on the dashboard.")
        geo_col1, geo_col2 = st.columns([3, 1])
        with geo_col1:
            city_input = st.text_input("City", value=loc["city"], key="settings_city")
        with geo_col2:
            st.write("")
            st.write("")
            if st.button("Look up", use_container_width=True):
                hit = geocode_city(city_input)
                if hit:
                    st.session_state["geo_lookup"] = hit
                    st.rerun()
                else:
                    st.warning("City not found — try another name or enter coordinates below.")

        loc_col1, loc_col2 = st.columns(2)
        with loc_col1:
            lat_input = st.number_input("Latitude", value=float(loc["latitude"]), format="%.4f", step=0.0001)
        with loc_col2:
            lon_input = st.number_input("Longitude", value=float(loc["longitude"]), format="%.4f", step=0.0001)
        tz_input = st.text_input("Timezone", value=loc["timezone"], help="e.g. Australia/Brisbane")

    with st.form("settings_form"):
        model = st.text_input("Vehicle", value=vehicle.get("model", ""))
        c1, c2 = st.columns(2)
        with c1:
            tank = st.number_input("Tank capacity (L)", min_value=1.0, value=float(vehicle["tank_capacity"]), step=0.5)
            consumption = st.number_input(
                "Fuel consumption (L/100km)",
                min_value=0.1,
                value=float(vehicle["fuel_consumption_l_100km"]),
                step=0.1,
            )
        with c2:
            tax_pct = st.number_input(
                "Tax buffer (decimal, e.g. 0.10 = 10%)",
                min_value=0.0,
                max_value=1.0,
                value=float(financials["tax_buffer_pct"]),
                step=0.01,
                format="%.2f",
            )
            ato_rate = st.number_input(
                "ATO km rate (AUD/km)",
                min_value=0.01,
                value=float(financials.get("ato_km_rate", 0.88)),
                step=0.01,
                format="%.2f",
            )
        target = st.number_input(
            "Daily gross target (AUD)",
            min_value=0.0,
            value=float(settings.get("daily_target", 150)),
            step=5.0,
        )

        st.caption("Live values (odo / fuel) update when you log shifts or refuel.")
        live1, live2 = st.columns(2)
        live1.metric("Odometer", f"{settings.get('last_odo_reading', 0):,.0f} km")
        live2.metric("Fuel in tank", f"{settings.get('current_fuel_litres', 0):.1f} L")

        if st.form_submit_button("Save settings", type="primary"):
            try:
                updated = settings_from_form(
                    model=model,
                    tank_capacity=tank,
                    fuel_consumption=consumption,
                    tax_buffer_pct=tax_pct,
                    ato_km_rate=ato_rate,
                    daily_target=target,
                    current=settings,
                )
                updated["location"] = {
                    "city": city_input.strip() or DEFAULT_CITY,
                    "latitude": float(lat_input),
                    "longitude": float(lon_input),
                    "timezone": tz_input.strip() or DEFAULT_TIMEZONE,
                }
                save_settings(updated)
                clear_caches()
                st.success("Settings saved.")
                st.rerun()
            except ValidationError as e:
                st.error(str(e))

    if not CONFIG_PATH.exists() and CONFIG_EXAMPLE_PATH.exists():
        st.warning("No `config/settings.json` found.")
        if st.button("Create settings from example"):
            shutil.copy(CONFIG_EXAMPLE_PATH, CONFIG_PATH)
            clear_caches()
            st.rerun()
