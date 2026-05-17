"""Generate dummy_dasher_log.csv for repo clones (no private data)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "dummy_dasher_log.csv"

ROWS = [
    {
        "Log_Timestamp": "01/05/2026 18:00:00",
        "Shift_Date": "01/05/2026",
        "End_Date": "01/05/2026",
        "Start_Time": "09:00",
        "End_Time": "13:00",
        "Hours": 4.0,
        "Total_KM": 45.0,
        "Gross": 85.0,
        "Actual_Fuel_Cost": 6.16,
        "ATO_Deduction_Est": 39.6,
        "Tax_Savings_Buffer": 8.5,
        "Net_Profit": 70.34,
        "Hourly_Net": 17.59,
        "Energy_State": "Flow",
    },
    {
        "Log_Timestamp": "02/05/2026 20:00:00",
        "Shift_Date": "02/05/2026",
        "End_Date": "03/05/2026",
        "Start_Time": "22:00",
        "End_Time": "02:30",
        "Hours": 4.5,
        "Total_KM": 52.0,
        "Gross": 102.5,
        "Actual_Fuel_Cost": 7.12,
        "ATO_Deduction_Est": 45.76,
        "Tax_Savings_Buffer": 10.25,
        "Net_Profit": 85.13,
        "Hourly_Net": 18.92,
        "Energy_State": "Neutral",
    },
    {
        "Log_Timestamp": "03/05/2026 14:00:00",
        "Shift_Date": "03/05/2026",
        "End_Date": "03/05/2026",
        "Start_Time": "06:00",
        "End_Time": "12:00",
        "Hours": 6.0,
        "Total_KM": 78.0,
        "Gross": 145.0,
        "Actual_Fuel_Cost": 10.68,
        "ATO_Deduction_Est": 68.64,
        "Tax_Savings_Buffer": 14.5,
        "Net_Profit": 119.82,
        "Hourly_Net": 19.97,
        "Energy_State": "Stuck",
    },
]

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(ROWS).to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"Wrote {OUT}")
