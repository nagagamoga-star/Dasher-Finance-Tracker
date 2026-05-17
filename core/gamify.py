"""Gamified CLI messages: daily targets, fuel nudges, menu flair."""

from __future__ import annotations

FUEL_NUDGE_LITRES = 5.0


def progress_bar(pct: float, width: int = 20) -> str:
    filled = int(min(max(pct, 0), 100) // (100 / width))
    return "█" * filled + "░" * (width - filled)


def daily_target_status(gross_so_far: float, target: float, added: float = 0.0) -> list[str]:
    """Lines to print for daily gross quest progress."""
    if target <= 0:
        return []

    total = gross_so_far + added
    remaining = max(0.0, target - total)
    pct = min(total / target * 100, 100)
    bar = progress_bar(pct)

    if remaining <= 0:
        over = total - target
        return [
            f"🎉 DAILY TARGET CRUSHED! +${over:.2f} above ${target:.0f}",
            f"   [{bar}] {pct:.0f}%",
        ]

    lines = [f"🎯 Daily quest: ${remaining:.2f} to go (${total:.2f} / ${target:.0f})", f"   [{bar}] {pct:.0f}%"]
    if added > 0:
        lines[0] = f"🎯 +${added:.2f} logged — ${remaining:.2f} left to hit ${target:.0f} today"
    lines.append(_motivation(pct))
    return lines


def _motivation(pct: float) -> str:
    if pct >= 100:
        return "   ★ Legendary shift — target destroyed!"
    if pct >= 75:
        return "   ★ So close — one more run could do it!"
    if pct >= 50:
        return "   ★ Halfway hero — keep the momentum!"
    if pct >= 25:
        return "   ★ Good start — stay in Flow!"
    return "   ★ Quest begun — every dollar counts!"


def fuel_topup_nudge(fuel_used: float, litres_left: float, km_left: float) -> str | None:
    if fuel_used <= FUEL_NUDGE_LITRES:
        return None
    return (
        f"⛽ Fuel alert: {fuel_used:.1f}L used this shift · "
        f"~{litres_left:.1f}L left (~{km_left:.0f} km) — consider topping up (option 2)"
    )


def menu_quest_tagline(gross_today: float, target: float) -> str:
    if target <= 0:
        return ""
    remaining = max(0.0, target - gross_today)
    if remaining <= 0:
        return "🏆 Today's quest: COMPLETE"
    return f"🏆 Quest: ${remaining:.2f} to daily target"
