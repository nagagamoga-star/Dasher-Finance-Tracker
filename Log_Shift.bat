@echo off
title BioDash Logger
cd /d "%~dp0"
uv run src/logging/unified_logger.py
if %errorlevel% neq 0 pause
