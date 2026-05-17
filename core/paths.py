"""Canonical project paths — all apps read/write here."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.json"
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "config" / "settings.example.json"
UNIFIED_LOG_PATH = PROJECT_ROOT / "data" / "raw" / "unified_dasher_log.csv"
DUMMY_LOG_PATH = PROJECT_ROOT / "data" / "raw" / "dummy_dasher_log.csv"
BACKUPS_DIR = PROJECT_ROOT / "data" / "backups"
LOGS_DIR = PROJECT_ROOT / "logs"
ARCHIVE_DIR = PROJECT_ROOT / "scripts" / "archive"
