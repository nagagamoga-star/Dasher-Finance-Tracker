"""Tests for core business logic."""
import pandas as pd
import pytest

from datetime import datetime

from core.logic import (
    compute_shift,
    repair_csv_shield,
    shift_hours,
    weekly_stats,
)
from core.shift_time import resolve_shift_span
from core.validation import ValidationError, parse_time, validate_refill, validate_shift_inputs


def test_repair_csv_shield_splits_merged_row():
    fixed = repair_csv_shield("Stuck13/05/2026")
    assert "Stuck\n13/05/2026" in fixed


def test_compute_shift_math():
    settings = {
        "last_fuel_price": 2.0,
        "vehicle": {"fuel_consumption_l_100km": 7.2},
        "financials": {"tax_buffer_pct": 0.10, "ato_km_rate": 0.88},
    }
    result = compute_shift(settings, gross=100.0, dist_km=50.0, hours=4.0)
    assert result["fuel_cost"] == round((50 / 100) * 7.2 * 2.0, 2)
    assert result["tax"] == 10.0
    assert result["net"] == round(100 - result["fuel_cost"] - 10, 2)
    assert result["hourly_net"] == round(result["net"] / 4, 2)


def test_shift_hours_overnight():
    assert shift_hours("22:00", "02:00") == 4.0


def test_shift_overnight_with_dates():
    start = datetime(2026, 5, 15)
    end = datetime(2026, 5, 16)
    _, _, hours, _, _, start_str, end_str = resolve_shift_span(
        start, "22:00", "02:00", end_date=end, ends_next_day=True
    )
    assert hours == 4.0
    assert start_str == "15/05/2026"
    assert end_str == "16/05/2026"


def test_shift_same_day():
    start = datetime(2026, 5, 15)
    _, _, hours, _, _, _, end_str = resolve_shift_span(start, "09:00", "17:00", ends_next_day=False)
    assert hours == 8.0
    assert end_str == "15/05/2026"


def test_validate_shift_rejects_negative_gross():
    with pytest.raises(ValidationError):
        validate_shift_inputs(
            gross=-1,
            end_odo=100,
            last_odo=50,
            start_time="09:00",
            end_time="12:00",
            hours=3,
            energy_state="Flow",
            energy_states=["Flow"],
        )


def test_validate_shift_rejects_odo_backwards():
    with pytest.raises(ValidationError):
        validate_shift_inputs(
            gross=50,
            end_odo=40,
            last_odo=100,
            start_time="09:00",
            end_time="12:00",
            hours=3,
            energy_state="Flow",
            energy_states=["Flow"],
            allow_odo_decrease=False,
        )


def test_validate_refill():
    validate_refill(10.0, 1.9)
    with pytest.raises(ValidationError):
        validate_refill(0, 1.9)


def test_parse_time_from_string():
    assert parse_time("08:30") == "08:30"


def test_weekly_stats_aggregation():
    df = pd.DataFrame(
        {
            "Shift_Date": pd.to_datetime(["15/05/2026", "16/05/2026"], dayfirst=True),
            "Gross": [100.0, 50.0],
            "Net_Profit": [80.0, 40.0],
        }
    )
    stats = weekly_stats(df, days=30)
    assert stats["weekly_gross"] == 150.0
    assert stats["weekly_net"] == 120.0
    assert stats["shift_count"] == 2
