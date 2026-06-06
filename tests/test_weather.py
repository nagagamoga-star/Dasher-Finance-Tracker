"""Tests for weather helpers."""
from core.weather import delivery_weather_hint, location_from_settings, wmo_summary


def test_wmo_summary_clear():
    label, icon = wmo_summary(0)
    assert label == "Clear sky"
    assert icon == "☀️"


def test_wmo_summary_unknown_code():
    label, icon = wmo_summary(999)
    assert label == "Weather"


def test_location_from_settings_defaults():
    loc = location_from_settings({})
    assert loc["city"] == "Townsville"
    assert loc["timezone"] == "Australia/Brisbane"


def test_delivery_weather_hint_rain():
    hint = delivery_weather_hint({"weather_code": 65, "precipitation_mm": 0, "wind_kmh": 10})
    assert hint is not None
    assert "Wet" in hint


def test_delivery_weather_hint_calm():
    assert delivery_weather_hint({"weather_code": 0, "precipitation_mm": 0, "wind_kmh": 5}) is None
