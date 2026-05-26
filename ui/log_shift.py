"""Log shift tab."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import streamlit as st

from core.logic import ENERGY_STATES, append_shift, compute_shift
from core.shift_time import ends_on_later_day_default, format_shift_span, resolve_shift_span
from core.validation import ValidationError
from ui.cache import clear_caches


def render_log_shift(settings: dict) -> None:
    st.subheader("Log a new shift")
    st.caption("For shifts after midnight: set **start date** to when you began, then enable **ends on a later day**.")
    last_odo = float(settings.get("last_odo_reading", 0))

    with st.form("log_shift_form"):
        shift_date = st.date_input("Start date", value=date.today())
        t1, t2 = st.columns(2)
        with t1:
            start_t = st.time_input("Start", value=time(8, 0))
        with t2:
            end_t = st.time_input("End", value=time(14, 0))

        start_str = start_t.strftime("%H:%M")
        end_str = end_t.strftime("%H:%M")
        default_later = ends_on_later_day_default(start_str, end_str)

        ends_later = st.checkbox(
            "Shift ends on a later calendar day (crosses midnight)",
            value=default_later,
        )
        end_shift_date = shift_date
        if ends_later:
            end_shift_date = st.date_input(
                "End date (finish day)",
                value=shift_date + timedelta(days=1),
                min_value=shift_date,
            )

        gross = st.number_input("Gross earnings (AUD)", min_value=0.0, step=0.01, format="%.2f")
        end_odo = st.number_input(
            f"End odometer (last: {last_odo:.0f} km)",
            min_value=0.0,
            value=last_odo,
            step=0.1,
        )
        energy = st.selectbox("Energy state", ENERGY_STATES, index=1)
        allow_odo_reset = st.checkbox("Odometer reset (allow lower reading)")
        confirm_long = st.checkbox("Confirm shift over 500 km")
        submitted = st.form_submit_button("Preview & save", type="primary")

    if not submitted:
        return

    start_dt = datetime.combine(shift_date, datetime.min.time())
    end_dt = datetime.combine(end_shift_date, datetime.min.time()) if ends_later else None
    ends_flag = ends_later if ends_later else False

    try:
        _, _, hours, start_str, end_str, shift_str, end_str_date = resolve_shift_span(
            start_dt,
            start_str,
            end_str,
            end_date=end_dt,
            ends_next_day=ends_flag if ends_later else None,
        )
        span = format_shift_span(shift_str, start_str, end_str_date, end_str)
        dist = max(0.0, end_odo - last_odo) if end_odo >= last_odo else 0.0
        preview = compute_shift(settings, gross, dist, hours)

        st.markdown("**Preview**")
        st.caption(span)
        p1, p2, p3 = st.columns(3)
        p1.metric("Gross / hr", f"${preview['hourly_gross']:.2f}")
        p2.metric("Net / hr", f"${preview['hourly_net']:.2f}")
        p3.metric("Net profit", f"${preview['net']:.2f}")
        st.caption(
            f"{dist:.1f} km · {hours}h · Fuel {preview['fuel_used']:.2f}L (${preview['fuel_cost']:.2f}) · "
            f"Tax buffer ${preview['tax']:.2f}"
        )

        if dist > 500 and not confirm_long:
            st.error(f"{dist:.0f} km is a long shift — tick the confirmation box to save.")
            return

        append_shift(
            settings,
            shift_date=start_dt,
            start_time=start_str,
            end_time=end_str,
            gross=gross,
            end_odo=end_odo,
            energy_state=energy,
            allow_odo_decrease=allow_odo_reset,
            end_date=end_dt if ends_later else None,
            ends_next_day=ends_flag if ends_later else None,
        )
        clear_caches()
        st.success(f"Saved · {span} · Net ${preview['net']:.2f}")
        st.rerun()
    except (ValidationError, ValueError) as e:
        st.error(str(e))
