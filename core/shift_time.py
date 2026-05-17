"""Shift start/end datetime resolution (including overnight and multi-day spans)."""
from __future__ import annotations

from datetime import datetime, timedelta

from core.validation import ValidationError, parse_time

MAX_SHIFT_HOURS = 36.0


def resolve_shift_span(
    start_date: datetime,
    start_time: str,
    end_time: str,
    *,
    end_date: datetime | None = None,
    ends_next_day: bool | None = None,
) -> tuple[datetime, datetime, float, str, str, str, str]:
    """
    Build full shift window and duration.

    Returns:
        start_dt, end_dt, hours, start_time (HH:MM), end_time (HH:MM),
        shift_date (dd/mm/yyyy), end_date (dd/mm/yyyy)
    """
    start_hm = parse_time(start_time)
    end_hm = parse_time(end_time)
    st = datetime.strptime(start_hm, "%H:%M").time()
    et = datetime.strptime(end_hm, "%H:%M").time()
    start_dt = datetime.combine(start_date.date(), st)

    if end_date is not None:
        end_dt = datetime.combine(end_date.date(), et)
    elif ends_next_day is True:
        end_dt = datetime.combine(start_date.date() + timedelta(days=1), et)
    elif ends_next_day is False:
        end_dt = datetime.combine(start_date.date(), et)
        if end_dt <= start_dt:
            raise ValidationError(
                "End time is before start on the same day. "
                "Enable 'ends on a later day' if the shift crossed midnight."
            )
    else:
        # Auto: end clock before start clock → next calendar day
        if et <= st:
            end_dt = datetime.combine(start_date.date() + timedelta(days=1), et)
        else:
            end_dt = datetime.combine(start_date.date(), et)

    if end_dt <= start_dt:
        raise ValidationError("End must be after start. Check dates and times.")

    hours = round((end_dt - start_dt).total_seconds() / 3600, 2)
    if hours <= 0:
        raise ValidationError("Shift duration must be greater than zero.")
    if hours > MAX_SHIFT_HOURS:
        raise ValidationError(
            f"Shift length is {hours}h (max {MAX_SHIFT_HOURS:.0f}h). "
            "Check start/end dates if the shift spans multiple days."
        )

    return (
        start_dt,
        end_dt,
        hours,
        start_hm,
        end_hm,
        start_dt.strftime("%d/%m/%Y"),
        end_dt.strftime("%d/%m/%Y"),
    )


def format_shift_span(start_date_str: str, start_time: str, end_date_str: str, end_time: str) -> str:
    if start_date_str == end_date_str:
        return f"{start_date_str} {start_time}–{end_time}"
    return f"{start_date_str} {start_time} → {end_date_str} {end_time}"


def ends_on_later_day_default(start_time: str, end_time: str) -> bool:
    """Heuristic: end clock earlier than start clock usually means after midnight."""
    st = datetime.strptime(parse_time(start_time), "%H:%M").time()
    et = datetime.strptime(parse_time(end_time), "%H:%M").time()
    return et <= st
