"""Legacy entry point — use unified_logger instead."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if __name__ == "__main__":
    print("shift_logger is retired. Use: uv run src/logging/unified_logger.py")
    print("Or double-click Log_Shift.bat in the project root.")
    sys.exit(0)
