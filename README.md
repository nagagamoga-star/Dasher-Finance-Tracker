# Dasher Finance Tracker (BioDash)

**Open-source Python app for gig delivery drivers in Australia** — track **gross vs net** pay, fuel and odometer, **ATO cents-per-km** estimates, and shift “flow state” trends. Works with DoorDash-style work; **your earnings stay on your PC** (local CSV + JSON).

[![CI](https://github.com/nagagamoga-star/Dasher-Finance-Tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/nagagamoga-star/Dasher-Finance-Tracker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b.svg)](https://streamlit.io)

**Keywords:** delivery driver finance tracker · dasher earnings · gig economy · net profit calculator · fuel log · odometer · tax buffer · Streamlit dashboard · pandas · Australia ATO km rate

---

## Why use this?

| Problem | BioDash helps |
|--------|----------------|
| App shows gross, not real take-home | Net profit after fuel + tax buffer |
| Fuel and odometer in notes | One log: km, litres, daily target |
| “Good” vs “bad” shifts unclear | Energy states (Flow / Neutral / Stuck / Drained) + charts |
| Tax / BAS prep | Export CSV; estimated ATO deduction per shift |

Privacy-first: `config/settings.json` and `data/raw/unified_dasher_log.csv` are **gitignored** — not uploaded to GitHub.

---

## Quick start

```bash
git clone https://github.com/nagagamoga-star/Dasher-Finance-Tracker.git
cd Dasher-Finance-Tracker

pip install -r requirements.txt

# One-time private config (copy example)
copy config\settings.example.json config\settings.json   # Windows
# cp config/settings.example.json config/settings.json    # Mac/Linux

# Optional: sample shifts
python scripts/seed_dummy_data.py
copy data\raw\dummy_dasher_log.csv data\raw\unified_dasher_log.csv

# Web dashboard
streamlit run app.py

# Terminal logger (Windows: Log_Shift.bat)
uv run src/logging/unified_logger.py
```

---

## Features

- **Streamlit dashboard** — KPIs, date filters, charts, log shift, refuel, settings
- **CLI logger** — daily earning target, fuel top-up nudges, overnight shifts
- **Pandas** — CSV load, row-repair for merged exports, weekly gross/net stats
- **Safe saves** — atomic writes + backup to `data/backups/`
- **Tests & CI** — pytest + GitHub Actions

---

## Who is this for?

Independent **food delivery** and **courier** drivers in **Australia** who want:

- Real **hourly net** (not app gross)
- **Fuel consumption** and tank range (km left)
- Simple **shift diary** with mood/energy tagging
- Local data only (no cloud account required)

---

## Stack

| Layer | Tech |
|-------|------|
| UI | [Streamlit](https://streamlit.io) (`app.py`, `ui/`) |
| Data | [Pandas](https://pandas.pydata.org) (`core/logic.py`) |
| Storage | Local JSON + CSV |
| CLI | `src/logging/unified_logger.py` |

---

## Project layout

```
├── app.py                      # Streamlit entry (deploy this on Streamlit Cloud)
├── core/                       # Business logic, validation, backups
├── ui/                         # Dashboard tabs
├── config/settings.example.json
├── data/raw/dummy_dasher_log.csv   # Public sample data only
├── Log_Shift.bat
└── tests/
```

---

## Deploy & share

**Repo link:** https://github.com/nagagamoga-star/Dasher-Finance-Tracker

**Streamlit Cloud:** connect repo → main file `app.py` → use sample data or document that users bring their own config.

**Do not publish:** real `settings.json`, personal CSV logs, or `data/backups/`.

---

## Development

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
ruff check core ui tests app.py
```

---

## License

MIT — see [LICENSE](LICENSE). Forks welcome; attribution appreciated.
