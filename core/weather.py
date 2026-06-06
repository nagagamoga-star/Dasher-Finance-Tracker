"""Weather via Open-Meteo (no API key)."""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger("biodash")

DEFAULT_TIMEZONE = "Australia/Brisbane"
DEFAULT_LAT = -19.2569
DEFAULT_LON = 146.8239
DEFAULT_CITY = "Townsville"

# WMO weather interpretation codes (Open-Meteo)
WMO_LABELS: dict[int, tuple[str, str]] = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Icy fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Heavy drizzle", "🌧️"),
    61: ("Light rain", "🌧️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "🌨️"),
    73: ("Snow", "🌨️"),
    75: ("Heavy snow", "🌨️"),
    80: ("Rain showers", "🌦️"),
    81: ("Showers", "🌦️"),
    82: ("Heavy showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm & hail", "⛈️"),
    99: ("Severe thunderstorm", "⛈️"),
}


def location_from_settings(settings: dict[str, Any]) -> dict[str, Any]:
    loc = settings.get("location") or {}
    return {
        "city": str(loc.get("city") or DEFAULT_CITY),
        "latitude": float(loc.get("latitude", DEFAULT_LAT)),
        "longitude": float(loc.get("longitude", DEFAULT_LON)),
        "timezone": str(loc.get("timezone") or DEFAULT_TIMEZONE),
    }


def wmo_summary(code: int | None) -> tuple[str, str]:
    if code is None:
        return "Unknown", "🌡️"
    return WMO_LABELS.get(int(code), ("Weather", "🌡️"))


def _fetch_json(url: str, timeout: float = 8.0) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BioDash/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        logger.warning("Weather request failed: %s", e)
        return None


def geocode_city(city: str, *, country: str = "AU") -> dict[str, Any] | None:
    name = city.strip()
    if not name:
        return None
    params = urllib.parse.urlencode(
        {"name": name, "count": 1, "language": "en", "format": "json", "country_code": country}
    )
    data = _fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{params}")
    if not data or not data.get("results"):
        return None
    hit = data["results"][0]
    return {
        "city": hit.get("name", name),
        "latitude": float(hit["latitude"]),
        "longitude": float(hit["longitude"]),
        "timezone": hit.get("timezone", DEFAULT_TIMEZONE),
    }


def fetch_current_weather(
    latitude: float,
    longitude: float,
    *,
    timezone: str = DEFAULT_TIMEZONE,
) -> dict[str, Any] | None:
    params = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
            "timezone": timezone,
        }
    )
    data = _fetch_json(f"https://api.open-meteo.com/v1/forecast?{params}")
    if not data or "current" not in data:
        return None
    cur = data["current"]
    label, icon = wmo_summary(cur.get("weather_code"))
    return {
        "temperature_c": cur.get("temperature_2m"),
        "humidity_pct": cur.get("relative_humidity_2m"),
        "wind_kmh": cur.get("wind_speed_10m"),
        "precipitation_mm": cur.get("precipitation"),
        "weather_code": cur.get("weather_code"),
        "label": label,
        "icon": icon,
        "timezone": timezone,
    }


def delivery_weather_hint(weather: dict[str, Any] | None) -> str | None:
    if not weather:
        return None
    code = weather.get("weather_code")
    precip = float(weather.get("precipitation_mm") or 0)
    wind = float(weather.get("wind_kmh") or 0)
    if code in (65, 82, 95, 96, 99) or precip >= 2:
        return "Wet conditions — allow extra time and watch for slippery roads."
    if wind >= 40:
        return "Strong wind — take care on open roads and with hot food bags."
    if code in (45, 48):
        return "Low visibility — use headlights and reduce speed."
    return None
