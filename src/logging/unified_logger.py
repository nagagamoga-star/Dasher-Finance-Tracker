"""CLI entry point — thin wrapper around core.logic."""
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.gamify import (  # noqa: E402
    daily_target_status,
    fuel_topup_nudge,
    menu_quest_tagline,
    progress_bar,
)
from core.logging_config import setup_logging  # noqa: E402
from core.logic import (  # noqa: E402
    apply_refill,
    append_shift,
    compute_shift,
    daily_target,
    fuel_level_pct,
    gross_for_date,
    km_left_on_fuel,
    load_settings,
    load_shifts_df,
    weekly_stats,
)
from core.shift_time import ends_on_later_day_default, format_shift_span, resolve_shift_span  # noqa: E402
from core.validation import ValidationError  # noqa: E402
from core.version import __version__  # noqa: E402

setup_logging()


def fuel_bar_text(settings):
    pct = fuel_level_pct(settings)
    return "⛽ [" + "█" * int(pct * 10) + "░" * (10 - int(pct * 10)) + "]", float(settings.get("current_fuel_litres", 0))


def _print_quest_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _prompt_required_float(label: str, *, allow_empty: bool = False, default: float | None = None) -> float:
    """Ask until the user enters a valid number (no silent skip)."""
    while True:
        hint = f" [{default:.0f}]" if default is not None else ""
        raw = input(f"{label}{hint}: ").strip()
        if not raw:
            if allow_empty and default is not None:
                return default
            print("   Please enter a value.")
            continue
        try:
            return float(raw)
        except ValueError:
            print("   Enter a valid number.")


def _prompt_shift_dates(start_date: datetime, start_t: str, end_t: str) -> tuple[datetime | None, bool | None]:
    likely_overnight = ends_on_later_day_default(start_t, end_t)
    if likely_overnight:
        print("   ℹ️  End time is after midnight — overnight shift.")
        prompt = "Shift ends on a later calendar day? [Y/n]: "
    else:
        prompt = "Shift ends on a later calendar day? [y/N]: "

    answer = input(prompt).strip().lower()
    if not answer:
        ends_later = likely_overnight
    else:
        ends_later = answer in ("y", "yes")

    if not ends_later:
        return None, False

    default_end = (start_date + timedelta(days=1)).strftime("%d/%m/%Y")
    end_date_str = input(f"End date (finish day) [{default_end}]: ").strip() or default_end
    return datetime.strptime(end_date_str, "%d/%m/%Y"), True


