from core.gamify import daily_target_status, fuel_topup_nudge


def test_daily_target_remaining():
    lines = daily_target_status(80.0, 150.0, added=20.0)
    assert any("$50.00" in line for line in lines)


def test_daily_target_complete():
    lines = daily_target_status(160.0, 150.0)
    assert any("CRUSHED" in line for line in lines)


def test_fuel_nudge_over_threshold():
    msg = fuel_topup_nudge(6.0, 30.0, 400.0)
    assert msg is not None
    assert "6.0L" in msg


def test_fuel_nudge_under_threshold():
    assert fuel_topup_nudge(4.0, 40.0, 500.0) is None
