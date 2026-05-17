"""Input validation shared by CLI and Streamlit."""
from __future__ import annotations

import re
from datetime import time

TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


class ValidationError(ValueError):
    """User-facing validation failure."""


def format_time(t: time) -> str:
    return t.strftime("%H:%M")


def parse_time(value: str | time) -> str:
    if isinstance(value, time):
        return format_time(value)
    text = str(value).strip()
    if not TIME_PATTERN.match(text):
        raise ValidationError(f"Invalid time '{text}'. Use HH:MM (24-hour).")
    return text


def validate_refill(litres: float, price_per_litre: float) -> None:
    if litres <= 0:
        raise ValidationError("Litres added must be greater than zero.")
    if price_per_litre <= 0:
        raise ValidationError("Fuel price must be greater than zero.")


def validate_shift_inputs(
    *,
    gross: float,
    end_odo: float,
    last_odo: float,
    start_time: str | time,
    end_time: str | time,
    hours: float,
    energy_state: str,
    energy_states: list[str],
    allow_odo_decrease: bool = False,
) -> tuple[str, str]:
    start = parse_time(start_time)
    end = parse_time(end_time)

    if gross < 0:
        raise ValidationError("Gross earnings cannot be negative.")
    if hours <= 0:
        raise ValidationError("Shift hours must be greater than zero. Check start/end times.")
    if end_odo < 0:
        raise ValidationError("Odometer cannot be negative.")
    if end_odo < last_odo and not allow_odo_decrease:
        raise ValidationError(
            f"End odometer ({end_odo:.0f}) is below last reading ({last_odo:.0f}). "
            "Tick 'Odometer reset' if intentional."
        )
    if energy_state not in energy_states:
        raise ValidationError(f"Energy state must be one of: {', '.join(energy_states)}")

    return start, end


def validate_settings_values(settings: dict) -> None:
    vehicle = settings.get("vehicle", {})
    financials = settings.get("financials", {})

    if float(vehicle.get("tank_capacity", 0)) <= 0:
        raise ValidationError("Tank capacity must be greater than zero.")
    if float(vehicle.get("fuel_consumption_l_100km", 0)) <= 0:
        raise ValidationError("Fuel consumption must be greater than zero.")
    tax = float(financials.get("tax_buffer_pct", -1))
    if not 0 <= tax <= 1:
        raise ValidationError("Tax buffer must be between 0% and 100% (e.g. 0.10 for 10%).")
    if float(financials.get("ato_km_rate", 0)) <= 0:
        raise ValidationError("ATO km rate must be greater than zero.")
    if float(settings.get("daily_target", 0)) < 0:
        raise ValidationError("Daily target cannot be negative.")