def log_shift():
    s = load_settings()
    df = load_shifts_df()
    target = daily_target(s)
    now = datetime.now()
    today_str = now.strftime("%d/%m/%Y")

    print("\n--- 📝 LOGGING NEW SHIFT ---")
    print("Tip: For shifts after midnight, use start date = day you began, then set end date.")

    date_str = input(f"Start date [{today_str}]: ") or today_str
    start_date = datetime.strptime(date_str, "%d/%m/%Y")
    start_t = input("Start Time (HH:MM): ") or "00:00"
    end_t = input("End Time (HH:MM): ") or "00:00"

    try:
        end_date, ends_next_day = _prompt_shift_dates(start_date, start_t, end_t)

        _, _, hours, start_t, end_t, shift_str, end_str = resolve_shift_span(
            start_date, start_t, end_t, end_date=end_date, ends_next_day=ends_next_day
        )
        span_label = format_shift_span(shift_str, start_t, end_str, end_t)
        print(f"   → Span: {span_label} ({hours}h)")

        last_odo = float(s.get("last_odo_reading", 0.0))
        print(f"\n📍 Odometer (last saved: {last_odo:.0f} km)")
        while True:
            end_odo = _prompt_required_float("End odometer (km)")
            dist = max(0.0, end_odo - last_odo) if end_odo >= last_odo else 0.0
            print(f"   → Distance this shift: {dist:.1f} km")
            if dist > 500 and input(f"   ⚠️ {dist:.0f} km is a long shift. Confirm? (y/n): ").lower() != "y":
                continue
            break

        allow_reset = False
        if end_odo < last_odo:
            allow_reset = input("   Odometer went backwards — save anyway? (y/n): ").lower() == "y"
            if not allow_reset:
                print("   Cancelled — update odometer and try again.")
                return

        gross = _prompt_required_float("Gross earnings ($)", allow_empty=True, default=0.0)
        if hours > 0:
            print(f"   → Gross rate: ${gross / hours:.2f}/hr")

        day_gross = gross_for_date(df, start_date)
        print()
        _print_quest_lines(daily_target_status(day_gross, target, added=gross))

        print("\nFlow state (energy): [1] Flow | [2] Neutral | [3] Stuck | [4] Drained")
        vibe_map = {"1": "Flow", "2": "Neutral", "3": "Stuck", "4": "Drained"}
        energy = vibe_map.get(input("Select flow state (1-4): "), "Neutral")

        preview = compute_shift(s, gross, dist, hours)
        litres_after = max(0.0, float(s.get("current_fuel_litres", 0)) - preview["fuel_used"])
        km_after = km_left_on_fuel({**s, "current_fuel_litres": litres_after})

        print("\n--- Shift summary ---")
        print(f"   {span_label}")
        print(f"   Distance: {dist:.1f} km  |  Fuel used: {preview['fuel_used']:.2f}L (${preview['fuel_cost']:.2f})")
        if hours > 0:
            print(f"   Rates:    ${preview['hourly_gross']:.2f}/hr gross  |  ${preview['hourly_net']:.2f}/hr net")
        print(f"   Net profit: ${preview['net']:.2f}")
        print(f"   Flow state: {energy}")

        nudge = fuel_topup_nudge(preview["fuel_used"], litres_after, km_after)
        if nudge:
            print(f"\n   {nudge}")

        if input("\nSave this shift? (y/n): ").lower() == "y":
            append_shift(
                s,
                shift_date=start_date,
                start_time=start_t,
                end_time=end_t,
                gross=gross,
                end_odo=end_odo,
                energy_state=energy,
                allow_odo_decrease=allow_reset,
                end_date=end_date,
                ends_next_day=ends_next_day,
            )
            print("\n✅ Shift saved!")
            _print_quest_lines(daily_target_status(day_gross, target, added=gross))
            if nudge:
                print(f"   {nudge}")
            time.sleep(2)
    except (ValidationError, ValueError) as e:
        print(f"❌ Error: {e}")
        time.sleep(2)


def weekly_check():
    df = load_shifts_df()
    stats = weekly_stats(df)
    breakdown = stats["daily_breakdown"]

    os.system("cls" if os.name == "nt" else "clear")
    print(f"{'='*55}\n📅 7-DAY PERFORMANCE SUMMARY\n{'='*55}")
    if breakdown.empty:
        print("No data found for the last 7 days.")
    else:
        print(f"{'DATE':<12} | {'GROSS':<12} | {'NET':<12}\n{'-'*40}")
        for _, row in breakdown.iterrows():
            d = pd.Timestamp(row["date"]).strftime("%d/%m/%Y")
            print(f"{d:<12} | ${row['gross']:>11.2f} | ${row['net']:>11.2f}")

    prior = stats.get("prior_weekly_net", 0)
    delta = stats["weekly_net"] - prior
    print(f"{'='*55}")
    print(f"TOTALS ({stats['shift_count']} shifts) | ${stats['weekly_gross']:>11.2f} | ${stats['weekly_net']:>11.2f}")
    if prior:
        print(f"vs prior week net: ${delta:+.2f}")
    print(f"{'='*55}")
    input("\nPress Enter to return...")


