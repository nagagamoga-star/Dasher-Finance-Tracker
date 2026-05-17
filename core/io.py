"""Atomic file writes and backups."""
from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger("biodash")

BACKUP_MAX_KEEP = 20


def backup_file(source: Path, backup_dir: Path) -> Path | None:
    if not source.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = backup_dir / f"{source.stem}_{stamp}{source.suffix}"
    shutil.copy2(source, dest)
    logger.info("Backup created: %s", dest.name)
    _prune_old_backups(backup_dir, source.stem, source.suffix)
    return dest


def _prune_old_backups(backup_dir: Path, stem: str, suffix: str) -> None:
    matches = sorted(backup_dir.glob(f"{stem}_*{suffix}"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in matches[BACKUP_MAX_KEEP:]:
        old.unlink(missing_ok=True)


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp, path)
    logger.debug("Wrote settings: %s", path)


def atomic_write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8-sig")
    os.replace(tmp, path)
    logger.debug("Wrote CSV: %s (%d rows)", path.name, len(df))


def atomic_append_csv_row(path: Path, row: dict, columns: list[str], backup_dir: Path) -> None:
    backup_file(path, backup_dir)
    new_row = pd.DataFrame([row])
    if path.exists():
        existing = pd.read_csv(path, encoding="utf-8-sig")
        combined = pd.concat([existing, new_row], ignore_index=True)
    else:
        combined = new_row
    for col in columns:
        if col not in combined.columns:
            combined[col] = None
    atomic_write_csv(path, combined[columns])
