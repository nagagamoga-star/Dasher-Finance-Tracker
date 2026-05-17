# BioDash v3.3

Analytics for independent delivery drivers (Australia). Track **gross vs net** profit, fuel range, ATO km deductions, and energy-state performance.

## Stack

| Layer | Tech |
|-------|------|
| UI | Streamlit (`app.py`, `ui/`) |
| Data | Pandas (`core/logic.py`) |
| Storage | Local JSON + CSV (gitignored) |
| CLI | `src/logging/unified_logger.py` |

## Quick start

```bash
pip install -r requirements.txt

# First-time setup (private config)
copy config\settings.example.json config\settings.json

# Optional sample data
python scripts/seed_dummy_data.py
copy data\raw\dummy_dasher_log.csv data\raw\unified_dasher_log.csv

# Dashboard
streamlit run app.py

# Terminal logger
uv run src/logging/unified_logger.py
```

## Project layout

```
├── app.py                    # Streamlit entry
├── core/
│   ├── logic.py              # Pandas + profit math + Shield repair
│   ├── io.py                 # Atomic writes + backups
│   ├── validation.py         # Shared input checks
│   └── paths.py
├── ui/                       # Streamlit tabs & sidebar
├── config/settings.example.json
├── data/raw/                 # Your CSV (gitignored)
├── tests/
└── .streamlit/config.toml    # Theme
```

## Features (v3.3)

- **Cached** data loads in Streamlit
- **Atomic** saves for settings and CSV
- **Auto-backup** before each write (`data/backups/`)
- **Settings tab** in the web UI
- **Export** filtered shifts as CSV
- **Validation** on shifts, refuel, and settings
- **Weekly net delta** vs prior week
- **pytest** + GitHub Actions CI

## Development

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
ruff check core ui tests app.py
```

## Privacy & GitHub

`.gitignore` excludes `config/settings.json` and `data/raw/*.csv` (except `dummy_dasher_log.csv`).

**Streamlit Cloud:** main file = `app.py`. Upload `settings.example.json`; use Secrets or mount config locally.

## License

MIT — see [LICENSE](LICENSE).