def launch_web_dashboard():
    """Start Streamlit app.py in a new terminal (CLI menu stays open)."""
    app_path = ROOT / "app.py"
    if not app_path.exists():
        print(f"\n❌ Could not find {app_path}")
        time.sleep(2)
        return

    print("\n🌐 Starting BioDash web dashboard...")
    print("   URL: http://localhost:8501")
    print("   (Opens in a new window — use Ctrl+C there to stop Streamlit)\n")

    cmd = ["uv", "run", "streamlit", "run", "app.py"]
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                cmd,
                cwd=str(ROOT),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            subprocess.Popen(cmd, cwd=str(ROOT), start_new_session=True)
        print("✅ Dashboard launched. You can keep using this menu for logging.")
    except FileNotFoundError:
        print("❌ Could not run 'uv'. Try: pip install streamlit && streamlit run app.py")
    except OSError as e:
        print(f"❌ Failed to start dashboard: {e}")
    time.sleep(2)


def refill_fuel():
    s = load_settings()
    tank = s["vehicle"]["tank_capacity"]
    current = float(s.get("current_fuel_litres", 0))
    default_price = s.get("last_fuel_price", 1.90)

    print(f"\n--- ⛽ REFUEL ---")
    print(f"Tank now: {current:.1f}L / {tank:.0f}L  (~{km_left_on_fuel(s):.0f} km range)")

    try:
        litres_in = float(input("Litres added: "))
        price_str = input(f"Price per litre [${default_price:.2f}]: ")
        price = float(price_str) if price_str.strip() else float(default_price)

        result = apply_refill(s, litres_in, price)
        if result["capped"]:
            print("⚠️ Fill capped at tank capacity.")
        print(f"\n✅ Refill: {litres_in:.1f}L @ ${price:.2f}/L = ${result['total_cost']:.2f}")
        print(f"   Tank: {result['new_level']:.1f}L  |  ~{result['km_range']:.0f} km range")
        time.sleep(2)
    except (ValidationError, ValueError) as e:
        print(f"❌ Error: {e}")
        time.sleep(2)


def main():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        settings = load_settings()
        df = load_shifts_df()
        stats = weekly_stats(df)
        target = daily_target(settings)

        today_gross = stats["today_gross"]
        p_earn = min((today_gross / target) * 100, 100) if target else 0
        quest_bar = progress_bar(p_earn)
        e_bar = "█" * int(p_earn // 5) + "░" * (20 - int(p_earn // 5))
        f_bar, fuel_l = fuel_bar_text(settings)
        km_range = km_left_on_fuel(settings)
        quest_line = menu_quest_tagline(today_gross, target)

        print(f"{'='*55}")
        print(f"🚀 BIODASH v{__version__} | {datetime.now().strftime('%A, %d %b')}")
        if quest_line:
            print(quest_line)
        print(f"📍 ODO: {settings.get('last_odo_reading', 0.0):.0f} km")
        print(f"{f_bar} {fuel_l:.1f}L left  |  ~{km_range:.0f} km on fuel")
        print(f"{'-'*55}")
        print(f"📈 WEEKLY GROSS: ${stats['weekly_gross']:.2f}")
        print(f"💰 WEEKLY NET:   ${stats['weekly_net']:.2f}")
        print(f"🎯 TODAY:  [{quest_bar}] {int(p_earn)}%  (${today_gross:.2f} / ${target:.0f})")
        if target > 0 and today_gross < target:
            print(f"   └─ ${target - today_gross:.2f} to go — log a shift to level up!")
        elif target > 0:
            print(f"   └─ 🏆 Daily target beaten by ${today_gross - target:.2f}!")
        print(f"{'='*55}")
        print("1. 📝 Log Shift   2. ⛽ Refill Fuel   3. 📅 Weekly Check")
        print("4. 🌐 Web Dashboard (app.py)   Q. Quit")

        choice = input("\nAction: ").lower()
        if choice == "1":
            log_shift()
        elif choice == "2":
            refill_fuel()
        elif choice == "3":
            weekly_check()
        elif choice in ("4", "w", "web"):
            launch_web_dashboard()
        elif choice == "q":
            break


if __name__ == "__main__":
    main()
