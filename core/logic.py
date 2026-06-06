"""BioDash business logic: settings, Pandas data loading, profit math."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from core.io import atomic_append_csv_row, atomic_write_json, backup_file
from core.paths import BACKUPS_DIR, CONFIG_EXAMPLE_PATH, CONFIG_PATH, UNIFIED_LOG_PATH
from core.shift_time import format_shift_span, resolve_shift_span
from core.validation import validate_refill, validate_settings_values, validate_shift_inputs

logger = logging.getLogger("biodash")

SHIFT_COLUMNS = [
    "Log_Timestamp",
    "Shift_Date",
    "End_Date",
    "Start_Time",
    "End_Time",
    "Hours",
    "Total_KM",
    "Gross",
    "Actual_Fuel_Cost",
    "ATO_Deduction_Est",
    "Tax_Savings_Buffer",
    "Net_Profit",
    "Hourly_Net",
    "Energy_State",
]

MONEY_COLUMNS = ["Gross", "Net_Profit", "Actual_Fuel_Cost", "ATO_Deduction_Est", "Tax_Savings_Buffer", "Hourly_Net"]
NUMERIC_COLUMNS = ["Hours", "Total_KM"] + MONEY_COLUMNS

DEFAULT_SETTINGS: dict[str, Any] = {
    "current_fuel_litres": 45.0,
    "last_odo_reading": 0.0,
    "last_fuel_price": 1.90,
    "vehicle": {
        "model": "2021 Hyundai Venue",
        "tank_capacity": 45.0,
        "fuel_consumption_l_100km": 7.2,
    },
    "financials": {
        "tax_buffer_pct": 0.10,
        "ato_km_rate": 0.88,
        "currency": "AUD",
    },
    "daily_target": 150.0,
    "location": {
        "city": "Townsville",
        "latitude": -19.2569,
        "longitude": 146.8239,
        "timezone": "Australia/Brisbane",
    },
}

ENERGY_STATES = ["Flow", "Neutral", "Stuck", "Drained"]
_SHIELD_PATTERN = re.compile(r"(Flow|Neutral|Stuck|Drained)(\d{2}/\d{2}/\d{4})")


def repair_csv_shield(raw: str) -> str:
    repaired = _SHIELD_PATTERN.sub(r"\1\n\2", raw)
    if repaired != raw:
        logger.warning("Shield repair applied to merged CSV rows")
    return repaired


def ensure_settings_file() -> bool:
    """Return True if settings exist; False if user must copy example."""
    if CONFIG_PATH.exists():
        return True
    if CONFIG_EXAMPLE_PATH.exists():
        return False
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_settings(DEFAULT_SETTINGS.copy())
    return True


def load_settings() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        if CONFIG_EXAMPLE_PATH.exists():
            raise FileNotFoundError(
                f"Missing {CONFIG_PATH.name}. Copy config/settings.example.json to config/settings.json"
            )
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()

    with open(CONFIG_PATH, encoding="utf-8") as f:
        current = json.load(f)
    if "vehicle" not in current:
        current["vehicle"] = DEFAULT_SETTINGS["vehicle"].copy()
    if "financials" not in current:
        current["financials"] = DEFAULT_SETTINGS["financials"].copy()
    return current


def save_settings(settings: dict[str, Any]) -> None:
    validate_settings_values(settings)
    backup_file(CONFIG_PATH, BACKUPS_DIR)
    atomic_write_json(CONFIG_PATH, settings)


def settings_from_form(
    *,
    model: str,
    tank_capacity: float,
    fuel_consumption: float,
    tax_buffer_pct: float,
    ato_km_rate: float,
    daily_target: float,
    current: dict[str, Any],
) -> dict[str, Any]:
    updated = json.loads(json.dumps(current))
    updated["vehicle"]["model"] = model.strip() or "Vehicle"
    updated["vehicle"]["tank_capacity"] = float(tank_capacity)
    updated["vehicle"]["fuel_consumption_l_100km"] = float(fuel_consumption)
    updated["financials"]["tax_buffer_pct"] = float(tax_buffer_pct)
    updated["financials"]["ato_km_rate"] = float(ato_km_rate)
    updated["daily_target"] = float(daily_target)
    return updated


def daily_target(settings: dict[str, Any]) -> float:
    return float(settings.get("daily_target", 150.0))


def km_left_on_fuel(settings: dict[str, Any]) -> float:
    litres = float(settings.get("current_fuel_litres", 0))
    consumption = float(settings["vehicle"]["fuel_consumption_l_100km"])
    if consumption <= 0 or litres <= 0:
        return 0.0
    return (litres / consumption) * 100


def fuel_level_pct(settings: dict[str, Any]) -> float:
    tank = float(settings["vehicle"]["tank_capacity"])
    litres = float(settings.get("current_fuel_litres", 0))
    return min(litres / tank, 1.0) if tank > 0 else 0.0


def _clean_money_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("", "0")
        .astype(float)
    )


def load_shifts_df(path: Path | str | None = None) -> pd.DataFrame:
    log_path = Path(path) if path else UNIFIED_LOG_PATH
    if not log_path.exists():
        return pd.DataFrame(columns=SHIFT_COLUMNS)

    raw = log_path.read_text(encoding="utf-8-sig")
    repaired = repair_csv_shield(raw)
    df = pd.read_csv(StringIO(repaired), encoding="utf-8-sig")

    for col in MONEY_COLUMNS:
        if col in df.columns:
            df[col] = _clean_money_series(df[col])
    for col in NUMERIC_COLUMNS:
        if col in df.columns and col not in MONEY_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "Shift_Date" in df.columns:
        df["Shift_Date"] = pd.to_datetime(df["Shift_Date"], dayfirst=True, errors="coerce")
    if "End_Date" not in df.columns:
        df["End_Date"] = df["Shift_Date"]
    else:
        df["End_Date"] = pd.to_datetime(df["End_Date"], dayfirst=True, errors="coerce")
        df["End_Date"] = df["End_Date"].fillna(df["Shift_Date"])

    return df.dropna(subset=["Shift_Date"])


def gross_for_date(df: pd.DataFrame, day: datetime) -> float:
    """Total gross already logged on a given calendar day (by shift start date)."""
    if df.empty or "Shift_Date" not in df.columns:
        return 0.0
    day_norm = pd.Timestamp(day).normalize()
    mask = df["Shift_Date"].dt.normalize() == day_norm
    return float(df.loc[mask, "Gross"].sum())


def is_backfill_shift(df: pd.DataFrame, shift_date: datetime) -> bool:
    """True when logging a shift earlier than the newest shift already on file."""
    if df.empty or "Shift_Date" not in df.columns:
        return False
    day = pd.Timestamp(shift_date).normalize()
    latest = df["Shift_Date"].max()
    if pd.isna(latest):
        return False
    return day < pd.Timestamp(latest).normalize()


def infer_shift_start_odo(df: pd.DataFrame, settings: dict[str, Any], shift_date: datetime) -> float:
    """
    Estimate odometer at shift start when backfilling out-of-order days.

    Uses the saved reading minus km from this day and all later shifts.
    """
    last = float(settings.get("last_odo_reading", 0))
    if df.empty or "Shift_Date" not in df.columns:
        return last
    day = pd.Timestamp(shift_date).normalize()
    after = df[df["Shift_Date"].dt.normalize() > day]
    same_day = df[df["Shift_Date"].dt.normalize() == day]
    km_after = float(after["Total_KM"].sum()) if not after.empty else 0.0
    km_same = float(same_day["Total_KM"].sum()) if not same_day.empty else 0.0
    return max(0.0, last - km_after - km_same)


def resolve_shift_distance(
    end_odo: float,
    *,
    settings_last_odo: float,
    start_odo: float | None = None,
) -> float:
    """Km for this shift from explicit start odo or the latest saved reading."""
    if start_odo is not None:
        return max(0.0, end_odo - start_odo)
    if end_odo >= settings_last_odo:
        return end_odo - settings_last_odo
    return 0.0


def weekly_stats(df: pd.DataFrame | None = None, days: int = 7) -> dict[str, Any]:
    empty = {
        "today_gross": 0.0,
        "weekly_gross": 0.0,
        "weekly_net": 0.0,
        "prior_weekly_net": 0.0,
        "shift_count": 0,
        "daily_breakdown": pd.DataFrame(columns=["date", "gross", "net"]),
    }
    if df is None:
        df = load_shifts_df()
    if df.empty:
        return empty

    now = datetime.now()
    week_limit = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0)
    prior_limit = (now - timedelta(days=days * 2)).replace(hour=0, minute=0, second=0)
    today = pd.Timestamp.now().normalize()

    recent = df[df["Shift_Date"] >= pd.Timestamp(week_limit)].copy()
    prior = df[
        (df["Shift_Date"] >= pd.Timestamp(prior_limit)) & (df["Shift_Date"] < pd.Timestamp(week_limit))
    ]

    recent = recent.assign(day=recent["Shift_Date"].dt.normalize())
    daily = recent.groupby("day", as_index=False).agg(
        gross=("Gross", "sum"), net=("Net_Profit", "sum")
    ).rename(columns={"day": "date"})

    today_rows = recent[recent["Shift_Date"].dt.normalize() == today]

    return {
        "today_gross": float(today_rows["Gross"].sum()),
        "weekly_gross": float(recent["Gross"].sum()),
        "weekly_net": float(recent["Net_Profit"].sum()),
        "prior_weekly_net": float(prior["Net_Profit"].sum()) if not prior.empty else 0.0,
        "shift_count": int(len(recent)),
        "daily_breakdown": daily,
    }


def shift_hours(
    start_time: str,
    end_time: str,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    ends_next_day: bool | None = None,
) -> float:
    """Hours worked; uses calendar dates when provided for overnight/multi-day shifts."""
    base = start_date or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    _, _, hours, _, _, _, _ = resolve_shift_span(
        base, start_time, end_time, end_date=end_date, ends_next_day=ends_next_day
    )
    return hours


def compute_shift(
    settings: dict[str, Any],
    gross: float,
    dist_km: float,
    hours: float,
) -> dict[str, float]:
    consumption = float(settings["vehicle"]["fuel_consumption_l_100km"])
    fuel_price = float(settings.get("last_fuel_price", 1.9))
    tax_pct = float(settings["financials"]["tax_buffer_pct"])
    ato_rate = float(settings["financials"].get("ato_km_rate", 0.88))

    fuel_used = (dist_km / 100) * consumption
    fuel_cost = round(fuel_used * fuel_price, 2)
    tax = round(gross * tax_pct, 2)
    net = round(gross - fuel_cost - tax, 2)
    hourly_net = round(net / hours, 2) if hours > 0 else 0.0
    hourly_gross = round(gross / hours, 2) if hours > 0 else 0.0

    return {
        "fuel_used": round(fuel_used, 3),
        "fuel_cost": fuel_cost,
        "tax": tax,
        "net": net,
        "hourly_net": hourly_net,
        "hourly_gross": hourly_gross,
        "ato_deduction": round(dist_km * ato_rate, 2),
    }


def append_shift(
    settings: dict[str, Any],
    *,
    shift_date: datetime,
    start_time: str,
    end_time: str,
    gross: float,
    end_odo: float,
    energy_state: str,
    allow_odo_decrease: bool = False,
    start_odo: float | None = None,
    end_date: datetime | None = None,
    ends_next_day: bool | None = None,
) -> dict[str, Any]:
    last_odo = float(settings.get("last_odo_reading", 0))
    _, _, hours, start_time, end_time, shift_date_str, end_date_str = resolve_shift_span(
        shift_date, start_time, end_time, end_date=end_date, ends_next_day=ends_next_day
    )
    start_time, end_time = validate_shift_inputs(
        gross=gross,
        end_odo=end_odo,
        last_odo=last_odo,
        start_time=start_time,
        end_time=end_time,
        hours=hours,
        energy_state=energy_state,
        energy_states=ENERGY_STATES,
        allow_odo_decrease=allow_odo_decrease,
        start_odo=start_odo,
    )

    dist_km = resolve_shift_distance(end_odo, settings_last_odo=last_odo, start_odo=start_odo)
    df_before = load_shifts_df()
    backfill = is_backfill_shift(df_before, shift_date) or start_odo is not None
    calc = compute_shift(settings, gross, dist_km, hours)
    now = datetime.now()

    row = {
        "Log_Timestamp": now.strftime("%d/%m/%Y %H:%M:%S"),
        "Shift_Date": shift_date_str,
        "End_Date": end_date_str,
        "Start_Time": start_time,
        "End_Time": end_time,
        "Hours": hours,
        "Total_KM": dist_km,
        "Gross": gross,
        "Actual_Fuel_Cost": calc["fuel_cost"],
        "ATO_Deduction_Est": calc["ato_deduction"],
        "Tax_Savings_Buffer": calc["tax"],
        "Net_Profit": calc["net"],
        "Hourly_Net": calc["hourly_net"],
        "Energy_State": energy_state,
    }

    atomic_append_csv_row(UNIFIED_LOG_PATH, row, SHIFT_COLUMNS, BACKUPS_DIR)

    if end_odo > last_odo:
        settings["last_odo_reading"] = end_odo

    if not backfill:
        settings["current_fuel_litres"] = max(
            0.0, float(settings.get("current_fuel_litres", 0)) - calc["fuel_used"]
        )
    save_settings(settings)
    span = format_shift_span(shift_date_str, start_time, end_date_str, end_time)
    logger.info("Shift saved: %s (%.2fh) gross=$%.2f net=$%.2f", span, hours, gross, calc["net"])
    return {**row, **calc, "shift_span": span}


def apply_refill(settings: dict[str, Any], litres: float, price_per_litre: float) -> dict[str, float]:
    validate_refill(litres, price_per_litre)
    tank = float(settings["vehicle"]["tank_capacity"])
    current = float(settings.get("current_fuel_litres", 0))
    new_level = min(current + litres, tank)

    settings["current_fuel_litres"] = round(new_level, 3)
    settings["last_fuel_price"] = price_per_litre
    save_settings(settings)
    logger.info("Refuel: %.1fL @ $%.2f/L", litres, price_per_litre)

    return {
        "litres_added": litres,
        "price_per_litre": price_per_litre,
        "total_cost": round(litres * price_per_litre, 2),
        "new_level": new_level,
        "km_range": km_left_on_fuel(settings),
        "capped": current + litres > tank,
    }


def export_shifts_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
